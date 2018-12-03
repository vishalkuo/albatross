resource "aws_cloudwatch_event_rule" "albatross_cron" {
    description = "albatross cron job"
    schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "albatross_cron_lambda" {
    rule = "${aws_cloudwatch_event_rule.albatross_cron.name}"
    arn = "${aws_lambda_function.albatross-internal.arn}"
}

resource "aws_cloudwatch_event_rule" "albatross_state_change" {
    description =  "Notifies when instances is stopped"
    event_pattern = <<EOF
    {
        "source": [
            "aws.ec2"
        ],
        "detail-type": [
            "EC2 Instance State-change Notification"
        ],
        "detail": {
            "state": [
                "stopped"
            ]
        }
    }
EOF
}

resource "aws_cloudwatch_event_target" "albatross_state_change_lambda" {
    rule = "${aws_cloudwatch_event_rule.albatross_state_change.name}"
    arn = "${aws_lambda_function.albatross-internal.arn}"
}

