resource "aws_sns_topic" "albatrossTopic" {
    display_name = "albatross"
}

resource "aws_sns_topic_subscription" "albatrossSubscription" {
   endpoint = "${aws_lambda_function.albatross-internal.arn}" 
   protocol = "lambda"
   topic_arn = "${aws_sns_topic.albatrossTopic.arn}"
}
