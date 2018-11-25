import hashlib
import hmac
import logging
import boto3
import json
import os
import urllib.parse as urlparse
from typing import Optional
import constants
import aws


logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def verify_slack_request(
    slack_signature=None, slack_request_timestamp=None, request_body=None
):
    basestring = f"v0:{slack_request_timestamp}:{request_body}".encode("utf-8")
    s = bytes(constants.SLACK_SIGNING_SECRET, "utf-8")
    sig = "v0=" + hmac.new(s, basestring, hashlib.sha256).hexdigest()

    if hmac.compare_digest(sig, slack_signature):
        return True
    else:
        return False


def handle(event, context):
    try:
        slack_signature = event["headers"]["X-Slack-Signature"]
        slack_request_timestamp = event["headers"]["X-Slack-Request-Timestamp"]

        if not verify_slack_request(
            slack_signature, slack_request_timestamp, event["body"]
        ):
            response = {"statusCode": 401, "body": "Unauthorized"}
            return response

        body = urlparse.parse_qs(event["body"])
        if not body["text"] or body["text"][0] not in constants.COMMANDS:
            text = f"Invalid command, please try `{constants.COMMANDS}``"
            return {"statusCode": 200, "body": json.dumps({"text": text})}

        cmd = body["text"][0]
        body = ""
        client = boto3.client("ec2")
        if cmd == constants.STATUS:
            body = _process_status(client)
        elif cmd == constants.DOWN:
            body = _process_down(client)

        response = {"text": body, "response_type": "in_channel"}

        return {"statusCode": 200, "body": json.dumps(response)}

    except Exception as e:
        response = {"statusCode": 400, "body": f"Error: {e}"}
        return response


def _process_down(client) -> str:
    server = aws.find_devserver(client)
    if not server:
        return "No devserver found"
    try:
        client.stop_instances(InstanceIds=[server["InstanceId"]])
    except Exception as e:
        return f"Error stopping instance: `{e}``"
    return "Stopping..."


def _process_status(client) -> str:
    server = aws.find_devserver(client, non_terminated=True)
    if not server:
        return "Not found, please start"
    return server["State"]["Name"]
