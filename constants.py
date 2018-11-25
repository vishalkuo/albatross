import os

UP, DOWN, STATUS = "up", "down", "status"
COMMANDS = set([UP, DOWN, STATUS])
DEVSERVER = "devserver"
SLACK_SIGNING_SECRET = os.environ.get("SLACK_KEY")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")

# CONFIGURABLE
INSTANCE_TYPE = "t2.micro"
SECURITY_GROUPS = os.environ.get("SECURITY_GROUPS").split(",")
KEY_NAME = os.environ.get("KEY_NAME")
