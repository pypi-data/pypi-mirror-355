# Terra MCP Server

A Model Context Protocol server that allows LLMs to configure the [TerraAPI dashboard](https://dashboard.tryterra.co/).

### Quickstart

Get started quickly with one of these installation options:

**For Cursor users:**
[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=terramcp&config=eyJjb21tYW5kIjoidXZ4IHRlcnJhbWNwIiwiZW52Ijp7IlRFUlJBX0FQSV9LRVkiOiJ5b3VyX2FwaV9rZXlfaGVyZSIsIlRFUlJBX0RFVl9JRCI6InlvdXItZGV2LWlkLWhlcmUifX0%3D)

**For VS Code users:**
[![Install with UV in VS Code](https://img.shields.io/badge/VS_Code-UV-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=terramcp&config=%7B%22command%22:%22uvx%22,%22args%22:%5B%22terramcp%22%5D%7D)


### Available Tools

* `terra_get_integrations`
  * Description: Get list of available [integrations](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#source-provider-integration).
  * Parameters: None
* `terra_get_detailed_integrations`
  * Description: Retrieve a detailed list of [supported integrations](https://docs.tryterra.co/reference/health-and-fitness-api/supported-integrations), filtered by the developer's enabled integrations and the requirement for SDK usage.
  * Parameters:
    * `sdk` (Optional[bool]): If true, allows SDK integrations to be included in the response.
* `get_destinations`
  * Description: Get [destinations](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#destinations).
  * Parameters: None
* `get_developer_destination_credentials`
  * Description: Get developer [destination](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#destinations) credentials.
  * Parameters:
    * `destination` (str): The destination to get credentials for.
* `delete_destination`
  * Description: Delete a [destination](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#destinations).
  * Parameters:
    * `destination` (str): The destination to delete.
    * `dev_id` (Optional[str]): Developer ID. If not provided, uses the environment variable.
* `set_destination_state`
  * Description: Set [destination](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#destinations) state (active or inactive).
  * Parameters:
    * `destination` (str): The destination to update.
    * `active` (bool): Whether the destination should be active or not.
* `add_developer_destination`
  * Description: Add developer [destination](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#destinations).
  * Parameters:
    * `destination` (str): The destination type to add (e.g. 's3', 'sql', 'webhook').
    * `scheme` (str): The scheme (e.g 's3/postgres/https/mysql').
    * `host` (str): The host (e.g 'webhook.site', 'eu-west-2', 'localhost').
    * `path` (Optional[str]): The path (e.g bucket name, database name, webhook path without leading '/').
    * `user` (Optional[str]): Username for credentials.
    * `password` (Optional[str]): Password for credentials.
    * `port` (Optional[int]): Port for the service if needed.
    * `query` (Optional[str]): Query string if needed.
    * `certificate` (Optional[str]): Certificate for certain destinations like GCS.
    * `complete_destination` (bool, default: True): If true, ping the destination before adding.
* `ping_developer_destination`
  * Description: Ping a developer [destination](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#destinations) to check if it's reachable.
  * Parameters:
    * `destination` (str): The destination type to ping.
    * `scheme` (str): The scheme (e.g 's3/postgres/https/mysql').
    * `host` (str): The host (e.g 'webhook.site', 'eu-west-2', 'localhost').
    * `path` (Optional[str]): The path (e.g bucket name, database name, webhook path).
    * `user` (Optional[str]): Username for credentials.
    * `password` (Optional[str]): Password for credentials.
    * `port` (Optional[int]): Port for the service if needed.
    * `query` (Optional[str]): Query string if needed.
    * `certificate` (Optional[str]): Certificate for certain destinations like GCS.
* `set_provider_keys`
  * Description: Set [provider](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#source-provider-integration) keys.
  * Parameters:
    * `resource` (str): The provider resource.
    * `client_id` (str): The client ID for the provider.
    * `client_secret` (str): The client secret for the provider.
    * `redirect_url` (Optional[str]): The redirect URL for the provider.
* `get_provider_keys`
  * Description: Get [provider](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#source-provider-integration) keys.
  * Parameters:
    * `resource` (str): The provider resource.
* `get_developer_providers`
  * Description: Get developer providers.
  * Parameters: None
* `add_providers`
  * Description: Add [providers](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#source-provider-integration).
  * Parameters:
    * `providers` (list[str]): list of providers to add.
* `deactivate_provider`
  * Description: Delete [provider](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#source-provider-integration).
  * Parameters:
    * `provider` (str): The provider to deactivate.
* `set_provider_state`
  * Description: Set provider state (active or inactive).
  * Parameters:
    * `provider` (str): The provider to update.
    * `active` (bool): Whether the provider should be active or not.
* `get_providers_by_popularity`
  * Description: Get [providers](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#source-provider-integration) ranked by popularity.
  * Parameters: None
* `add_custom_credentials`
  * Description: Add custom credentials for a [provider](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#source-provider-integration).
  * Parameters:
    * `provider` (str): The provider to add credentials for.
    * `client_id` (str): The client ID.
    * `client_secret` (str): The client secret.
    * `redirect_url` (Optional[str]): The redirect URL.
* `get_custom_credentials`
  * Description: Get custom credentials for a [provider](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#source-provider-integration).
  * Parameters:
    * `provider` (str): The provider to get credentials for.
* `search_documentation`
  * Description: Allows the MCP client to search our [docs](https://docs.tryterra.co/).
  * Parameters:
    * `query` (str): Search query.

## Installation

> [!NOTE]
> You will need your [`TERRA_API_KEY`](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#api-key) and [`TERRA_DEV_ID`](https://docs.tryterra.co/reference/health-and-fitness-api/core-concepts#developer-id-dev-id) which is available from the [dashboard](https://dashboard.tryterra.co/)

### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *terramcp*.

#### `uv` Installation

*Mac / Linux*

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

*Windows*

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Using PIP

Alternatively you can install `terramcp` via pip:

```bash
pip install terramcp
```

After installation, you can run it as a script using:

```bash
python -m terramcp
```

## Configuration

### Configure for Claude.app

Add to your Claude settings:

<details>
<summary>Using uvx</summary>

```json
{
  "mcpServers": {
    "terramcp": {
      "command": "uvx",
      "args": ["terramcp"],
      "env": {
        "TERRA_API_KEY": "your_api_key_here",
        "TERRA_DEV_ID": "your-dev-id-here"
      }
    }
  }
}
```

</details>

<details>
<summary>Using pip installation</summary>

```json
{
  "mcpServers": {
    "terramcp": {
      "command": "python",
      "args": ["-m", "terramcp"],
      "env": {
        "TERRA_API_KEY": "your_api_key_here",
        "TERRA_DEV_ID": "your-dev-id-here"
      }
    }
  }
}
```

</details>

### Configure for Zed

Add to your Zed settings.json:

<details>
<summary>Using uvx</summary>

```json
"context_servers": [
  "terramcp": {
    "command": "uvx",
    "args": ["terramcp"],
    "env": {
        "TERRA_API_KEY": "your_api_key_here",
        "TERRA_DEV_ID": "your-dev-id-here"
    }
  }
],
```

</details>

<details>
<summary>Using pip installation</summary>

```json
"context_servers": {
  "terramcp": {
    "command": "python",
    "args": ["-m", "terramcp"],
    "env": {
        "TERRA_API_KEY": "your_api_key_here",
        "TERRA_DEV_ID": "your-dev-id-here"
    }
  }
},
```

</details>

### Configure for VS Code

For quick installation, use one of the one-click install buttons below...

[![Install with UV in VS Code](https://img.shields.io/badge/VS_Code-UV-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=terramcp&config=%7B%22command%22:%22uvx%22,%22args%22:%5B%22terramcp%22%5D%7D) [![Install with UV in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-UV-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=terramcp&config=%7B%22command%22:%22uvx%22,%22args%22:%5B%22terramcp%22%5D%7D&quality=insiders)


For manual installation, add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` and typing `Preferences: Open User Settings (JSON)` .

Optionally, you can add it to a file called `.vscode/mcp.json` in your workspace. This will allow you to share the configuration with others.

> Note that the `mcp` key is needed when using the `mcp.json` file.

<details>
<summary>Using uvx</summary>

```json
{
  "mcp": {
    "servers": {
      "terramcp": {
        "command": "uvx",
        "args": ["terramcp"],
        "env": {
            "TERRA_API_KEY": "your_api_key_here",
            "TERRA_DEV_ID": "your-dev-id-here"
        }
      }
    }
  }
}
```

</details>

## Debugging

You can use the MCP inspector to debug the server. For uvx installations:

```bash
npx @modelcontextprotocol/inspector uvx terramcp
```

Or if you've installed the package in a specific directory or are developing on it:

```bash
cd path/to/servers/src/terramcp
npx @modelcontextprotocol/inspector uv run terramcp
```

## License

terramcp is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the [LICENSE](https://github.com/tryterra/terramcp/blob/master/LICENSE) file in the project repository.
