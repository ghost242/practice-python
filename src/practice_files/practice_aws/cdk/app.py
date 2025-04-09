from aws_cdk.core import App
from lib.cdk_workshop_stack import CdkWorkshopStack

app = App()
stack = CdkWorkshopStack(app, "CdkWorkshopStack")

app.synth()
