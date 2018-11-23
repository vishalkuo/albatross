import hashlib
import hmac
import logging
import boto3
import json
import os
import urllib.parse as urlparse
from typing import Optional


logger = logging.getLogger()
logger.setLevel(logging.WARNING)


UP, DOWN, STATUS = "up", "down", "status"
COMMANDS = set([UP, DOWN, STATUS])
DEVSERVER = "devserver"

slack_signing_secret = os.environ.get("SLACK_KEY")


def verify_slack_request(
    slack_signature=None, slack_request_timestamp=None, request_body=None
):
    basestring = f"v0:{slack_request_timestamp}:{request_body}".encode("utf-8")
    s = bytes(slack_signing_secret, "utf-8")
    sig = "v0=" + hmac.new(s, basestring, hashlib.sha256).hexdigest()

    if hmac.compare_digest(sig, slack_signature):
        return True
    else:
        return False


def post(event, context):
    try:
        slack_signature = event["headers"]["X-Slack-Signature"]
        slack_request_timestamp = event["headers"]["X-Slack-Request-Timestamp"]

        if not verify_slack_request(
            slack_signature, slack_request_timestamp, event["body"]
        ):
            response = {"statusCode": 401, "body": "Unauthorized"}
            return response

        body = urlparse.parse_qs(event["body"])
        if not body["text"] or body["text"][0] not in COMMANDS:
            text = f"Invalid command, please try {COMMANDS}"
            return {"statusCode": 200, "body": json.dumps({"text": text})}

        cmd = body["text"][0]
        body = ""
        client = boto3.client("ec2")
        if cmd == STATUS:
            body = _process_status(client)
        elif cmd == DOWN:
            body = _process_down(client)

        response = {"text": body, "response_type": "in_channel"}

        return {"statusCode": 200, "body": json.dumps(response)}

    except Exception as e:
        response = {"statusCode": 400, "body": f"Error: {e}"}
        return response


def _process_down(client) -> str:
    server = _find_devserver(client)
    if not server:
        return "No devserver found"
    try:
        client.stop_instances(InstanceIds=[server["InstanceId"]])
    except Exception as e:
        return f"Error stopping instance: `{e}``"
    return "Stopping..."


def _process_status(client) -> str:
    server = _find_devserver(client)
    if not server:
        return "Not found, please start"
    return server["State"]["Name"]


def _find_devserver(client) -> Optional[any]:
    reservations = _get_ec2_instances(client)["Reservations"]
    if (
        not reservations
        or not reservations[0]["Instances"]
        or not reservations[0]["Instances"][0]
    ):
        return None

    return reservations[0]["Instances"][0]


def _get_ec2_instances(client):
    return client.describe_instances(
        Filters=[{"Name": "tag:application", "Values": [DEVSERVER]}]
    )
