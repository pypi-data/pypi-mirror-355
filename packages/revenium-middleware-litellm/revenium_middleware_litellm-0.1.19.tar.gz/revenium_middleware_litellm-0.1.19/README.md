# 🤖 Revenium Middleware for LiteLLM

[![PyPI version](https://img.shields.io/pypi/v/revenium-middleware-litellm.svg)](https://pypi.org/project/revenium-middleware-litellm/)
[![Python Versions](https://img.shields.io/pypi/pyversions/revenium-middleware-litellm.svg)](https://pypi.org/project/revenium-middleware-litellm/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

A middleware library for metering and monitoring LiteLLM usage in Python applications, supporting both direct client calls and the LiteLLM proxy. 🐍✨

## ✨ Features

- **📊 Precise Usage Tracking**: Monitor tokens, costs, and request counts across all LLM API endpoints via LiteLLM.
- **🔌 Seamless Integration**:
    - **Client:** Drop-in middleware that works with minimal code changes for `litellm.completion`.
    - **Proxy:** Custom callback middleware for easy integration with the LiteLLM proxy.
- **⚙️ Flexible Configuration**: Customize metering behavior to suit your application needs.
- **📈 Enhanced Metadata**: Track detailed usage context like trace IDs, task types, and user identifiers.

## 📥 Installation

Install the base package along with the specific middleware you need:

```bash
# For LiteLLM client-side metering ONLY
pip install "revenium-middleware-litellm[litellm_client]"

# For LiteLLM proxy metering ONLY
pip install "revenium-middleware-litellm[litellm_proxy]"

# To install BOTH client and proxy middleware support
pip install "revenium-middleware-litellm[litellm_all]"
```

## 🔧 Usage: LiteLLM Client Middleware

This middleware automatically intercepts `litellm.completion` calls made directly from your Python code.

### 🔄 Zero-Config Integration

Simply export your `REVENIUM_METERING_API_KEY` (and other relevant Revenium environment variables) and import the middleware module *before* your first call to `litellm.completion`. Your LiteLLM calls will be metered automatically:

```python
import litellm
import os

# Ensure Revenium environment variables (e.g., REVENIUM_METERING_API_KEY) are set
# os.environ["REVENIUM_METERING_API_KEY"] = "YOUR_REVENIUM_METERING_API_KEY"
# os.environ["REVENIUM_PRODUCT_ID"] = "YOUR_REVENIUM_PRODUCT_ID" # Optional, but recommended

# Import the client middleware module to activate patching
import revenium_middleware_litellm_client.middleware

# Now use litellm.completion as usual
response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[{ "content": "Why is the sky blue?","role": "user"}]
)
print(response.choices[0].message.content)
```

The middleware automatically intercepts LiteLLM API calls and sends metering data to Revenium without requiring changes to your existing `litellm.completion` calls. Make sure to configure the underlying `revenium_middleware` (e.g., set the `REVENIUM_METERING_API_KEY` environment variable) for authentication with the Revenium service.

### 📈 Enhanced Tracking with Metadata

For more granular usage tracking and detailed reporting, add the `usage_metadata` parameter directly to your `litellm.completion` call:

```python
import litellm
import revenium_middleware_litellm_client.middleware # Ensure middleware is imported

response = litellm.completion(
    model="gpt-3.5-turbo",
    messages=[{ "content": "Why is the sky blue?","role": "user"}],
    usage_metadata={
         "trace_id": "conv-28a7e9d4",
         "task_type": "summarize-customer-issue",
         "subscriber_email": "user@example.com",
         "subscriber_id": "subscriberid-1234567890",
         "subscriber_credential_name": "engineering-api-key",
         "organization_id": "acme-corp",
         "subscription_id": "startup-plan-Q1",
         "product_id": "saas-app-gold-tier",
         "agent": "support-agent",
    },
)
print(response.choices[0].message.content)
```

#### 🏷️ Metadata Fields

The `usage_metadata` parameter supports the following fields:

| Field                        | Description                                               | Use Case                                                          |
|------------------------------|-----------------------------------------------------------|-------------------------------------------------------------------|
| `trace_id`                   | Unique identifier for a conversation or session           | Group multi-turn conversations into single event for performance & cost tracking                           |
| `task_type`                  | Classification of the AI operation by type of work        | Track cost & performance by purpose (e.g., classification, summarization)                                  |
| `subscriber_email`           | The email address of the subscriber                       | Track cost & performance by individual users (if customer e-mail addresses are known)                      |
| `subscriber_id`              | The id of the subscriber from non-Revenium systems        | Track cost & performance by individual users (if customers are anonymous or tracking by emails is not desired)   |
| `subscriber_credential_name` | An alias for an API key used by one or more users         | Track cost & performance by individual API keys                                                            |
| `subscriber_credential`      | The key value associated with the subscriber (i.e an API key)     | Track cost & performance by API key value (normally used when the only identifier for a user is an API key) |
| `organization_id`            | Customer or department ID from non-Revenium systems       | Track cost & performance by customers or business units                                                    |
| `subscription_id`            | Reference to a billing plan in non-Revenium systems       | Track cost & performance by a specific subscription                                                        |
| `product_id`                 | Your product or feature making the AI call                | Track cost & performance across different products                                                         |
| `agent`                      | Identifier for the specific AI agent                      | Track cost & performance performance by AI agent                                                           |
| `response_quality_score`     | The quality of the AI response (0..1)                     | Track AI response quality                                                                                  |

**All metadata fields are optional**. Adding them enables more detailed reporting and analytics in Revenium.

---

## 🔧 Usage: LiteLLM Proxy Middleware

This middleware integrates with the LiteLLM proxy using its custom callback mechanism.

### 🔄 Integration with LiteLLM Proxy

To integrate the Revenium middleware with your LiteLLM proxy, you need to:

1. Install the middleware (`pip install "revenium-middleware-litellm[litellm_proxy]"`).
2. Ensure Revenium environment variables (e.g., `REVENIUM_METERING_API_KEY`) are set where the proxy runs.
3. Configure your LiteLLM proxy to use the Revenium middleware callback.

#### Configuration

Add the Revenium middleware callback path to your LiteLLM `config.yaml`:

```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo # Example using OpenAI provider prefix
      api_key: "os.environ/OPENAI_API_KEY"

general_settings:
  master_key: "sk-1234" # Example master key

litellm_settings:
  # Add the absolute path to the installed middleware's proxy_handler_instance
  callbacks: ["revenium_middleware_litellm_proxy.middleware.proxy_handler_instance"]
  # Example database URL (optional, for LiteLLM's own logging)
  # database_url: "postgresql://user:password@localhost/litellm"
```

> **⚠️ Important Note on Callbacks**: LiteLLM proxy expects the `callbacks` list to contain importable Python paths to the callback handler instances. Ensure the `revenium-middleware-litellm` package is installed in the Python environment where the LiteLLM proxy runs. You do *not* need an absolute file path if the package is correctly installed.

### 📈 Enhanced Tracking with Custom Headers (Proxy)

For more granular usage tracking when using the proxy, add custom HTTP headers to your API requests made *to* the LiteLLM proxy endpoint:

```python
# Example using requests library to call the LiteLLM proxy
import requests
import json

proxy_url = "http://localhost:4000/chat/completions" # Your LiteLLM proxy URL
api_key = "sk-1234" # Your LiteLLM proxy master key or virtual key

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
    # Revenium Custom Headers
    "x-revenium-trace-id": "conv-28a7e9d4",
    "x-revenium-task-type": "summarize-customer-issue",
    "x-revenium-organization-id": "acme-corp",
    "x-revenium-product-id": "saas-app-gold-tier",
    "x-revenium-agent": "support-agent",
    "x-revenium-subscriber-email": "user@example.com",
    "x-revenium-subscriber-id": "subscriberid-1234567890",
    "x-revenium-subscriber-credential-name": "engineering-api-key",
}

data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the meaning of life?"}
    ]
}

response = requests.post(proxy_url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.json())

```

#### 🏷️ Custom HTTP Headers (Proxy)

The `usage_metadata` parameter supports the following fields:

| Field                        | Description                                               | Use Case                                                          |
|------------------------------|-----------------------------------------------------------|-------------------------------------------------------------------|
| `x-revenium-trace-id`                   | Unique identifier for a conversation or session           | Group multi-turn conversations into single event for performance & cost tracking                           |
| `x-revenium-task-type`                  | Classification of the AI operation by type of work        | Track cost & performance by purpose (e.g., classification, summarization)                                  |
| `x-revenium-subscriber-email`           | The email address of the subscriber                       | Track cost & performance by individual users (if customer e-mail addresses are known)                      |
| `x-revenium-subscriber-id`              | The id of the subscriber from non-Revenium systems        | Track cost & performance by individual users (if customers are anonymous or tracking by emails is not desired)   |
| `x-revenium-subscriber-credential-name` | An alias for an API key used by one or more users         | Track cost & performance by individual API keys                                                            |
| `x-revenium-subscriber-credential`      | The key value associated with the subscriber (i.e an API key)     | Track cost & performance by API key value (normally used when the only identifier for a user is an API key) |
| `x-revenium-organization-id`            | Customer or department ID from non-Revenium systems       | Track cost & performance by customers or business units                                                    |
| `x-revenium-subscription-id`            | Reference to a billing plan in non-Revenium systems       | Track cost & performance by a specific subscription                                                        |
| `x-revenium-product-id`                 | Your product or feature making the AI call                | Track cost & performance across different products                                                         |
| `x-revenium-agent`                      | Identifier for the specific AI agent                      | Track cost & performance performance by AI agent                                                           |


**All metadata fields are optional**. Adding them enables more detailed reporting and analytics in Revenium.

All custom headers are optional. Adding them enables more detailed reporting and analytics in Revenium. The proxy middleware extracts these headers from the incoming request.

---

## 🔄 Compatibility

- 🐍 Python 3.8+
- 🤖 LiteLLM (Client usage & Proxy v1.15.0+)
- 🌐 Works with all LLM models and providers supported by LiteLLM

## 🔍 Logging

This module uses Python's standard logging system, inheriting configuration from the core `revenium_middleware`. You can control the log level by setting the `REVENIUM_LOG_LEVEL` environment variable:

```bash
# Enable debug logging
export REVENIUM_LOG_LEVEL=DEBUG

# Or when running your script (for client middleware)
REVENIUM_LOG_LEVEL=DEBUG python your_script.py

# Or when starting the proxy (for proxy middleware)
REVENIUM_LOG_LEVEL=DEBUG litellm --config /path/to/config.yaml
```

Available log levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only
- `CRITICAL`: Critical error messages only

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🙏 Acknowledgments

- 💖 Built with ❤️ by the Revenium team
