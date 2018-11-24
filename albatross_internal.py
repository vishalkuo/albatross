import json
import logging
from typing import Optional
import boto3
import os
import requests
import constants
import aws
import slack

logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def handle(event, context):
    client = boto3.client("ec2")
    logger.warn(f"Received event {event}")

    server = aws.find_devserver(client)
    if not server:
        return {"statusCode": 400, "body": "Server not found"}
    if event["detail-type"] == "EC2 Instance State-change Notification":
        return _process_instance_state_change(client, event, server)
    if event["detail-type"] == "Scheduled Event":
        return _process_cron(client, event, server)

    return {"statusCode": 200, "body": "noop"}


def _process_cron(client, event, server):
    images = aws.get_images(client)
    if not images["Images"]:
        return {"statusCode": 200, "body": "noop"}

    image = images["Images"][0]
    if image["State"] == "available":
        slack_str = "Image created and instance terminated"
        try:
            client.terminate_instances(InstanceIds=[server["InstanceId"]])
        except Exception as e:
            slack_str = f"Couldn't terminate instance: {e}"
        slack.post(slack_str)
        return {"statusCode": 200, "body": "Terminated instance"}

    return {"statusCode": 200, "body": "noop"}


def _process_instance_state_change(client, event, server):
    if server["InstanceId"] != event["detail"]["instance-id"]:
        return {"statusCode": 400, "body": "Irrelevant instance id"}

    if event["detail"]["state"] != "stopped":
        return {"statusCode": 400, "body": "Irrelevant state"}

    instance_id = server["InstanceId"]
    slack_str = "Instance has stopped, image created"
    try:
        res = aws.create_image(client, instance_id)
        client.create_tags(
            Resources=[res["ImageId"]],
            Tags=[{"Key": "application", "Value": constants.DEVSERVER}],
        )
    except Exception as e:
        slack_str = f"Couldn't create image on shut down: `{e}`"

    slack.post(slack_str)
    return {"statusCode": 200, "body": json.dumps("Creating snapshot")}

