def get_mock_server(instance_id="id", state="running"):
    return {"State": {"Name": state}, "InstanceId": instance_id}

