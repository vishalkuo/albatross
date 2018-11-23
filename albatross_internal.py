import json
import logging
from typing import Optional
import boto3
import os
import requests

logger = logging.getLogger()
logger.setLevel(logging.WARNING)

DEVSERVER = "devserver"
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")


def handle(event, context):
    client = boto3.client("ec2")
    server = _find_devserver(client)

    logger.warn(f"Received event {event}")
    if not server:
        return {"statusCode": 400, "body": "Server not found"}

    if server["InstanceId"] != event["detail"]["instance-id"]:
        return {"statusCode": 400, "body": "Irrelevant instance id"}

    slack_str = ""
    state = event["detail"]["state"]
    if state == "stopped":
        slack_str = "Instance has stopped, terminating..."
        client.terminate_instances(InstanceIds=[server["InstanceId"]])
    else:
        slack_str = "Instance terminated"

    requests.post(SLACK_WEBHOOK, json={"text": slack_str})
    return {"statusCode": 200, "body": json.dumps(state)}


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
