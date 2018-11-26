import constants
from typing import Optional
import time

# TODO(vishalkuo): refactor to remove custom filters
devserver_filter = {"Name": "tag:application", "Values": [constants.DEVSERVER]}
state_filter = {
    "Name": "instance-state-name",
    "Values": ["pending", "running", "stopping", "stopped"],
}
image_filter = {
    "Name": f"tag:{constants.ALBATROSS_STATUS}",
    "Values": [constants.MARKED_FOR_DELETION],
}


def create_image(client, instance_id: str):
    return client.create_image(
        InstanceId=instance_id, Name=f"albatross-{int(time.time())}"
    )


def get_images(client, include_deleted: bool = True):
    filters = [devserver_filter]
    if include_deleted:
        filters.append(image_filter)
    return client.describe_images(Filters=filters)


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
