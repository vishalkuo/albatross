provider "aws" {
  region = "us-east-1"
}

resource "aws_lambda_function" "albatross" {
  function_name = "albatross"

  handler = "albatross.handle"
  runtime = "python3.6"

  role = "${aws_iam_role.albatross_role.arn}"

  environment {
    variables = {
      KEY_NAME = "${var.key_name}",
      SECURITY_GROUPS = "${var.security_groups}",
      SLACK_KEY = "${var.slack_key}",
      SNS_TOPIC = "${var.sns_topic}"
    }
  }
}

resource "aws_lambda_function" "albatross-internal" {
  function_name = "albatross-internal"

  handler = "albatross_internal.handle"
  runtime = "python3.6"

  role = "${aws_iam_role.albatross_role.arn}"

  environment {
    variables = {
      KEY_NAME = "${var.key_name}",
      SECURITY_GROUPS = "${var.security_groups}",
      SLACK_WEBHOOK = "${var.slack_webhook}"
    }
  }

  timeout = "10"
}

resource "aws_iam_role" "albatross_role" {
  name = "albatrossRole"
 
  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
EOF
}
