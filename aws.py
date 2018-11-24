import constants
from typing import Optional


devserver_filter = {"Name": "tag:application", "Values": [constants.DEVSERVER]}


def create_image(client, instance_id: str):
    return client.create_image(InstanceId=instance_id, Name="albatross")


def get_images(client):
    return client.describe_images(Filters=[devserver_filter])


def find_devserver(client) -> Optional[any]:
    reservations = get_ec2_instances(client)["Reservations"]
    if (
        not reservations
        or not reservations[0]["Instances"]
        or not reservations[0]["Instances"][0]
    ):
        return None

    return reservations[0]["Instances"][0]


def get_ec2_instances(client):
    return client.describe_instances(Filters=[devserver_filter])
