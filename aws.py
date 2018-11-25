import constants
from typing import Optional


devserver_filter = {"Name": "tag:application", "Values": [constants.DEVSERVER]}
state_filter = {
    "Name": "instance-state-name",
    "Values": ["pending", "running", "shutting-down", "stopping", "stopped"],
}


def create_image(client, instance_id: str):
    return client.create_image(InstanceId=instance_id, Name="albatross")


def get_images(client):
    return client.describe_images(Filters=[devserver_filter])


def find_devserver(client, non_terminated=False) -> Optional[any]:
    reservations = get_ec2_instances(client, non_terminated=non_terminated)[
        "Reservations"
    ]
    if (
        not reservations
        or not reservations[0]["Instances"]
        or not reservations[0]["Instances"][0]
    ):
        return None

    return reservations[0]["Instances"][0]


def get_ec2_instances(client, non_terminated=False):
    filters = [devserver_filter]
    if non_terminated:
        filters.append(state_filter)
    return client.describe_instances(Filters=filters)


def spawn_devserver(resource, image_id):
    return resource.create_instances(
        MaxCount=1,
        MinCount=1,
        ImageId=image_id,
        SecurityGroups=constants.SECURITY_GROUPS,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "application", "Value": constants.DEVSERVER}],
            }
        ],
        InstanceType=constants.INSTANCE_TYPE,
        KeyName=constants.KEY_NAME,
    )
