import requests
import constants
import hmac
import hashlib


def post(raw_text: str) -> None:
    requests.post(constants.SLACK_WEBHOOK, json={"text": raw_text})


def verify(slack_signature=None, slack_request_timestamp=None, request_body=None):
    basestring = f"v0:{slack_request_timestamp}:{request_body}".encode("utf-8")
    s = bytes(constants.SLACK_SIGNING_SECRET, "utf-8")
    sig = "v0=" + hmac.new(s, basestring, hashlib.sha256).hexdigest()

    if hmac.compare_digest(sig, slack_signature):
        return True
    else:
        return False

