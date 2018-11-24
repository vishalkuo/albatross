import requests
import constants


def post(raw_text: str) -> None:
    requests.post(constants.SLACK_WEBHOOK, json={"text": raw_text})

