"""AWS glue availability application logic for generating diagrams for subnet assocation"""

from diagrams import Cluster, Diagram
from diagrams.aws.analytics import Glue as GlueDiagram

from awsglueavailability.client import EC2, Glue, jobs_by_subnet


def draw_diagram(glue_client: Glue, ec2_client: EC2) -> None:
    """Generate VPC diagram showing Glue assocation to subnets

    Keyword arguments:
    glue_client -- awsglueavailability Glue client
    ec2_client -- awsglueavailability EC2 client
    """

    glue_data = jobs_by_subnet(glue_client.get_jobs())
    vpc_data = {}

    for subnet in glue_data:
        vpc = ec2_client.get_subnet(subnet).vpc
        vpc_data[vpc] = vpc_data[vpc] + [subnet] if vpc in vpc_data else [subnet]

    for vpc, subnets in vpc_data.items():
        with Diagram(vpc, show=False, filename=f"output/{vpc}"):

            for subnet in subnets:
                with Cluster(subnet):
                    for job in glue_data[subnet]:
                        GlueDiagram(job.name)
