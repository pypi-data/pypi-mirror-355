# Weni Data Lake SDK

The Weni Data Lake SDK is a Python library that provides an interface to interact with Weni's data lake services. It supports operations for sending data, managing message templates, and handling traces.

## Installation

```bash
pip install weni-datalake-sdk
In case you are using poetry, you can add the package to your project with the following command:
poetry add weni-datalake-sdk
```

## Environment Variables

Before using the SDK, make sure to set up the following environment variables:

```bash
DATALAKE_SERVER_ADDRESS=your_server_address
REDSHIFT_QUERY_BASE_URL=your_redshift_url
REDSHIFT_SECRET=your_secret
REDSHIFT_ROLE_ARN=your_role_arn
MESSAGE_TEMPLATES_METRIC_NAME=your_metric_name
TRACES_METRIC_NAME=your_trace_metric_name
```

## Usage Examples

### 1. Sending Data

```python
from weni_datalake_sdk.clients.client import send_data
from weni_datalake_sdk.paths.your_path import YourPath

# Prepare your data
data = {
    "field1": "value1",
    "field2": "value2"
}

# Send data using a path class
send_data(YourPath, data)

# Or using an instantiated path
path = YourPath()
send_data(path, data)
```

### 2. Working with Message Templates

```python
from weni_datalake_sdk.clients.redshift.message_templates import get_message_templates

# Get templates with specific parameters
result = get_message_templates(
    contact_urn="contact123",
    template_id="template456"
)

```

### 3. Working with Traces

```python
from weni_datalake_sdk.clients.redshift.traces import get_traces

# Get traces with query parameters
result = get_traces(
    query_params={
        "message_uuid": "123e4567-e89b-12d3-a456-426614174000"
    }
)
```

### 4. Sending Message Template Data

```python
from weni_datalake_sdk.clients.client import send_message_template_data
from weni_datalake_sdk.paths.message_template import MessageTemplatePath

template_data = {
    "template_id": "template123",
    "content": "Hello, {{name}}!",
    "status": "approved"
}

status = send_message_template_data(MessageTemplatePath, template_data)
```

## Error Handling

The SDK includes proper error handling. Always wrap your calls in try-except blocks:

```python
try:
    result = get_message_templates(template_id="template123")
except Exception as e:
    print(f"Error: {e}")
```

## Best Practices

1. **Environment Variables**: Always ensure all required environment variables are set before using the SDK.
2. **Path Validation**: Use proper path classes instead of raw strings.
3. **Error Handling**: Implement proper error handling in your code.
4. **Data Types**: Ensure you're passing the correct data types for each parameter.
5. **Security**: Never hardcode sensitive information like tokens or credentials.

## Common Issues and Solutions

1. **Connection Issues**
   - Ensure `DATALAKE_SERVER_ADDRESS` is correct and accessible
   - Check your network connectivity

2. **Authentication Errors**
   - Verify your AWS credentials are properly configured
   - Check if `REDSHIFT_SECRET` and `REDSHIFT_ROLE_ARN` are correct

3. **Missing Environment Variables**
   - Double-check all required environment variables are set
   - Use a `.env` file for local development

## Contributing

For contributing to this SDK, please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
