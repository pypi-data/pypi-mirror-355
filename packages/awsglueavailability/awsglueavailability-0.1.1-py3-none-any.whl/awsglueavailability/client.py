"""Clients for interacting with AWS"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Generator, Literal

import boto3

AvailabilityZone = Literal["eu-west-1a", "eu-west-1b", "eu-west-1c"]


@dataclass
class Conn:
    """Glue Connector definition"""

    name: str
    subnet: str
    az: AvailabilityZone


@dataclass
class Job:
    """Glue Job definition"""

    name: str
    conns: list[Conn]


@dataclass
class Subnet:
    """AWS Subnet definition"""

    vpc: str
    cidr_block: str


def jobs_by_subnet(jobs: list[Job]) -> dict[str, str]:
    """Restructure data to jobs by subnet

    Keyword arguments:
    jobs -- list of Jobs with Connection details
    """

    return {
        job_conn.subnet: [
            job
            for job in jobs
            if job_conn.subnet in [conn.subnet for conn in job.conns]
        ]
        for job in jobs
        for job_conn in job.conns
    }


class EC2:  # pylint: disable=too-few-public-methods
    """AWS EC2 Client

    Keyword arguments:
    client -- boto3 compatable ec2 client
    """

    def __init__(self, client=None):
        self.client = client if client else boto3.client("ec2")

    @lru_cache(maxsize=32)
    def get_subnet(self, subnet_id) -> Subnet:
        """retrieve vpc subnet information

        Keyword arguments:
        subnet_id -- id of subnet to retrieve attributes for
        """
        subnets = self.client.describe_subnets(SubnetIds=[subnet_id])["Subnets"]

        if not subnets:
            raise ValueError("Subnet not found")

        return Subnet(vpc=subnets[0]["VpcId"], cidr_block=subnets[0]["CidrBlock"])


class Glue:
    """AWS Glue Client

    Keyword arguments:
    client -- boto3 compatable Glue client
    """

    def __init__(self, client=None, max_results=200):
        self.client = client if client else boto3.client("glue")
        self.max_results = max_results

    def list_jobs(self) -> Generator[str]:
        """list all jobs deployed into the connected authenticated AWS account"""

        resp = self.client.list_jobs(MaxResults=self.max_results)

        while True:
            yield from resp["JobNames"]

            if not "NextToken" in resp:
                break

            resp = self.client.list_jobs(
                NextToken=resp["NextToken"] if resp else "", MaxResults=self.max_results
            )

    def get_job_connections(self, job_name) -> list[Conn]:
        """get the Glue Jobs associated to the specified job

        Keyword arguments:
        job_name -- Glue job name
        """

        job = self.client.get_job(JobName=job_name)["Job"]

        conns = (
            job["Connections"]["Connections"]
            if "Connections" in job and "Connections" in job["Connections"]
            else []
        )
        return [self._get_connection(conn) for conn in conns]

    @lru_cache(maxsize=32)
    def _get_connection(self, connection_name):
        conn = self.client.get_connection(Name=connection_name)["Connection"]

        return Conn(
            name=connection_name,
            subnet=(
                conn["PhysicalConnectionRequirements"]["SubnetId"]
                if "PhysicalConnectionRequirements" in conn
                and "SubnetId" in conn["PhysicalConnectionRequirements"]
                else None
            ),
            az=(
                conn["PhysicalConnectionRequirements"]["AvailabilityZone"]
                if "PhysicalConnectionRequirements" in conn
                and "AvailabilityZone" in conn["PhysicalConnectionRequirements"]
                else None
            ),
        )

    def get_jobs(self) -> list[Job]:
        """List all jobs within the authenticated AWS Account"""
        return [
            Job(name=job_name, conns=self.get_job_connections(job_name))
            for job_name in self.list_jobs()
        ]
