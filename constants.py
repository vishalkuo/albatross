import os

UP, DOWN, STATUS = "up", "down", "status"
COMMANDS = set([UP, DOWN, STATUS])
DEVSERVER = "devserver"
SLACK_SIGNING_SECRET = os.environ.get("SLACK_KEY")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
ALBATROSS_STATUS = "albatross_status"
MARKED_FOR_DELETION = "marked_for_deletion"

# CONFIGURABLE
INSTANCE_TYPE = os.environ.get("INSTANCE_TYPE", default="t2.micro")
SECURITY_GROUPS = os.environ.get("SECURITY_GROUPS", default="").split(",")
KEY_NAME = os.environ.get("KEY_NAME", default="")
DEFAULT_IMAGE = os.environ.get("DEFAULT_IMAGE", default="ami-09479453c5cde9639")
SNS_TOPIC = os.environ.get("SNS_TOPIC", default="")
