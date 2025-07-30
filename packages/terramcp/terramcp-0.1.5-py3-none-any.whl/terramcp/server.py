import os
from enum import Enum
from typing import Any, Optional

import requests
from fastmcp import FastMCP

mcp = FastMCP(
    name="Terra Dashboard MCP Server",
    instructions="Use this MCP server to configure your Terra Application",
    dependencies=["requests"],
)

BASE_API_URL = "https://api.tryterra.co/v2"

# Set the API key from environment variable
API_KEY = os.getenv("TERRA_API_KEY")
DEV_ID = os.getenv("TERRA_DEV_ID")

assert API_KEY, "TERRA_API_KEY environment variable is not set."
assert DEV_ID, "TERRA_DEV_ID environment variable is not set."


def get_default_headers():
    headers = {"X-API-Key": API_KEY, "dev-id": DEV_ID, "User-Agent": "Terra-MCP/1.0.0"}
    return headers


# Get list of available integrations
@mcp.tool()
def terra_get_integrations() -> str:
    """
    Get list of available integrations.

    Returns:
        str: list of available integrations in json format
    """
    data = requests.get(f"{BASE_API_URL}/integrations", headers=get_default_headers())
    return data.json()


# Get detailed list of integrations
@mcp.tool()
def terra_get_detailed_integrations(sdk: Optional[bool] = None) -> str:
    """
    Retrieve a detailed list of supported integrations, filtered by the developer's enabled integrations and the requirement for SDK usage.

    Args:
        sdk (Optional[bool]): If true, allows SDK integrations to be included in the response.
    Returns:
        str: Detailed list of integrations in json format
    """
    params = {}
    if sdk is not None:
        params["sdk"] = sdk

    data = requests.get(
        f"{BASE_API_URL}/integrations/detailed",
        params=params,
        headers=get_default_headers(),
    )
    return data.json()


@mcp.tool()
def get_destinations() -> dict[str, Any]:
    """
    Get destinations.

    Returns:
        dict[str, Any]: list of destinations or destination details for a specific developer
    """
    params = {"dev_id": DEV_ID}

    response = requests.get(
        f"{BASE_API_URL}/dashboard/destinations",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def get_developer_destination_credentials(destination: str) -> dict[str, Any]:
    """
    Get developer destination credentials.

    Args:
        destination (str): The destination to get credentials for

    Returns:
        dict[str, Any]: Destination credentials details
    """
    params = {"destination": destination}

    response = requests.get(
        f"{BASE_API_URL}/dashboard/destinations/credentials",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def delete_destination(
    destination: str, dev_id: Optional[str] = None
) -> dict[str, Any]:
    """
    Delete a destination.

    Args:
        destination (str): The destination to delete
        dev_id (Optional[str]): Developer ID. If not provided, uses the environment variable.

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    payload = {"dev_id": dev_id or DEV_ID, "destination": destination}

    response = requests.delete(
        f"{BASE_API_URL}/dashboard/destinations",
        json=payload,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def set_destination_state(destination: str, active: bool) -> dict[str, Any]:
    """
    Set destination state (active or inactive).

    Args:
        destination (str): The destination to update
        active (bool): Whether the destination should be active or not

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    payload = {"dev_id": DEV_ID, "destination": destination, "active": active}

    response = requests.patch(
        f"{BASE_API_URL}/dashboard/destinations",
        json=payload,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def add_developer_destination(
    destination: str,
    scheme: str,
    host: str,
    path: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    port: Optional[int] = None,
    query: Optional[str] = None,
    certificate: Optional[str] = None,
    complete_destination: bool = True,
) -> dict[str, Any]:
    """
    Add developer destination.

    Args:
        destination (str): The destination type to add (e.g. 's3', 'sql', 'webhook')
        scheme (str): The scheme (e.g 's3/postgres/https/mysql')
        host (str): The host (e.g 'webhook.site', 'eu-west-2', 'localhost')
        path (Optional[str]): The path (e.g bucket name, database name, webhook path without leading '/')
        user (Optional[str]): Username for credentials
        password (Optional[str]): Password for credentials
        port (Optional[int]): Port for the service if needed
        query (Optional[str]): Query string if needed
        certificate (Optional[str]): Certificate for certain destinations like GCS
        complete_destination (bool): If true, ping the destination before adding

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    payload = {
        "destination": destination,
        "dev_id": DEV_ID,
        "scheme": scheme,
        "host": host,
        "complete_destination": complete_destination,
    }

    if path is not None:
        payload["path"] = path
    if user is not None:
        payload["user"] = user
    if password is not None:
        payload["password"] = password
    if port is not None:
        payload["port"] = port
    if query is not None:
        payload["query"] = query
    if certificate is not None:
        payload["certificate"] = certificate

    response = requests.post(
        f"{BASE_API_URL}/dashboard/destinations",
        json=payload,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def ping_developer_destination(
    destination: str,
    scheme: str,
    host: str,
    path: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    port: Optional[int] = None,
    query: Optional[str] = None,
    certificate: Optional[str] = None,
) -> dict[str, Any]:
    """
    Ping a developer destination to check if it's reachable.

    Args:
        destination (str): The destination type to ping
        scheme (str): The scheme (e.g 's3/postgres/https/mysql')
        host (str): The host (e.g 'webhook.site', 'eu-west-2', 'localhost')
        path (Optional[str]): The path (e.g bucket name, database name, webhook path)
        user (Optional[str]): Username for credentials
        password (Optional[str]): Password for credentials
        port (Optional[int]): Port for the service if needed
        query (Optional[str]): Query string if needed
        certificate (Optional[str]): Certificate for certain destinations like GCS

    Returns:
        dict[str, Any]: Response indicating ping success or failure
    """
    payload = {
        "destination": destination,
        "dev_id": DEV_ID,
        "scheme": scheme,
        "host": host,
    }

    if path is not None:
        payload["path"] = path
    if user is not None:
        payload["user"] = user
    if password is not None:
        payload["password"] = password
    if port is not None:
        payload["port"] = port
    if query is not None:
        payload["query"] = query
    if certificate is not None:
        payload["certificate"] = certificate

    response = requests.post(
        f"{BASE_API_URL}/dashboard/destinations/ping",
        json=payload,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def set_provider_keys(
    resource: str,
    client_id: str,
    client_secret: str,
    redirect_url: Optional[str] = None,
) -> dict[str, Any]:
    """
    Set provider keys.

    Args:
        resource (str): The provider resource
        client_id (str): The client ID for the provider
        client_secret (str): The client secret for the provider
        redirect_url (Optional[str]): The redirect URL for the provider

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    params = {
        "resource": resource,
        "client_id": client_id,
        "client_secret": client_secret,
        "dev_id": DEV_ID,
    }

    if redirect_url:
        params["redirect_url"] = redirect_url

    response = requests.patch(
        f"{BASE_API_URL}/dashboard/providerKeys",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def get_provider_keys(resource: str) -> dict[str, Any]:
    """
    Get provider keys.

    Args:
        resource (str): The provider resource

    Returns:
        dict[str, Any]: Provider key details
    """
    params = {"resource": resource, "dev_id": DEV_ID}

    response = requests.get(
        f"{BASE_API_URL}/dashboard/providerKeys",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def get_developer_providers() -> dict[str, Any]:
    """
    Get developer providers.

    Args:
        None

    Returns:
        dict[str, Any]: list of provider details
    """
    params = {"dev_id": DEV_ID}

    response = requests.get(
        f"{BASE_API_URL}/dashboard/providers",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def add_providers(providers: list[str]) -> dict[str, Any]:
    """
    Add providers.

    Args:
        providers (list[str]): list of providers to add

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    payload = {"dev_id": DEV_ID, "providers": providers}

    response = requests.post(
        f"{BASE_API_URL}/dashboard/providers",
        json=payload,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def deactivate_provider(provider: str) -> dict[str, Any]:
    """
    Delete provider.

    Args:
        provider (str): The provider to deactivate

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    payload = {"dev_id": DEV_ID, "provider": provider}

    response = requests.delete(
        f"{BASE_API_URL}/dashboard/providers",
        json=payload,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def set_provider_state(provider: str, active: bool) -> dict[str, Any]:
    """
    Set provider state (active or inactive).

    Args:
        provider (str): The provider to update
        active (bool): Whether the provider should be active or not

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    payload = {"dev_id": DEV_ID, "provider": provider, "active": active}

    response = requests.patch(
        f"{BASE_API_URL}/dashboard/providers",
        json=payload,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def get_providers_by_popularity() -> dict[str, Any]:
    """
    Get providers ranked by popularity.

    Returns:
        dict[str, Any]: list of providers ranked by popularity
    """
    response = requests.get(
        f"{BASE_API_URL}/dashboard/providers/ranked", headers=get_default_headers()
    )
    return response.json()


@mcp.tool()
def add_custom_credentials(
    provider: str,
    client_id: str,
    client_secret: str,
    redirect_url: Optional[str] = None,
) -> dict[str, Any]:
    """
    Add custom credentials for a provider.

    Args:
        provider (str): The provider to add credentials for
        client_id (str): The client ID
        client_secret (str): The client secret
        redirect_url (Optional[str]): The redirect URL

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    payload = {
        "provider": provider,
        "client_id": client_id,
        "client_secret": client_secret,
        "dev_id": DEV_ID,
    }

    if redirect_url:
        payload["redirect_url"] = redirect_url

    response = requests.post(
        f"{BASE_API_URL}/dashboard/providers/credentials",
        json=payload,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def get_custom_credentials(provider: str) -> dict[str, Any]:
    """
    Get custom credentials for a provider.

    Args:
        provider (str): The provider to get credentials for

    Returns:
        dict[str, Any]: Provider credential details
    """
    params = {"provider": provider}

    response = requests.get(
        f"{BASE_API_URL}/dashboard/providers/credentials",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def search_documentation(query: str) -> dict[str, Any]:
    """
    Search documentation using AI.
    Use this whenever you are unsure about the API or how to use it.
    Ask questions like "How do I build a application that integrates with Terra?" or "What is the best way to integrate with the API?"

    Args:
        query (str): The search query. Written in natural language.
        This will be used to search the documentation.

    Returns:
        str: Response from the AI model.
    """
    params = {"query": query}

    response = requests.post(
        "https://ubd7f3f36wgejf3kvci5647fby0ueuvi.lambda-url.eu-west-1.on.aws",
        json=params,
        headers=get_default_headers(),
    )
    return response.json().get("content", "No response was received.")


class Data_Type(Enum):
    """Enum for data types"""

    BODY = "Body"
    NUTRITION = "Nutrition"
    MENSTRUATION = "Menstruation"
    SLEEP = "Sleep"
    DAILY = "Daily"
    ACTIVITY = "Activity"


@mcp.tool()
def generate_dummy_data(
    type: str,
    user_id: str,
    reference_id: str,
    webhook_url: str,
    for_provider: str,
    to_send: bool,
) -> str:
    """
    Generate dummy data for testing purposes.
    Terra will POST data to the webhook URL specified if to_send is true.
    This is useful for testing your application and ensuring that it can handle data from different providers.
    Generated data confoms to the webhook data model.

    Args:
        type (str): The type of data to generate. Possible values ['Body','Nutrition','Menstruation','Sleep','Daily','Activity']
        user_id (str): The user ID to associate with the generated data.
        reference_id (str): The reference ID for the generated data.
        webhook_url (str): The webhook URL to send the generated data to.
        for_provider (str): The provider to use for generating the data. Possible values ['apple','concept2','eight','fitbit','freestylelibre','garmin','google','ifit','oura','peloton','polar','samsung','suunto','omron','coros','tempo','trainingpeaks','wahoo','whoop','wearos','withings','zwift','fatsecret','cronometer','myfitnesspal','nutracheck','underarmour','googlefit']
        to_send (bool): If true, send the generated data to the webhook URL. Else, just generate the data.
    Returns:
        str: The response from the API.
    """
    params = {
        "type": type,
        "dev_id": DEV_ID,
        "send": "true" if to_send else "false",
        "user_id": user_id,
        "reference_id": reference_id,
        "webhook_url": webhook_url,
        "for_provider": for_provider,
    }
    response = requests.get(
        f"{BASE_API_URL}/dashboard/generateData",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def get_paginated_webhook_history(
    start_date: str,
    end_date: str,
    limit: int,
    offset: int,
    provider: Optional[str] = None,
    data_type: Optional[str] = None,
    user_id: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get paginated webhook history.
    The webhook history is paginated, so you can use the limit and offset parameters to get a specific page of results.

    Args:
        start_timestamp (str): The start date for the webhook history in ISO 8601 format.
        end_timestamp (str): The end date for the webhook history in ISO 8601 format.
        limit (int): The number of records to return per page.
        offset (int): The offset for pagination.
        provider (Optional[str]): The provider to filter by.
        data_type (Optional[str]): The data type to filter by.
        user_id (Optional[str]): The user ID to filter by.
        reference_id (Optional[str]): The reference ID to filter by.


    Returns:
        dict[str, Any]: Webhook history
    """
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "offset": offset,
    }
    if provider:
        params["provider"] = provider
    if data_type:
        params["data_type"] = data_type
    if user_id:
        params["user_id"] = user_id
    if reference_id:
        params["reference_id"] = reference_id

    response = requests.get(
        f"{BASE_API_URL}/dashboard/webhooks",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


@mcp.tool()
def resend_webhook(user_id: str, timestamp: str):
    """
    Resend a webhook. Looks up the webhook by user_id and timestamp.

    Args:
        user_id (str): The user ID to resend the webhook to.
        timestamp (str): The timestamp of the webhook to resend. ISO 8601 format.

    Returns:
        dict[str, Any]: Response indicating success or failure
    """
    params = {"user_id": user_id, "timestamp": timestamp}

    response = requests.post(
        f"{BASE_API_URL}/dashboard/webhooks/resend",
        params=params,
        headers=get_default_headers(),
    )
    return response.json()


# Check if API key is set


@mcp.resource("config://api_key")
def get_api_key() -> str:
    """Get the API key"""
    if API_KEY:
        return f"API key is set: {API_KEY}"
    else:
        raise ValueError(
            "API key is not set. Please set the TERRA_API_KEY environment variable."
        )


# Check if developer ID is set
@mcp.resource("config://dev_id")
def get_dev_id() -> str:
    """Get the developer ID"""
    if DEV_ID:
        return f"Developer key is set: {DEV_ID}"
    else:
        raise ValueError(
            "Developer ID is not set. Please set the TERRA_DEV_ID environment variable."
        )


# About Terra

@mcp.resource("config://about")
def get_about() -> str:
    """Get about information"""
    return (
        "The Terra API standardizes health and fitness data, allowing you to use it structured and efficient manner, no matter the source."
        "It allows developers to integrate and manage their data sources easily."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
