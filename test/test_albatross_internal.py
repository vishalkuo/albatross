import unittest
import albatross_internal
from unittest.mock import patch, MagicMock
from test import helper
import json


def get_test_sns(message: str):
    return {"Records": [{"Sns": {"Message": message}}]}


def get_test_cron():
    return {"detail-type": "Scheduled Event"}


def get_state_change(instance_id: str, state: str):
    return {
        "detail-type": "EC2 Instance State-change Notification",
        "detail": {"instance-id": instance_id, "state": state},
    }


@patch("albatross_internal.aws")
@patch("albatross_internal.constants")
@patch("albatross_internal.boto3")
@patch("albatross_internal.slack")
class TestAlbatross(unittest.TestCase):
    def test_processess_sns_for_irrelevant_action(self, slack, boto3, constants, aws):
        constants.DOWN = "down"
        resp = albatross_internal.handle(get_test_sns(constants.DOWN), None)
        self.assertEqual(200, resp["statusCode"])
        slack.post.assert_not_called()

    def test_processess_sns_for_up_with_running_server(
        self, slack, boto3, constants, aws
    ):
        constants.UP = "up"
        resource = MagicMock()
        boto3.resource.return_value = resource
        client = MagicMock()
        boto3.client.return_value = client
        aws.find_devserver.return_value = helper.get_mock_server(state="running")

        resp = albatross_internal.handle(get_test_sns(constants.UP), None)

        self.assertEqual(200, resp["statusCode"])
        slack.post.assert_called_with("Server already running, can't start another one")
        aws.spawn_devserver.assert_not_called()

    def test_processess_sns_for_up_with_stopped_server(
        self, slack, boto3, constants, aws
    ):
        constants.UP = "up"
        resource = MagicMock()
        boto3.resource.return_value = resource
        client = MagicMock()
        boto3.client.return_value = client
        aws.find_devserver.return_value = helper.get_mock_server(state="stopped")

        resp = albatross_internal.handle(get_test_sns(constants.UP), None)

        self.assertEqual(200, resp["statusCode"])
        slack.post.assert_called_with("Server is in the shutdown process, please wait")
        aws.spawn_devserver.assert_not_called()

    def test_processess_sns_with_no_image(self, slack, boto3, constants, aws):
        constants.UP = "up"
        resource = MagicMock()
        boto3.resource.return_value = resource
        client = MagicMock()
        boto3.client.return_value = client
        aws.find_devserver.return_value = None
        aws.get_images.return_value = {"Images": []}
        server = MagicMock()
        server.public_dns_name = "foobar.com"
        aws.spawn_devserver.return_value = [server]

        resp = albatross_internal.handle(get_test_sns(constants.UP), None)

        self.assertEqual(200, resp["statusCode"])
        aws.spawn_devserver.assert_called_with(resource, constants.DEFAULT_IMAGE)
        slack.post.assert_called_with(
            """devserver successfully started:
    ```
    mosh -I albatross ec2-user@foobar.com
    ```"""
        )

    def test_processess_sns_with_image(self, slack, boto3, constants, aws):
        constants.UP = "up"
        resource = MagicMock()
        boto3.resource.return_value = resource
        client = MagicMock()
        boto3.client.return_value = client
        aws.find_devserver.return_value = None
        aws.get_images.return_value = {"Images": [{"ImageId": "imageId"}]}
        server = MagicMock()
        server.public_dns_name = "foobar.com"
        aws.spawn_devserver.return_value = [server]

        resp = albatross_internal.handle(get_test_sns(constants.UP), None)

        self.assertEqual(200, resp["statusCode"])
        aws.spawn_devserver.assert_called_with(resource, "imageId")
        slack.post.assert_called_with(
            """devserver successfully started:
    ```
    mosh -I albatross ec2-user@foobar.com
    ```"""
        )

    def test_processess_cron_with_running_server(self, slack, boto3, constants, aws):
        client = MagicMock()
        boto3.client.return_value = client
        server = helper.get_mock_server(state="running")
        aws.find_devserver.return_value = server

        resp = albatross_internal.handle(get_test_cron(), None)

        self.assertEqual(200, resp["statusCode"])
        client.terminate_instances.assert_not_called()
        slack.post.assert_not_called()

    def test_processess_cron_with_unavailable_image(self, slack, boto3, constants, aws):
        client = MagicMock()
        boto3.client.return_value = client
        server = helper.get_mock_server(state="stopped")
        aws.find_devserver.return_value = server
        aws.get_images.return_value = {"Images": [{"State": "pending"}]}

        resp = albatross_internal.handle(get_test_cron(), None)

        self.assertEqual(200, resp["statusCode"])
        client.terminate_instances.assert_not_called()
        slack.post.assert_not_called()

    def test_processess_cron_with_available_image_no_deletion(
        self, slack, boto3, constants, aws
    ):
        client = MagicMock()
        boto3.client.return_value = client
        server = helper.get_mock_server(state="stopped")
        aws.find_devserver.return_value = server
        aws.get_images.return_value = {"Images": [{"State": "available"}]}
        client.describe_images.return_value = {"Images": []}

        resp = albatross_internal.handle(get_test_cron(), None)

        self.assertEqual(200, resp["statusCode"])
        client.terminate_instances.assert_called_with(
            InstanceIds=[server["InstanceId"]]
        )
        slack.post.assert_called_with("Image created and instance terminated")
        client.deregister_image.assert_not_called()
        client.delete_snapshot.assert_not_called()

    def test_processess_cron_with_available_image_with_deletion(
        self, slack, boto3, constants, aws
    ):
        client = MagicMock()
        boto3.client.return_value = client
        server = helper.get_mock_server(state="stopped")
        aws.find_devserver.return_value = server
        aws.get_images.return_value = {"Images": [{"State": "available"}]}
        client.describe_images.return_value = {
            "Images": [
                {
                    "ImageId": "foo",
                    "BlockDeviceMappings": [{"Ebs": {"SnapshotId": "bar"}}],
                }
            ]
        }

        resp = albatross_internal.handle(get_test_cron(), None)

        self.assertEqual(200, resp["statusCode"])
        client.terminate_instances.assert_called_with(
            InstanceIds=[server["InstanceId"]]
        )
        slack.post.assert_called_with("Image created and instance terminated")
        client.deregister_image.assert_called_with(ImageId="foo")
        client.delete_snapshot.assert_called_with(SnapshotId="bar")

    def test_processess_state_change_for_irrelevant_server(
        self, slack, boto3, constants, aws
    ):
        client = MagicMock()
        boto3.client.return_value = client
        server = helper.get_mock_server(state="stopped")
        aws.find_devserver.return_value = server

        resp = albatross_internal.handle(get_state_change("foo", "bar"), None)

        self.assertEqual(200, resp["statusCode"])
        slack.post.assert_not_called()
        aws.create_image.assert_not_called()
        client.create_tags.assert_not_called()

    def test_processess_state_change_for_irrelevant_state(
        self, slack, boto3, constants, aws
    ):
        client = MagicMock()
        boto3.client.return_value = client
        server = helper.get_mock_server(state="stopped")
        aws.find_devserver.return_value = server

        resp = albatross_internal.handle(
            get_state_change(server["InstanceId"], "running"), None
        )

        self.assertEqual(200, resp["statusCode"])
        slack.post.assert_not_called()
        aws.create_image.assert_not_called()
        client.create_tags.assert_not_called()

    def test_processess_state_change_for_relevant_state_and_server(
        self, slack, boto3, constants, aws
    ):
        client = MagicMock()
        boto3.client.return_value = client
        server = helper.get_mock_server(state="stopped")
        aws.find_devserver.return_value = server
        aws.get_images.return_value = {"Images": [{"ImageId": "foo"}]}
        aws.create_image.return_value = {"ImageId": "id2"}

        resp = albatross_internal.handle(
            get_state_change(server["InstanceId"], "stopped"), None
        )

        self.assertEqual(200, resp["statusCode"])
        slack.post.assert_called_with("Instance has stopped, image created")
        aws.create_image.assert_called_with(client, server["InstanceId"])
        client.create_tags.assert_called_with(
            Resources=["id2"],
            Tags=[{"Key": "application", "Value": constants.DEVSERVER}],
        )

