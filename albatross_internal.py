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
    # From SNS
    if "Records" in event:
        _handle_records(client, event["Records"])
        return {"statusCode": 200, "body": "started"}

    server = aws.find_devserver(client, non_terminated=True)
    if not server:
        return {"statusCode": 200, "body": "Server not found"}
    if event["detail-type"] == "EC2 Instance State-change Notification":
        return _process_instance_state_change(client, event, server)
    if event["detail-type"] == "Scheduled Event":
        return _process_cron(client, event, server)

    return {"statusCode": 200, "body": "noop"}


def _process_cron(client, event, server):
    images = aws.get_images(client, include_deleted=False)
    if not images["Images"] or server["State"]["Name"] == "terminated":
        return {"statusCode": 200, "body": "noop"}

    image = images["Images"][0]
    if image["State"] == "available":
        slack_str = "Image created and instance terminated"
        try:
            _delete_old_image(client)
            client.terminate_instances(InstanceIds=[server["InstanceId"]])
        except Exception as e:
            slack_str = f"Couldn't terminate instance: {e}"
        slack.post(slack_str)
        return {"statusCode": 200, "body": "Terminated instance"}

    return {"statusCode": 200, "body": "noop"}


def _process_instance_state_change(client, event, server):
    if server["InstanceId"] != event["detail"]["instance-id"]:
        return {"statusCode": 200, "body": "Irrelevant instance id"}

    if event["detail"]["state"] != "stopped":
        return {"statusCode": 200, "body": "Irrelevant state"}

    instance_id = server["InstanceId"]
    slack_str = "Instance has stopped, image created"
    try:
        # Tag old image if exists, we'll delete it when the new one is ready
        images = aws.get_images(client, include_deleted=False)
        for image in images["Images"]:
            client.create_tags(
                Resources=[image["ImageId"]],
                Tags=[
                    {
                        "Key": constants.ALBATROSS_STATUS,
                        "Value": constants.MARKED_FOR_DELETION,
                    }
                ],
            )
        res = aws.create_image(client, instance_id)
        client.create_tags(
            Resources=[res["ImageId"]],
            Tags=[{"Key": "application", "Value": constants.DEVSERVER}],
        )
    except Exception as e:
        slack_str = f"Couldn't create image on shut down: `{e}`"

    slack.post(slack_str)
    return {"statusCode": 200, "body": json.dumps("Creating snapshot")}


# Deletes image and ALL snapshots associated with it
def _delete_old_image(client):
    images = client.describe_images(Filters=[aws.image_filter])
    for image in images["Images"]:
        client.deregister_image(ImageId=image["ImageId"])
        for device in image["BlockDeviceMappings"]:
            client.delete_snapshot(SnapshotId=device["Ebs"]["SnapshotId"])


def _handle_records(client, records):
    for record in records:
        if record["Sns"]["Message"] == constants.UP:
            slack_str = ""
            try:
                resource = boto3.resource("ec2")
                slack_str = _process_up(client, resource)
            except Exception as e:
                slack_str = f"Couldn't start up server: {e}"
            slack.post(slack_str)


def _process_up(client, resource) -> str:
    server = aws.find_devserver(client, non_terminated=True)
    if server:
        if server["State"]["Name"] == "stopped":
            return "Server is in the shutdown process, please wait"
        return "Server already running, can't start another one"
    ami_id = constants.DEFAULT_IMAGE
    images = aws.get_images(client, include_deleted=False)
    if images["Images"]:
        ami_id = images["Images"][0]["ImageId"]
    aws.spawn_devserver(resource, ami_id)

    return "devserver successfully started"

