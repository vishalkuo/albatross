import hashlib
import hmac
import logging

import json
import os


logger = logging.getLogger()
logger.setLevel(logging.WARNING)


slack_signing_secret = os.environ["SLACK_KEY"]


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

        return {"statusCode": 200, "body": json.dumps({"text": "foo"})}

    except Exception as e:
        response = {"statusCode": 400, "body": "Error: {e}"}
        return response
