"""run aws-glue-availability tool to produce diagrams"""

from awsglueavailability.app import draw_diagram
from awsglueavailability.client import EC2, Glue

glue_client = Glue()
ec2_client = EC2()

draw_diagram(glue_client, ec2_client)
