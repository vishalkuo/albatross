import logging
import boto3
import json
import os
import urllib.parse as urlparse
from typing import Optional
import constants
import aws
import slack


logger = logging.getLogger()
logger.setLevel(logging.WARNING)

# TODO(vishalkuo): handle try except better
# TODO(vishalkuo): create a generic context with client/resource.
def handle(event, context):
    try:
        slack_signature = event["headers"]["X-Slack-Signature"]
        slack_request_timestamp = event["headers"]["X-Slack-Request-Timestamp"]

        if not slack.verify(slack_signature, slack_request_timestamp, event["body"]):
            response = {"statusCode": 401, "body": "Unauthorized"}
            return response

        body = urlparse.parse_qs(event["body"])
        if not body["text"] or body["text"][0] not in constants.COMMANDS:
            text = f"Invalid command, please try `{constants.COMMANDS}`"
            return {"statusCode": 200, "body": json.dumps({"text": text})}

        cmd = body["text"][0]
        body = ""
        client = boto3.client("ec2")
        sns = boto3.client("sns")
        if cmd == constants.STATUS:
            body = _process_status(client)
        elif cmd == constants.DOWN:
            body = _process_down(client)
        elif cmd == constants.UP:
            body = _process_up(sns)

        response = {"text": body, "response_type": "in_channel"}

        return {"statusCode": 200, "body": json.dumps(response)}

    except Exception as e:
        response = {"statusCode": 500, "body": f"Error: {e}"}
        return response


def _process_down(client) -> str:
    server = aws.find_devserver(client, non_terminated=True)
    if not server:
        return "No devserver found"

    if server["State"]["Name"] != "running":
        return "Server not running"

    client.stop_instances(InstanceIds=[server["InstanceId"]])
    return "Stopping..."


def _process_status(client) -> str:
    server = aws.find_devserver(client, non_terminated=True)
    if not server:
        return "Not found, please start"
    return server["State"]["Name"]


def _process_up(sns) -> str:
    sns.publish(TopicArn=constants.SNS_TOPIC, Message=constants.UP)
    return "Start request received!"
