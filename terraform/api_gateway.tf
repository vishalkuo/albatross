resource "aws_api_gateway_rest_api" "albatross_gateway" {
  name = "albatross-API"
  description = "receive slack commands from slack"
}

resource "aws_api_gateway_resource" "albatross_resource" {
   rest_api_id = "${aws_api_gateway_rest_api.albatross_gateway.id}"
   parent_id = "${aws_api_gateway_rest_api.albatross_gateway.root_resource_id}"
   path_part = "albatross"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = "${aws_api_gateway_rest_api.albatross_gateway.id}"
  resource_id   = "${aws_api_gateway_resource.albatross_resource.id}"
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy_root" {
    rest_api_id = "${aws_api_gateway_rest_api.albatross_gateway.id}"
    resource_id = "${aws_api_gateway_method.proxy.resource_id}"
    http_method = "${aws_api_gateway_method.proxy.http_method}"


    integration_http_method = "POST"
    type                    = "AWS_PROXY"
    uri                     = "${aws_lambda_function.albatross.invoke_arn}"
}
