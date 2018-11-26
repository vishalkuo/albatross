import unittest
import albatross
from unittest.mock import patch, MagicMock
from test import helper
import json


def get_test_event(body_str: str = ""):
    return {
        "headers": {"X-Slack-Signature": "foo", "X-Slack-Request-Timestamp": "bar"},
        "body": f"text={body_str}",
    }


@patch("albatross.aws")
@patch("albatross.constants")
@patch("albatross.boto3")
@patch("albatross.slack")
class TestAlbatross(unittest.TestCase):
    def test_no_slack_auth(self, slack, boto3, constants, aws):
        slack.verify.return_value = False
        resp = albatross.handle(get_test_event(), None)
        self.assertEqual(401, resp["statusCode"])
        slack.verify.assert_called_with("foo", "bar", "text=")
        boto3.client.assert_not_called()

    def test_with_invalid_command(self, slack, boto3, constants, aws):
        constants.COMMANDS = set(["up", "down", "status"])
        event = get_test_event("foo")
        slack.verify.return_value = True
        resp = albatross.handle(event, None)
        self.assertEqual(200, resp["statusCode"])
        boto3.client.assert_not_called()

    def test_status(self, slack, boto3, constants, aws):
        constants.COMMANDS = set(["up", "down", "status"])
        constants.STATUS = "status"
        event = get_test_event("status")
        slack.verify.return_value = True
        aws.find_devserver.return_value = helper.get_mock_server()

        resp = albatross.handle(event, None)

        expected = json.dumps({"text": "running", "response_type": "in_channel"})
        self.assertEqual(200, resp["statusCode"])
        self.assertEqual(expected, resp["body"])
        boto3.client.assert_any_call("ec2")
        boto3.client.assert_any_call("sns")

    def test_up(self, slack, boto3, constants, aws):
        constants.COMMANDS = set(["up", "down", "status"])
        constants.UP = "up"
        event = get_test_event("up")
        slack.verify.return_value = True
        sns = MagicMock()
        boto3.client.side_effect = [None, sns]

        resp = albatross.handle(event, None)

        expected = json.dumps(
            {"text": "Start request received!", "response_type": "in_channel"}
        )
        self.assertEqual(200, resp["statusCode"])
        self.assertEqual(expected, resp["body"])
        sns.publish.assert_called_with(
            TopicArn=constants.SNS_TOPIC, Message=constants.UP
        )
        boto3.client.assert_any_call("ec2")
        boto3.client.assert_any_call("sns")

    def test_down_with_running_instance(self, slack, boto3, constants, aws):
        constants.COMMANDS = set(["up", "down", "status"])
        constants.DOWN = "down"
        event = get_test_event("down")
        slack.verify.return_value = True
        ec2 = MagicMock()
        boto3.client.side_effect = [ec2, None]
        server = helper.get_mock_server()
        aws.find_devserver.return_value = server

        resp = albatross.handle(event, None)

        expected = json.dumps({"text": "Stopping...", "response_type": "in_channel"})
        self.assertEqual(200, resp["statusCode"])
        self.assertEqual(expected, resp["body"])
        ec2.stop_instances.assert_called_with(InstanceIds=[server["InstanceId"]])
        boto3.client.assert_any_call("ec2")
        boto3.client.assert_any_call("sns")

    def test_down_with_stopped_instance(self, slack, boto3, constants, aws):
        constants.COMMANDS = set(["up", "down", "status"])
        constants.DOWN = "down"
        event = get_test_event("down")
        slack.verify.return_value = True
        ec2 = MagicMock()
        boto3.client.side_effect = [ec2, None]
        server = helper.get_mock_server(state="stoped")
        aws.find_devserver.return_value = server

        resp = albatross.handle(event, None)

        expected = json.dumps(
            {"text": "Server not running", "response_type": "in_channel"}
        )
        self.assertEqual(200, resp["statusCode"])
        self.assertEqual(expected, resp["body"])
        ec2.stop_instances.assert_not_called()
        boto3.client.assert_any_call("ec2")
        boto3.client.assert_any_call("sns")

