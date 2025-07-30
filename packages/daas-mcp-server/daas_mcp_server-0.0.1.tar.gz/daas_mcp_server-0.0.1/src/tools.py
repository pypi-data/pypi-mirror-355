"""Tools for the DaaS MCP Server."""

import json
import os

import httpx
from langchain_core.runnables.config import RunnableConfig

from daas_mcp_server.constants import UNKNOWN
from daas_mcp_server.utils.cc_auth_client import auth_token_with_prefix
from daas_mcp_server.utils.logging import get_logger
from utility.cc_auth_client import get_token_in_cache

logger = get_logger(__name__)

client = httpx.AsyncClient()

customer = "qrrzoz820te8"
bearer_token = ""


async def get_latest_log(config: RunnableConfig) -> str:
    """Get the latest log in the site.

    This tool is designed to retrieve the latest log which indicates the actions performed by admins from the customers' DDC or site.

    Use this tool when the user wants to:
        - Get the latest log in the site.
        - Get the latest action performed by admins.

    Returns:
        str: The latest log in the site.
    """
    try:
        customer_id = config.get("configurable", {}).get("customer_id", "")
        user_id = config.get("configurable", {}).get("user_id", "")
        if not customer_id or not user_id:
            return "customer_id or user_id is not provided in the configuration, please provide both."

        auth_token = await get_token_in_cache(customer_id, user_id)

        if not auth_token or len(auth_token) == 0:
            return "Failed to get the auth token from the cache."

        virtual_site_id = await get_site_id(customer_id, auth_token)

        url = f"{os.getenv('WEBSTUDIO_API_ENDPOINT') % customer_id}/{customer_id}/{virtual_site_id}/ConfigLog/Operations/$search?limit=20"
        payload = {
            "SearchFilterGroups": [
                {
                    "SearchType": "And",
                    "SearchFilters": [
                        {
                            "Property": "StartTime",
                            "Value": "Last7Days",
                            "Operator": "IsWithin",
                        }
                    ],
                }
            ],
            "BasicSearchString": "",
            "SearchType": "And",
            "SortCriteria": {"Property": "StartTime", "SortDirection": "Descending"},
        }
        headers = {
            "Authorization": f"Bearer {auth_token}",
        }

        result = await client.post(url, json=payload, headers=headers)

        if result.status_code == 200:
            loggings = result.json().get("Items", [])
            loggings = [
                {logging.get("Text", UNKNOWN) + "by" + logging.get("User", UNKNOWN)}
                for logging in loggings
            ]
            return json.dumps(loggings, ensure_ascii=False)
        else:
            return f"Failed to get loggings. Status code: {result.status_code}, Response: {result.text}"
    except Exception as err:
        logger.error(f"Failed to get loggings. Error: {err}")
        return f"Failed to get loggings. Error: {err}"


async def get_delivery_groups(config: RunnableConfig) -> str:
    """Get the full list of delivery groups from the site.

    This tool is designed to retrieve the real data from the customers' DDC or site.

    Use this tool when the user wants to:
        - Get the list of delivery groups in the site.
        - Get the list of delivery groups in the site with a filter.

    Args:
        filter (str): optional.

    Returns:
        list: A list of delivery groups.
    """
    try:
        customer_id = config.get("configurable", {}).get("customer_id", "")
        user_id = config.get("configurable", {}).get("user_id", "")
        logger.info(f"Getting delivery groups for customer_id: {customer_id}")
        logger.info(f"Getting delivery groups for user_id: {user_id}")
        if not customer_id or not user_id:
            return "customer_id or user_id is not provided in the configuration, please provide both."

        auth_token = await get_token_in_cache(customer_id, user_id)

        if not auth_token or len(auth_token) == 0:
            return "Failed to get the auth token from the cache."

        # customer_id = customer
        # auth_token = bearer_token

        virtual_site_id = await get_site_id(customer_id, auth_token)

        url = f"{os.getenv('WEBSTUDIO_API_ENDPOINT') % customer_id}/{customer_id}/{virtual_site_id}/DeliveryGroupsV2"
        headers = {
            "Authorization": f"Bearer {auth_token}",
        }

        result = await client.get(url, headers=headers)

        if result.status_code == 200:
            delivery_groups = result.json().get("Items", [])
            delivery_groups = [
                {
                    "full_name": group.get("FullName", UNKNOWN),
                    "description": group.get("Description", "N/A"),
                    "is_maintenance_mode": group.get("InMaintenanceMode", False),
                }
                for group in delivery_groups
            ]
            return json.dumps(delivery_groups, ensure_ascii=False)
        else:
            return f"Failed to get delivery groups. Status code: {result.status_code}, Response: {result.text}"
    except Exception as err:
        logger.error(f"Failed to get delivery groups. Error: {err}")
        return f"Failed to get delivery groups. Error: {err}"


async def get_machine_catalogs(config: RunnableConfig) -> str:
    """Get the full list of machine catalogs from the site.

    This tool is designed to retrieve the real machine catalogs from the customers' DDC or site.

    Use this tool when the user wants to:
        - Get the list of machine catalogs in the site.
        - Get the list of machine catalogs in the site with a filter.

    Args:
        filter (str): optional.

    Returns:
        list: A list of machine catalogs.
    """
    try:
        customer_id = config.get("configurable", {}).get("customer_id", "")
        user_id = config.get("configurable", {}).get("user_id", "")
        logger.info(f"Getting delivery groups for customer_id: {customer_id}")
        logger.info(f"Getting delivery groups for user_id: {user_id}")
        if not customer_id or not user_id:
            return "customer_id or user_id is not provided in the configuration, please provide both."

        auth_token = await get_token_in_cache(customer_id, user_id)

        if not auth_token or len(auth_token) == 0:
            return "Failed to get the auth token from the cache."

        virtual_site_id = await get_site_id(customer_id, auth_token)

        url = f"{os.getenv('WEBSTUDIO_API_ENDPOINT') % customer_id}/{customer_id}/{virtual_site_id}/MachineCatalogsV2"
        headers = {
            "Authorization": f"Bearer {auth_token}",
        }

        result = await client.get(url, headers=headers)

        if result.status_code == 200:
            machine_catalogs = result.json().get("Items", [])
            machine_catalogs = [
                {
                    "full_name": catalog.get("Name", UNKNOWN),
                    "description": catalog.get("Description", UNKNOWN),
                    "session_support": catalog.get("SessionSupport", UNKNOWN),
                }
                for catalog in machine_catalogs
            ]
            return json.dumps(machine_catalogs, ensure_ascii=False)
        else:
            return f"Failed to get machine catalogs. Status code: {result.status_code}, Response: {result.text}"
    except Exception as err:
        logger.error(f"Failed to get machine catalogs. Error: {err}")
        return f"Failed to get machine catalogs. Error: {err}"


async def check_ddc_power_state(config: RunnableConfig) -> str:
    """Check the power state of the DDC.

    This tool is designed to check the power state of the DDC.

    Use this tool when the user wants to:
        - Check if the DDC is powered on or off.

    Returns:
        str: The power state of the DDC.
    """
    try:
        customer_id = config.get("configurable", {}).get("customer_id", "")
        user_id = config.get("configurable", {}).get("user_id", "")

        print(f"Checking DDC power state for customer_id: {customer_id}")

        if not customer_id or not user_id:
            return "customer_id or user_id is not provided in the configuration, please provide both."

        # customer_id = customer

        url = f"{os.getenv('WEBSTUDIO_API_ENDPOINT') % customer_id}/ping"

        print(f"Requesting DDC power state from URL: {url}")

        result = await client.get(url)

        if result.status_code == 200:
            response = result.text
            if response == "true":
                return "DDC is powered on."
            else:
                return "DDC is powered off."
        else:
            return f"Failed to check DDC power state. Status code: {result.status_code}, Response: {result.text}"
    except Exception as err:
        logger.error(f"Failed to check DDC power state. Error: {err}")
        return f"Failed to check DDC power state. Error: {err}"


async def restart_vda_machine(config: RunnableConfig, machine_id: str) -> str:
    """Restart the VDA machine with the given machine_id.

    Args:
        machine_id (str): The machine_id of the VDA machine to restart.

    Returns:
        str: A message indicating the success or failure of the restart operation.
    """
    try:
        customer_id = config.get("configurable", {}).get("customer_id", "")
        user_id = config.get("configurable", {}).get("user_id", "")
        if not customer_id or not user_id:
            return "customer_id or user_id is not provided in the configuration, please provide both."

        auth_token = await get_token_in_cache(customer_id, user_id)

        if not auth_token or len(auth_token) == 0:
            return "Failed to get the auth token from the cache."

        cc_url = f"{os.getenv('CC_API_ENDPOINT')}/resourceprovider/{customer_id}/customerrole"
        cc_headers = {
            "Authorization": auth_token_with_prefix("bearer", auth_token),
        }

        response = await client.get(cc_url, headers=cc_headers)
        if response.status_code != 200:
            return f"Failed to get the customer role from CC. Status code: {response.status_code}, Response: {response.text}"

        virtual_site_id = None
        try:
            virtual_site_id = response.json()["VirtualSiteId"]
        except Exception as e:
            return (
                f"Failed to get the virtual site id from the customer role. Error: {e}"
            )

        url = f"{os.getenv('WEBSTUDIO_API_ENDPOINT') % customer_id}/{customer_id}/{virtual_site_id}/Machines/{machine_id}/$reboot?detailResponseRequired=false"
        headers = {
            "Authorization": f"Bearer {auth_token}",
        }
        response = await client.post(url, headers=headers)

        if response.status_code == 200:
            return "Machine restart initiated successfully."
        else:
            return f"Failed to restart machine. Status code: {response.status_code}, Response: {response.text}"
    except Exception as err:
        logger.error(f"Failed to restart the VDA machine. Error: {err}")
        return f"Failed to restart machine. Error: {err}"


async def get_site_id(customerId: str, bearerToken: str) -> str:
    """Get the site id for the given customer id and bearer token."""
    try:
        cc_url = (
            f"{os.getenv('CC_API_ENDPOINT')}/resourceprovider/{customerId}/customerrole"
        )
        cc_headers = {
            "Authorization": auth_token_with_prefix("bearer", bearerToken),
        }

        response = await client.get(cc_url, headers=cc_headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to get the customer role from CC. Status code: {response.status_code}, Response: {response.text}"
            )

        return response.json()["VirtualSiteId"]
    except Exception as err:
        logger.error(f"Failed to get the site id. Error: {err}")
        raise err


SENSITIVE_TOOLS = [restart_vda_machine]
