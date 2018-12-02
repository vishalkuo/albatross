import unittest
import albatross_internal
from unittest.mock import patch, MagicMock
from test import helper
import json


def get_test_sns(message: str):
    return {"Records": [{"Sns": {"Message": message}}]}


def get_test_cron():
    pass


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

    def test_processess_sns_no_image(self, slack, boto3, constants, aws):
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

