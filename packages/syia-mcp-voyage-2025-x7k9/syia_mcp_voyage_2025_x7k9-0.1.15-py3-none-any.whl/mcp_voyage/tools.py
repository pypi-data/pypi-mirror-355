from dotenv import load_dotenv
from .databases import *
import json
from typing import Dict, Any, Union, Sequence, Optional
import mcp.types as types
import requests
import logging
from  .tool_schema import tool_definitions
import datetime as dt
from .utils import timestamped_filename
from playwright.async_api import Download
from playwright.async_api import TimeoutError as PwTimeout
from playwright.async_api import async_playwright
import os   
from asyncio import sleep
from pathlib import Path
import time


from .constants import (
    NAVTOR_API_BASE,
    SIYA_API_BASE,
    STORMGLASS_API_BASE,
    NAVTOR_USERNAME,
    NAVTOR_PASSWORD,
    NAVTOR_CLIENT_ID,
    NAVTOR_CLIENT_SECRET,
    SIYA_API_KEY,
    STORMGLASS_API_KEY,
    STORMGLASS_DEFAULT_PARAMS
)
from .constants import LLAMA_API_KEY, VENDOR_MODEL
from . import logger, mcp
from document_parse.main_file_s3_to_llamaparse import parse_to_document_link

from utils.llm import LLMClient
from pymongo import MongoClient
from datetime import datetime, timezone, UTC
import time
import difflib
import requests 
from typing import Dict, Any, List, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import base64
from typing import List, Optional
import re
import requests
from typing import Dict, Any
from .constants import MONGODB_URI, MONGODB_DB_NAME, OPENAI_API_KEY, PERPLEXITY_API_KEY

import httpx

import re
import base64
import pickle
from typing import List, Optional, Dict, Any, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pydantic import EmailStr

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

import os
import requests
import logging


# import for casefile update 
from bson import ObjectId
from .databases import MongoDBClient, TypesenseClient
from .generate_mail_html import MailBodyLinkGenerator
from . import logger
from .html_link_from_md import markdown_to_html_link

server_tools = tool_definitions


# NAVTOR authentication cache
NAVTOR_AUTH = {
    "token": None,
    "expires": 0
}

# Important: Note the capital 'T' in 'Token' which matters for case-sensitive URLs
NAVTOR_TOKEN_URL = f"{NAVTOR_API_BASE}/Token"

# Function to get NAVTOR OAuth token
async def get_navtor_token():
    """
    Get an OAuth token from NAVTOR API
    
    Returns:
        str: Access token
    """
    from time import time
    
    # Check if we have a valid token
    current_time = int(time())
    if NAVTOR_AUTH["token"] and NAVTOR_AUTH["expires"] > current_time + 60:
        logger.info("Using existing NAVTOR token")
        return NAVTOR_AUTH["token"]
    
    # Get a new token
    logger.info("Getting new NAVTOR OAuth token")
    
    # Create form data
    data = {
        "grant_type": "password",
        "username": NAVTOR_USERNAME,
        "password": NAVTOR_PASSWORD,
        "client_id": NAVTOR_CLIENT_ID,
        "client_secret": NAVTOR_CLIENT_SECRET
    }
    
    # Set headers for form data
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        # Make the POST request to the correct Token endpoint
        logger.info(f"Trying NAVTOR auth URL: {NAVTOR_TOKEN_URL}")
        response = requests.post(NAVTOR_TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        
        # Parse response
        auth_data = response.json()
        access_token = auth_data.get("access_token")
        expires_in = auth_data.get("expires_in", 3600)
        
        # Cache the token
        NAVTOR_AUTH["token"] = access_token
        NAVTOR_AUTH["expires"] = current_time + expires_in
        
        logger.info(f"Successfully obtained NAVTOR token")
        return access_token
    except Exception as e:
        logger.error(f"NAVTOR authentication failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response body: {e.response.text}")
        raise NavtorServiceError(f"Authentication failed: {str(e)}")

# API configuration
# These use values from constants.py which come from environment variables
API_CONFIG = {
    "navtor": {
        "base_url": NAVTOR_API_BASE,
    },
    "siya": {
        "base_url": SIYA_API_BASE,
        "api_key": SIYA_API_KEY,
    },
    "stormglass": {
        "base_url": STORMGLASS_API_BASE,
        "api_key": STORMGLASS_API_KEY,
    }
}

# Exception classes
class MissingParameterError(Exception):
    def __init__(self, param, tool_name):
        self.param = param
        self.tool_name = tool_name
        super().__init__(f"Missing required parameter '{param}' for tool '{tool_name}'")


class NavtorServiceError(Exception):
    def __init__(self, message, original_error=None):
        self.original_error = original_error
        super().__init__(message)


class SiyaServiceError(Exception):
    def __init__(self, message, original_error=None):
        self.original_error = original_error
        super().__init__(message)


class StormglassServiceError(Exception):
    def __init__(self, message, original_error=None):
        self.original_error = original_error
        super().__init__(message)


class VesselPositionError(Exception):
    def __init__(self, imo):
        self.imo = imo
        super().__init__(f"Vessel position data not available for IMO {imo}")


class VesselFuelConsumptionError(Exception):
    def __init__(self, imo):
        self.imo = imo
        super().__init__(f"Vessel fuel consumption data not available for IMO {imo}")


class VesselEtaError(Exception):
    def __init__(self, imo):
        self.imo = imo
        super().__init__(f"Vessel ETA data not available for IMO {imo}")


class WeatherDataError(Exception):
    def __init__(self, coordinates, message=None):
        self.coordinates = coordinates
        message = message or f"Weather data not available for coordinates {coordinates}"
        super().__init__(message)


class SearchError(Exception):
    def __init__(self, query, message=None, original_error=None):
        self.query = query
        self.original_error = original_error
        message = message or f"Search failed for query: {query}"
        super().__init__(message)

def convert_voyage_dates(document: dict) -> dict:
    """Convert Unix timestamps to human readable format for voyage date fields."""
    date_fields = [
        'reportdate'
    ]
    
    for field in date_fields:
        if field in document:
            try:
                document[field] = dt.datetime.fromtimestamp(document[field]).strftime('%Y-%m-%d %H:%M:%S')
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to convert {field}: {e}")
    
    return document

# Helper function for making API requests
async def make_api_request(base_url, endpoint, method="GET", data=None, auth_service=None, api_key=None, timeout=30):
    """
    Make an authenticated API request to an external service
    
    Args:
        base_url: Base URL for the API
        endpoint: API endpoint path
        method: HTTP method (GET or POST)
        data: Request data for POST requests
        auth_service: Service name to use for authentication (navtor, siya, stormglass)
        api_key: Optional explicit API key
        timeout: Request timeout in seconds
        
    Returns:
        JSON response from the API
    """
    url = f"{base_url}/{endpoint.lstrip('/')}"
    
    headers = {"Content-Type": "application/json"}
    
    # Add authentication if specified
    if auth_service:
        if auth_service == "navtor":
            # Use OAuth token for NAVTOR
            token = await get_navtor_token()
            headers["Authorization"] = f"Bearer {token}"
        else:
            # Use API key for other services
            service_config = API_CONFIG.get(auth_service, {})
            api_key = api_key or service_config.get("api_key")
            
            if api_key:
                if auth_service == "stormglass":
                    headers["Authorization"] = api_key
                elif auth_service == "siya":
                    # Use Bearer token for SIYA API
                    headers["Authorization"] = f"Bearer {api_key}"
                else:
                    headers["X-API-Key"] = api_key
    
    try:
        logger.info(f"Making {method} request to {url}")
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise e
    except Exception as e:
        logger.error(f"Error processing API response: {e}")
        raise e
    
def get_artifact(function_name: str, url: str):
    """
    Handle get artifact tool using updated artifact format
    """
    artifact = {
        "id": "msg_browser_ghi789",
        "parentTaskId": "task_japan_itinerary_7d8f9g",
        "timestamp": int(time.time()),
        "agent": {
            "id": "agent_siya_browser",
            "name": "SIYA",
            "type": "qna"
        },
        "messageType": "action",
        "action": {
            "tool": "browser",
            "operation": "browsing",
            "params": {
                "url": url,
                "pageTitle": f"Tool response for {function_name}",
                "visual": {
                    "icon": "browser",
                    "color": "#2D8CFF"
                },
                "stream": {
                    "type": "vnc",
                    "streamId": "stream_browser_1",
                    "target": "browser"
                }
            }
        },
        "content": f"Viewed page: {function_name}",
        "artifacts": [
            {
                "id": "artifact_webpage_1746018877304_994",
                "type": "browser_view",
                "content": {
                    "url": url,
                    "title": function_name,
                    "screenshot": "",
                    "textContent": f"Observed output of cmd `{function_name}` executed:",
                    "extractedInfo": {}
                },
                "metadata": {
                    "domainName": "example.com",
                    "visitTimestamp": int(time.time() * 1000),
                    "category": "web_page"
                }
            }
        ],
        "status": "completed"
    }
    return artifact



def get_vessel_qna_snapshot(imo_number: str, question_no: str) -> dict:
    """
    Fetch vessel QnA snapshot data synchronously.
    
    Args:
        imo_number (str): The IMO number of the vessel
        question_no (str): The question number to fetch
        
    Returns:
        dict: The response data from the snapshot API
        
    Raises:
        requests.RequestException: If the API request fails
    """
    # API endpoint
    snapshot_url = f"https://dev-api.siya.com/v1.0/vessel-info/qna-snapshot/{imo_number}/{question_no}"
    
    # Authentication token
    jwt_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiNjRkMzdhMDM1Mjk5YjFlMDQxOTFmOTJhIiwiZmlyc3ROYW1lIjoiU3lpYSIsImxhc3ROYW1lIjoiRGV2IiwiZW1haWwiOiJkZXZAc3lpYS5haSIsInJvbGUiOiJhZG1pbiIsInJvbGVJZCI6IjVmNGUyODFkZDE4MjM0MzY4NDE1ZjViZiIsImlhdCI6MTc0MDgwODg2OH0sImlhdCI6MTc0MDgwODg2OCwiZXhwIjoxNzcyMzQ0ODY4fQ.1grxEO0aO7wfkSNDzpLMHXFYuXjaA1bBguw2SJS9r2M"
    
    # Headers for the request
    headers = {
        "Authorization": jwt_token
    }
    
    try:
        response = requests.get(snapshot_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse and return the JSON response
        data = response.json()
        
        if "resultData" in data:
            return data["resultData"]
        return data
    except requests.RequestException:
        return None
    
def insert_data_link_to_mongodb(data_link: dict, link_header: str, session_id: str, imo: str, vessel_name: str):
    """
    Insert data link into MongoDB collection
    """
    #insert the datalink to mongodb collection casefile_data
    MONGO_URI_dev_syia_api = r'mongodb://dev-syia:m3BFsUxaPTHhE78@13.202.154.63:27017/?authMechanism=DEFAULT&authSource=dev-syia-api'
    DB_NAME_dev_syia_api = 'dev-syia-api'
      
    # Create connection to dev-syia-api database
    client = MongoClient(MONGO_URI_dev_syia_api)
    db = client[DB_NAME_dev_syia_api]

    #insert the datalink to mongodb collection casefile_data
    collection = "casefile_data"
    casefile_data_collection = db[collection]


    #check if sessionId exists in casefile_data collection
    session_exists = casefile_data_collection.find_one({"sessionId": session_id})

    link_data = {"link" : data_link, "linkHeader" : link_header}
    if session_exists:
       #append the data_link to the existing session
       casefile_data_collection.update_one(
          {"sessionId": session_id},
          {"$push": {"links": link_data},
           "$set": {"datetime" : dt.datetime.now(dt.timezone.utc)}}
       )
    else:
       to_insert = {"sessionId": session_id,
                 "imo": imo,
                 "vesselName": vessel_name,
                 "links": [link_data],
                 "datetime" : dt.datetime.now(dt.timezone.utc)}
       casefile_data_collection.insert_one(to_insert)


# Function to search for vessels by name
async def search_vessels_by_name(query):
    """
    Search for vessels by name using Typesense
    
    Args:
        query: Vessel name to search for
        
    Returns:
        Search results with matching vessel names and IMO numbers
    """
    # This would typically use a Typesense client - simplified here
    try:
        # Initialize Typesense client
        client = TypesenseClient()
        
        if not client.enabled:
            logger.warning("Typesense client is not enabled")
            return {"results": [], "found": 0, "error": "Typesense client is not enabled"}
        
        # Check if the vessels collection exists
        try:
            collections = client.collections.retrieve()
            collection_exists = any(c["name"] == "vessels" for c in collections)
            
            if not collection_exists:
                # Create a mock response since collection doesn't exist yet
                logger.warning("Vessels collection does not exist in Typesense")
                return {
                    "found": 0,
                    "results": [],
                    "error": "Vessels collection not initialized"
                }
        except Exception as e:
            logger.warning(f"Failed to check collections: {e}")
            return {"results": [], "found": 0, "error": str(e)}
            
        # Perform the search
        search_parameters = {
            'q': query,
            'query_by': 'vesselName',
            'collection': 'vessels',
            'per_page': 10,
        }
        
        try:
            results = client.collections['vessels'].documents.search(search_parameters)
            return results
        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return {"results": [], "found": 0, "error": str(e)}
            
    except Exception as e:
        logger.error(f"Vessel search error: {e}")
        raise SearchError(query, str(e), e)


# Tool handlers
server_tools = tool_definitions

async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        try:
            # Vessel tools
            if name == "get_vessel_live_position_and_eta":
                return await get_vessel_live_position_and_eta(arguments)
            elif name == "get_vessel_fuel_consumption_rob":
                return await get_vessel_fuel_consumption_rob(arguments)
            elif name == "get_vessel_eta_cargo_activity":
                return await get_vessel_eta_cargo_activity(arguments)
            elif name == "get_vessel_fuel_consumption_history":
                return await get_vessel_fuel_consumption_history(arguments)
            elif name == "get_voyage_details_from_shippalm":
                return await get_voyage_details_from_shippalm(arguments)
            elif name == "get_me_cylinder_oil_consumption_and_rob":
                return await get_me_cylinder_oil_consumption_and_rob(arguments)
            elif name == "get_mecc_aecc_consumption_and_rob":
                return await get_mecc_aecc_consumption_and_rob(arguments)
            elif name == "get_fresh_water_production_consumption_and_rob":
                return await get_fresh_water_production_consumption_and_rob(arguments)
            elif name == "get_charter_party_compliance_status":
                return await get_charter_party_compliance_status(arguments)
            elif name == "get_voyage_casefiles":
                return await get_voyage_casefiles(arguments)
            elif name == "get_laycan_emails":
                return await get_laycan_emails(arguments)
            elif name == "get_itinerary_emails":
                return await get_itinerary_emails(arguments)
            elif name == "get_agent_details_emails":
                return await get_agent_details_emails(arguments)
            elif name == "get_charterer_emails":
                return await get_charterer_emails(arguments)
            elif name == "voyage_table_search":
                return await voyage_table_search(arguments)
            elif name == "get_voyage_table_schema":
                return await get_typesense_schema(arguments)
            # Weather tools
            elif name == "get_live_weather_by_coordinates":
                return await get_live_weather_by_coordinates(arguments)
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            elif name == "google_search":
                return await google_search(arguments)
                
            # Search tools
            elif name == "get_vessel_details":
                return await get_vessel_details(arguments)
                
            # Document Parsing Tool Handlers
            elif name == "parse_document_link":
                return await parse_document_link(arguments)
            
            elif name == "smart_voyage_search":
                return await smart_voyage_search_handler(arguments)
            
            
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            
            elif name == "write_casefile_data":
                return await write_casefile_data(arguments)
            
            elif name == "retrieve_casefile_data":
                if arguments.get("operation") == "get_casefiles":
                    return await getcasefile(arguments)
                elif arguments.get("operation") == "get_casefile_plan":
                    return await get_casefile_plan(arguments)
                else:
                    raise ValueError(f"Error calling tool {name} and  {arguments.get('operation')}: it is not implemented")
            else: 
                raise ValueError(f"Unknown tool: {name}")
            
                
                    
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise ValueError(f"Error calling tool {name}: {str(e)}")

def register_tools():
    @mcp.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return server_tools

    @mcp.call_tool()
    async def mcp_call_tool(tool_name: str, arguments: dict):
        return await handle_call_tool(tool_name, arguments)
    


# ------------------- Vessel Tool Handlers -------------------

async def get_vessel_live_position_and_eta(arguments: dict):
    """
    Retrieves a vessel's current live position and estimated time of arrival
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing vessel position and ETA information as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo:
        raise MissingParameterError("imo", "get_vessel_live_position_and_eta")
    
    try:
        logger.info(f"Retrieving live position for vessel with IMO: {imo}")
        
        # Get authentication token directly
        token = await get_navtor_token()
        
        # Make direct API request to NAVTOR
        endpoint = f"api/v1/vessels/{imo}/reports/status"
        url = f"{NAVTOR_API_BASE}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Making request to: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse response
        vessel_data = response.json()
        
        # Check if response data exists and has necessary fields
        if not vessel_data or not isinstance(vessel_data, dict) or len(vessel_data) == 0:
            raise VesselPositionError(imo)
        
        # Format the results as JSON
        formatted_text = json.dumps(vessel_data, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Live position and ETA for vessel with IMO {imo}",
            format="json"
        )
        
        return [content]
    except VesselPositionError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except NavtorServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with NAVTOR service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to retrieve vessel position for IMO {imo}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]


async def get_vessel_fuel_consumption_rob(arguments: dict):
    """
    Fetches vessel fuel consumption and remaining on board (ROB) data
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing fuel consumption data as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo or (isinstance(imo, str) and imo.strip() == ""):
        raise MissingParameterError("imo", "get_vessel_fuel_consumption_rob")
    
    try:
        parsed_imo = int(imo) if isinstance(imo, str) and imo.isdigit() else imo
        logger.info(f"Fetching fuel consumption data for vessel with IMO: {parsed_imo}")
        
        # Make API request to SIYA
        response = await make_api_request(
            base_url=SIYA_API_BASE,
            endpoint="/v1.0/vessel-info/vessel-app/",
            method="POST",
            data={
                "imo": parsed_imo,
                "qNo": [34]
            },
            auth_service="siya"
        )
        
        # Validate the response
        if not response or not response.get("resultData"):
            raise VesselFuelConsumptionError(str(parsed_imo))
        
        # Format the results as JSON
        formatted_text = json.dumps(response, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Fuel consumption data for vessel with IMO {parsed_imo}",
            format="json"
        )
        
        link = get_vessel_qna_snapshot(parsed_imo, "34")

        artifact_data = get_artifact("get_vessel_fuel_consumption_rob", link)


        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Fuel consumption data for vessel with IMO {parsed_imo}",
            format="json"   
        )

        return [content, artifact]
    except VesselFuelConsumptionError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except MissingParameterError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except SiyaServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with SIYA service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to fetch vessel fuel consumption data for IMO {imo}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]


async def get_vessel_eta_cargo_activity(arguments: dict):
    """
    Fetches vessel ETA and cargo activity information from emails stored in the database
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing ETA data as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo or (isinstance(imo, str) and imo.strip() == ""):
        raise MissingParameterError("imo", "get_vessel_eta_cargo_activity")
    
    try:
        parsed_imo = int(imo) if isinstance(imo, str) and imo.isdigit() else imo
        logger.info(f"Fetching ETA data for vessel with IMO: {parsed_imo}")
        
        # Make API request to SIYA
        response = await make_api_request(
            base_url=SIYA_API_BASE,
            endpoint="/v1.0/vessel-info/vessel-app/",
            method="POST",
            data={
                "imo": parsed_imo,
                "qNo": [32]
            },
            auth_service="siya"
        )
        
        # Validate the response
        if not response or not response.get("resultData"):
            raise VesselEtaError(str(parsed_imo))
        
        # Format the results as JSON
        formatted_text = json.dumps(response, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"ETA data from emails for vessel with IMO {parsed_imo}",
            format="json"
        )

        link = get_vessel_qna_snapshot(parsed_imo, "32")
        artifact_data = get_artifact("get_vessel_eta_cargo_activity", link)

        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"ETA data from emails for vessel with IMO {parsed_imo}",
            format="json"
        )
        return [content, artifact]
    except VesselEtaError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except MissingParameterError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except SiyaServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with SIYA service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to fetch vessel ETA data for IMO {imo}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]

async def get_voyage_details_from_shippalm(arguments: dict):
    """
    Fetches latest voyage details for a vessel from the pre-computed database via the SIYA API.
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing voyage data as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo or (isinstance(imo, str) and imo.strip() == ""):
        raise MissingParameterError("imo", "get_voyage_details_from_shippalm")
    
    try:
        parsed_imo = int(imo) if isinstance(imo, str) and imo.isdigit() else imo
        logger.info(f"Fetching voyage details for vessel with IMO: {parsed_imo}")
        
        # Make API request to SIYA
        response = await make_api_request(
            base_url=SIYA_API_BASE,
            endpoint="/v1.0/vessel-info/vessel-app/",
            method="POST",
            data={
                "imo": parsed_imo,
                "qNo": [31]
            },
            auth_service="siya"
        )
        
        # Validate the response
        if not response or not response.get("resultData"):
            raise ValueError(f"No voyage details found for IMO {parsed_imo}")
        
        # Format the results as JSON
        formatted_text = json.dumps(response, indent=2, default=str)

        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Voyage details from Shippalm for vessel with IMO {parsed_imo}",
            format="json"
        )

        link = get_vessel_qna_snapshot(parsed_imo, "31")
        artifact_data = get_artifact("get_voyage_details_from_shippalm", link)

        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Voyage details from Shippalm for vessel with IMO {parsed_imo}",
            format="json"
        )
        
        return [content, artifact]
    except MissingParameterError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except SiyaServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with SIYA service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to fetch voyage details for IMO {imo}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]

async def get_me_cylinder_oil_consumption_and_rob(arguments: dict):
    """
    Fetches the most recent main-engine cylinder-lubricating-oil consumption and ROB data for a vessel
    from the pre-computed database via the SIYA API.
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing cylinder oil data as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo or (isinstance(imo, str) and imo.strip() == ""):
        raise MissingParameterError("imo", "get_me_cylinder_oil_consumption_and_rob")
    
    try:
        parsed_imo = int(imo) if isinstance(imo, str) and imo.isdigit() else imo
        logger.info(f"Fetching ME cylinder oil data for vessel with IMO: {parsed_imo}")
        
        # Make API request to SIYA
        response = await make_api_request(
            base_url=SIYA_API_BASE,
            endpoint="/v1.0/vessel-info/vessel-app/",
            method="POST",
            data={
                "imo": parsed_imo,
                "qNo": [35]
            },
            auth_service="siya"
        )
        
        # Validate the response
        if not response or not response.get("resultData"):
            raise ValueError(f"No ME cylinder oil data found for IMO {parsed_imo}")
        
        # Format the results as JSON
        formatted_text = json.dumps(response, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"ME cylinder oil consumption and ROB for vessel with IMO {parsed_imo}",
            format="json"
        )
        
        link = get_vessel_qna_snapshot(parsed_imo, "35")

        artifact_data = get_artifact("get_me_cylinder_oil_consumption_and_rob", link)

        artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"ME cylinder oil consumption and ROB for vessel with IMO {parsed_imo}",
          format="json"     
      )

    

        return [content, artifact]
    except MissingParameterError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except SiyaServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with SIYA service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to fetch ME cylinder oil data for IMO {imo}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]

async def get_mecc_aecc_consumption_and_rob(arguments: dict):
    """
    Fetches the most recent MECC and AECC lubricating-oil consumption and ROB data for a vessel
    from the pre-computed database via the SIYA API.
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing MECC and AECC oil data as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo or (isinstance(imo, str) and imo.strip() == ""):
        raise MissingParameterError("imo", "get_mecc_aecc_consumption_and_rob")
    
    try:
        parsed_imo = int(imo) if isinstance(imo, str) and imo.isdigit() else imo
        logger.info(f"Fetching MECC/AECC oil data for vessel with IMO: {parsed_imo}")
        
        # Make API request to SIYA
        response = await make_api_request(
            base_url=SIYA_API_BASE,
            endpoint="/v1.0/vessel-info/vessel-app/",
            method="POST",
            data={
                "imo": parsed_imo,
                "qNo": [36]
            },
            auth_service="siya"
        )
        
        # Validate the response
        if not response or not response.get("resultData"):
            raise ValueError(f"No MECC/AECC oil data found for IMO {parsed_imo}")
        
        # Format the results as JSON
        formatted_text = json.dumps(response, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"MECC and AECC oil consumption and ROB for vessel with IMO {parsed_imo}",
            format="json"
        )

        link = get_vessel_qna_snapshot(parsed_imo, "36")
        artifact_data = get_artifact("get_mecc_aecc_consumption_and_rob", link)

        artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"MECC and AECC oil consumption and ROB for vessel with IMO {parsed_imo}",
          format="json"     
      )

        return [content, artifact]
    
    except MissingParameterError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except SiyaServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with SIYA service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to fetch MECC/AECC oil data for IMO {imo}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]

async def get_fresh_water_production_consumption_and_rob(arguments: dict):
    """
    Fetches the most recent fresh-water production, consumption, and ROB data for a vessel
    from the pre-computed database via the SIYA API.
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing fresh-water statistics as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo or (isinstance(imo, str) and imo.strip() == ""):
        raise MissingParameterError("imo", "get_fresh_water_production_consumption_and_rob")
    
    try:
        parsed_imo = int(imo) if isinstance(imo, str) and imo.isdigit() else imo
        logger.info(f"Fetching fresh-water data for vessel with IMO: {parsed_imo}")
        
        # Make API request to SIYA
        response = await make_api_request(
            base_url=SIYA_API_BASE,
            endpoint="/v1.0/vessel-info/vessel-app/",
            method="POST",
            data={
                "imo": parsed_imo,
                "qNo": [37]
            },
            auth_service="siya"
        )
        
        # Validate the response
        if not response or not response.get("resultData"):
            raise ValueError(f"No fresh-water data found for IMO {parsed_imo}")
        
        # Format the results as JSON
        formatted_text = json.dumps(response, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Fresh-water production, consumption, and ROB for vessel with IMO {parsed_imo}",
            format="json"
        )
        
        link = get_vessel_qna_snapshot(parsed_imo, "37")
        artifact_data = get_artifact("get_fresh_water_production_consumption_and_rob", link)

        artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Fresh-water production, consumption, and ROB for vessel with IMO {parsed_imo}",
          format="json"     
      )


        return [content, artifact]
    except MissingParameterError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except SiyaServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with SIYA service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to fetch fresh-water data for IMO {imo}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]
    
async def get_charter_party_compliance_status(arguments: dict):
    """
    Fetches the latest charter-party compliance status for a vessel
    from the pre-computed database via the SIYA API.
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing charter-party compliance status as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo or (isinstance(imo, str) and imo.strip() == ""):
        raise MissingParameterError("imo", "get_charter_party_compliance_status")
    
    try:
        parsed_imo = int(imo) if isinstance(imo, str) and imo.isdigit() else imo
        logger.info(f"Fetching charter-party compliance status for vessel with IMO: {parsed_imo}")
        
        # Make API request to SIYA
        response = await make_api_request(
            base_url=SIYA_API_BASE,
            endpoint="/v1.0/vessel-info/vessel-app/",
            method="POST",
            data={
                "imo": parsed_imo,
                "qNo": [33]
            },
            auth_service="siya"
        )
        
        # Validate the response
        if not response or not response.get("resultData"):
            raise ValueError(f"No charter-party compliance status found for IMO {parsed_imo}")
        
        # Format the results as JSON
        formatted_text = json.dumps(response, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Charter-party compliance status for vessel with IMO {parsed_imo}",
            format="json"
        )
        
        link = get_vessel_qna_snapshot(parsed_imo, "33")
        artifact_data = get_artifact("get_charter_party_compliance_status", link)

        artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Charter-party compliance status for vessel with IMO {parsed_imo}",
          format="json"     
      )

        return [content, artifact]
    
    except MissingParameterError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except SiyaServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with SIYA service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to fetch charter-party compliance status for IMO {imo}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]
    
def convert_casefile_dates(document: dict) -> dict:
    """Convert Unix timestamps to human readable format for email casefile date fields."""
    date_fields = [
        'casefileInitiationDate',
        'lastCasefileUpdateDate'
    ]
    
    for field in date_fields:
        if field in document:
            try:
                document[field] = dt.datetime.fromtimestamp(document[field]).strftime('%Y-%m-%d %H:%M:%S')
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to convert {field}: {e}")
    
    return document

def get_list_of_artifacts(function_name: str, results: list):
    """
    Handle get artifact tool using updated artifact format
    """
    artifacts = []
    for i, result in enumerate(results):
        url = result.get("url")
        casefile = result.get("title")
        if url:
            artifact_data = {
                "id": f"msg_browser_ghi789{i}",
                "parentTaskId": "task_japan_itinerary_7d8f9g",
                "timestamp": int(time.time()),
                "agent": {
                    "id": "agent_siya_browser",
                    "name": "SIYA",
                    "type": "qna"
                },
                "messageType": "action",
                "action": {
                    "tool": "browser",
                    "operation": "browsing",
                    "params": {
                        "url": f"Casefile: {casefile}",
                        "pageTitle": f"Tool response for {function_name}",
                        "visual": {
                            "icon": "browser",
                            "color": "#2D8CFF"
                        },
                        "stream": {
                            "type": "vnc",
                            "streamId": "stream_browser_1",
                            "target": "browser"
                        }
                    }
                },
                "content": f"Viewed page: {function_name}",
                "artifacts": [{
                        "id": "artifact_webpage_1746018877304_994",
                        "type": "browser_view",
                        "content": {
                            "url": url,
                            "title": function_name,
                            "screenshot": "",
                            "textContent": f"Observed output of cmd `{function_name}` executed:",
                            "extractedInfo": {}
                        },
                        "metadata": {
                            "domainName": "example.com",
                            "visitTimestamp": int(time.time() * 1000),
                            "category": "web_page"
                        }
                    }],
                "status": "completed"
            }
            artifact = types.TextContent(
                type="text",
                text=json.dumps(artifact_data, indent=2, default=str),
                title=f"Casefile: {casefile}",
                format="json"
            ) 
            artifacts.append(artifact)
    return artifacts

async def get_voyage_casefiles(arguments: dict):
    """
    Handle get_voyage_casefiles tool.

    Args:
        arguments: Tool arguments including IMO number, lookback_hours, query_keyword, and optionally per_page.

    Returns:
        List containing the records as TextContent.
    """
    imo = arguments.get("imo")
    lookback_hours = arguments.get("lookback_hours")
    query_keyword = arguments.get("query_keyword", "voyage")
    per_page = arguments.get("per_page", 10)
    include_fields = "vesselName,lastCasefileUpdateDate,subject,importance,casefile,narrative,senderEmailAddress,toRecipientsEmailAddresses,imo,link"

    if not imo or not lookback_hours or not query_keyword:
        raise ValueError("IMO number, lookback_hours, and query_keyword are required")
    
    try:
        # Parse and compute timestamp threshold
        lookback_hours = int(lookback_hours)
        cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=lookback_hours)
        cutoff_ts = int(cutoff_date.timestamp())

        collection = "caseFiles"
        

        query = {
            "q": query_keyword,
            "query_by": "embedding",
            "filter_by": f"imo:{imo} && lastCasefileUpdateDate:>{cutoff_ts}",
            "per_page": per_page,
            "sort_by": "lastCasefileUpdateDate:desc",
            "include_fields": include_fields,
            "prefix": False
        }

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []
        link_data = []

        for hit in hits:
            document = hit.get('document', {})
            document.pop('embedding', None)
            # Convert date fields to human readable format
            document = convert_casefile_dates(document)
            filtered_hits.append({
                "id": document.get("id"),
                "score": hit.get("text_match", 0),
                "document": document
            })
            link_data.append({
                "title": document.get("casefile"),
                "url": document.get("link", None)
            })

        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }

        formatted_text = json.dumps(formatted_results, indent=2)
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Search results for '{collection}'",
            format="json"
        )

        artifacts = get_list_of_artifacts("get_voyage_casefiles", link_data)
        
        return [content] + artifacts

    except Exception as e:
        logger.error(f"Error searching collection {collection}: {e}")
        raise ValueError(f"Error searching collection: {str(e)}")
    

async def get_laycan_emails(arguments: dict):
    """
    Handle get laycan emails tool.

    Args:
        arguments: Tool arguments including IMO number, tag (must be 'Laycan'), and optionally lookbackHours and per_page.

    Returns:
        List containing the laycan-tagged emails as TextContent.
    """
    imo = arguments.get("imo")
    tag = arguments.get("tag")
    lookback_hours = arguments.get("lookbackHours", 24)  # Default to 24 hours if not provided
    per_page = arguments.get("per_page", 10)  # Default per schema
    include_fields = (
            "vesselName,dateTime,subject,importance,casefile,narrative,"
            "senderEmailAddress,toRecipientsEmailAddresses,imo,tags"
        )

    if not imo or not tag:
        raise ValueError("IMO number and tag are required")
    try:
        start_utc = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=lookback_hours)
        start_ts = int(start_utc.timestamp())*1000
        collection = "diary_mails"

        query = {
            "q": "*",
            "filter_by": f"imo:{imo} && dateTime:>{start_ts} && tags:=[\"{tag}\"]",
            "per_page": per_page,
            "include_fields": include_fields,
            "sort_by": "dateTime:desc",
            "prefix": False
        }

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get("document", {})
            document.pop("embedding", None)
            document["dateTime"] = dt.datetime.fromtimestamp(
                document["dateTime"] / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")
            filtered_hits.append({
                "id": document.get("id"),
                "score": hit.get("text_match", 0),
                "document": document
            })

        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }

        formatted_text = json.dumps(formatted_results, indent=2)

        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"{tag}-tagged emails for vessel {imo} in the last {lookback_hours} hours",
            format="json"
        )
        return [content]

    except Exception as e:
        logger.error(f"Error retrieving laycan emails for {imo}: {e}")
        raise ValueError(f"Error retrieving laycan emails: {str(e)}")

async def get_itinerary_emails(arguments: dict):
    """
    Handle get_itinerary_emails tool.

    Args:
        arguments: Tool arguments including IMO number, tag (Itinerary or LocationAndCargoActivityMail),
                   optional lookbackHours, and per_page.

    Returns:
        List containing the filtered emails as TextContent.
    """

    imo = arguments.get("imo")
    tag = arguments.get("tag")
    lookback_hours = arguments.get("lookbackHours", 24)
    per_page = arguments.get("per_page", 10)
    include_fields = (
            "vesselName,dateTime,subject,importance,casefile,narrative,"
            "senderEmailAddress,toRecipientsEmailAddresses,imo,tags"
        )

    if not imo or not tag:
        raise ValueError("IMO number and tag are required")
    try:
        # Compute lookback time
        start_utc = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=int(lookback_hours))
        start_ts = int(start_utc.timestamp()) * 1000

        collection = "diary_mails"

        query = {
            "q": "*",
            "filter_by": f"imo:{imo} && dateTime:>{start_ts} && tags:=[\"{tag}\"]",
            "per_page": per_page,
            "include_fields": include_fields,
            "sort_by": "dateTime:desc",
            "prefix": False
        }

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get("document", {})
            document.pop("embedding", None)
            document["dateTime"] = dt.datetime.fromtimestamp(
                document["dateTime"] / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")
            filtered_hits.append({
                "id": document.get("id"),
                "score": hit.get("text_match", 0),
                "document": document
            })

        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }

        formatted_text = json.dumps(formatted_results, indent=2)

        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"{tag}-tagged emails for vessel {imo} in the last {lookback_hours} hours",
            format="json"
        )
        return [content]

    except Exception as e:
        logger.error(f"Error retrieving {tag} emails for {imo}: {e}")
        raise ValueError(f"Error retrieving {tag} emails: {str(e)}")
    
async def get_agent_details_emails(arguments: dict):
    """
    Handle get_agent_details_emails tool.

    Args:
        arguments: Tool arguments including IMO number, tag (agent),
                   optional lookbackHours, and per_page.

    Returns:
        List containing the filtered emails as TextContent.
    """

    imo = arguments.get("imo")
    tag = arguments.get("tag")
    lookback_hours = arguments.get("lookbackHours", 24)
    per_page = arguments.get("per_page", 10)
    include_fields = (
            "vesselName,dateTime,subject,importance,casefile,narrative,"
            "senderEmailAddress,toRecipientsEmailAddresses,imo,tags"
        )

    if not imo or not tag:
        raise ValueError("IMO number and tag are required")
    try:
        # Compute lookback time
        start_utc = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=int(lookback_hours))
        start_ts = int(start_utc.timestamp()) * 1000

        collection = "diary_mails"

        query = {
            "q": "*",
            "filter_by": f"imo:{imo} && dateTime:>{start_ts} && tags:=[\"{tag}\"]",
            "per_page": per_page,
            "include_fields": include_fields,
            "sort_by": "dateTime:desc",
            "prefix": False
        }

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get("document", {})
            document.pop("embedding", None)
            document["dateTime"] = dt.datetime.fromtimestamp(
                document["dateTime"] / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")
            filtered_hits.append({
                "id": document.get("id"),
                "score": hit.get("text_match", 0),
                "document": document
            })

        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }

        formatted_text = json.dumps(formatted_results, indent=2)

        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"{tag}-tagged emails for vessel {imo} in the last {lookback_hours} hours",
            format="json"
        )
        return [content]

    except Exception as e:
        logger.error(f"Error retrieving {tag} emails for {imo}: {e}")
        raise ValueError(f"Error retrieving {tag} emails: {str(e)}")
    

async def get_charterer_emails(arguments: dict):
    """
    Handle get charterer emails tool
    
    Args:
        arguments: Tool arguments including IMO number and lookback hours       
    Returns:
        List containing the purchase emails as TextContent
    """

    imo = arguments.get("imo")
    lookbackHours = arguments.get("lookbackHours")
    per_page = arguments.get("per_page", 50)  # Changed default to 50 to match the example URL
    include_fields = "vesselName,dateTime,subject,importance,casefile,narrative,senderEmailAddress,toRecipientsEmailAddresses,im,tags"
    tag = arguments.get("tag")

    if not imo or not tag:
        raise ValueError("IMO number and tag are required")
    
    try:
        # Compute timestamp threshold
        start_utc = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=int(lookbackHours))
        start_ts = int(start_utc.timestamp()) * 1000

        collection = "diary_mails"

        query = {
            "q": "*",
            "filter_by": f"imo:{imo} && dateTime:>{start_ts} && tags:=[\"{tag}\"]",
            "per_page": per_page,
            "include_fields": include_fields,
            "sort_by": "dateTime:desc",
            "prefix": False
        }

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get("document", {})
            document.pop("embedding", None)
            document["dateTime"] = dt.datetime.fromtimestamp(
                document["dateTime"] / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")
            filtered_hits.append({
                "id": document.get("id"),
                "score": hit.get("text_match", 0),
                "document": document
            })

        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }

        formatted_text = json.dumps(formatted_results, indent=2)

        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"{tag}-tagged emails for vessel {imo} in the last {lookbackHours} hours",
            format="json"
        )

        return [content]

    except Exception as e:
        logger.error(f"Error retrieving Charter emails for {imo}: {e}")
        raise ValueError(f"Error retrieving Charter emails: {str(e)}")
    
def get_data_link(data):
    url = "https://dev-api.siya.com/v1.0/vessel-info/qna-snapshot"
    headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiNjRkMzdhMDM1Mjk5YjFlMDQxOTFmOTJhIiwiZmlyc3ROYW1lIjoiU3lpYSIsImxhc3ROYW1lIjoiRGV2IiwiZW1haWwiOiJkZXZAc3lpYS5haSIsInJvbGUiOiJhZG1pbiIsInJvbGVJZCI6IjVmNGUyODFkZDE4MjM0MzY4NDE1ZjViZiIsImlhdCI6MTc0MDgwODg2OH0sImlhdCI6MTc0MDgwODg2OCwiZXhwIjoxNzcyMzQ0ODY4fQ.1grxEO0aO7wfkSNDzpLMHXFYuXjaA1bBguw2SJS9r2M"
    }
    payload = {
    "data": data
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.json()['status'] == "OK":
        return response.json()['resultData']
    else:
        return None

async def voyage_table_search(arguments: dict):
    """
    Handle Typesense query tool.

    Args:
        arguments: Tool arguments including collection and query parameters.

    Returns:
        List containing the search results as TextContent.
    """
    collection = arguments.get("collection")
    query = arguments.get("query", {})
    
    if not collection:
        raise ValueError("Missing required parameter: 'collection'.")

    # Validate required query fields
    required_query_fields = ["q", "query_by"]
    for field in required_query_fields:
        if field not in query or not query[field]:
            raise ValueError(f"Missing required query field: '{field}'.")

    try:
        client = TypesenseClient()

        logger.debug(f"Querying Typesense collection '{collection}' with: {query}")
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        formatted_hits = []

        for hit in hits:
            document = hit.get("document", {})
            # Remove embedding field to reduce response size
            document.pop('embedding', None)
            # Convert date fields to human readable format
            if collection == "voyage":
                document = convert_voyage_dates(document)
            formatted_hits.append(document)

        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": formatted_hits
        }

        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Search results for '{collection}'",
            format="json"
        )
        link = get_data_link(formatted_hits)
        artifact_data = get_artifact("voyage_table_search", link)

        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Search results for '{collection}'",
            format="json"
        )
        return [content, artifact]

    except Exception as e:
        logger.error(f"Error searching collection '{collection}': {e}")
        raise ValueError(f"Typesense query failed: {str(e)}")


async def get_typesense_schema(arguments: dict):
    """
    Handle get typesense schema tool
    
    Args:
        arguments: Tool arguments including category

    Returns:
        List containing the schema as TextContent
    """
    category = arguments.get("category")
    if not category:
        raise ValueError("Category is required")

    try:
        # Execute the query
        collection = "typesense_schema"
        query = {"category": category}
        projection = {"_id": 0, "schema": 1, "category": 1}

        mongo_client = MongoDBClient()
        db = mongo_client.db
        collection = db[collection]
        cursor = collection.find(query, projection=projection)
        documents = [doc async for doc in cursor]

        # Format the results
        formatted_results = {
            "count": len(documents),
            "documents": documents
        }
        
        # Convert the results to JSON string using custom encoder
        formatted_text = json.dumps(formatted_results, indent=2)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Query results from '{collection}'",
            format="json"
        )
        
        return [content]
    except Exception as e:
        logger.error(f"Error querying collection {collection}: {e}")
        raise ValueError(f"Error querying collection: {str(e)}")
    


    





# ------------------- Weather Tool Handlers -------------------

async def get_live_weather_by_coordinates(arguments: dict):
    """
    Fetches live weather data for specific coordinates
    
    Args:
        arguments: Tool arguments including latitude, longitude, and timestamp
        
    Returns:
        List containing weather data as TextContent
    """
    latitude = arguments.get("latitude")
    longitude = arguments.get("longitude")
    timestamp = arguments.get("timestamp")
    
    if not latitude:
        raise MissingParameterError("latitude", "get_live_weather_by_coordinates")
    
    if not longitude:
        raise MissingParameterError("longitude", "get_live_weather_by_coordinates")
    
    if not timestamp:
        raise MissingParameterError("timestamp", "get_live_weather_by_coordinates")
    
    try:
        # Convert to appropriate types
        parsed_lat = float(latitude) if isinstance(latitude, str) and latitude else latitude
        parsed_lng = float(longitude) if isinstance(longitude, str) and longitude else longitude
        parsed_time = timestamp
        
        logger.info(f"Retrieving weather data for coordinates: lat={parsed_lat}, lng={parsed_lng}, time={parsed_time}")
        
        # Adjust the date format if needed - Stormglass expects ISO format for start/end
        from datetime import datetime
        try:
            # Try to parse if it's not already in ISO format
            if "T" not in parsed_time and not parsed_time.endswith("Z"):
                dt = datetime.fromisoformat(parsed_time)
                parsed_time = dt.isoformat()
        except:
            # If parsing fails, keep original format
            pass
            
        # Prepare the API request with params properly formatted
        params = STORMGLASS_DEFAULT_PARAMS
        params_str = ",".join(params)
        
        # Make API request to Stormglass
        endpoint = f"weather/point?lat={parsed_lat}&lng={parsed_lng}&params={params_str}&start={parsed_time}&end={parsed_time}"
        response = await make_api_request(
            base_url=STORMGLASS_API_BASE,
            endpoint=endpoint,
            method="GET",
            auth_service="stormglass"
        )
        
        # Check if response data exists and has necessary fields
        if not response or not response.get("hours") or len(response.get("hours", [])) == 0:
            raise WeatherDataError(
                f"{parsed_lat},{parsed_lng}",
                f"No weather data available for coordinates ({parsed_lat}, {parsed_lng}) at time {parsed_time}"
            )
        
        # Format the results as JSON
        formatted_text = json.dumps(response, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Weather conditions at coordinates ({parsed_lat}, {parsed_lng})",
            format="json"
        )
        
        return [content]
    except WeatherDataError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except MissingParameterError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    except StormglassServiceError as e:
        return [types.TextContent(
            type="text",
            text=f"Error with Stormglass service: {str(e)}"
        )]
    except Exception as e:
        error_msg = f"Failed to retrieve weather data for coordinates ({parsed_lat}, {parsed_lng}): {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=f"Error: {error_msg}"
        )]


# ------------------- Search Tool Handlers -------------------

async def imo_search(arguments: dict):
    """
    Lookup up to 4 vessels by name in the 'fleet-vessel-lookup' Typesense collection,
    returning only vesselName and IMO for each hit.
    
    Args:
        arguments: Tool arguments including vessel name query
        
    Returns:
        List containing vessel IMO information as TextContent
    """
    query = arguments.get("query")
    
    if not query:
        return [types.TextContent(
            type="text", 
            text="Error: 'query' parameter is required for IMO search"
        )]
    
    try:
        logger.info(f"Searching for IMO numbers with vessel name: {query}")
        
        # Set up search parameters for the fleet-vessel-lookup collection
        search_parameters = {
            'q': query,
            'query_by': 'vesselName',
            'collection': 'fleet-vessel-lookup',
            'per_page': 4,
            'include_fields': 'vesselName,imo',
            'prefix': False,
            'num_typos': 2,
        }
        
        # Execute search
        client = TypesenseClient()
        raw = client.collections['fleet-vessel-lookup'].documents.search(search_parameters)
        hits = raw.get('hits', [])
        
        if not hits:
            return [types.TextContent(
                type="text",
                text=f"No vessels found named '{query}'."
            )]
        
        # Process and format results
        results = []
        for hit in hits:
            doc = hit.get('document', {})
            results.append({
                'vesselName': doc.get('vesselName'),
                'imo': doc.get('imo'),
                'score': hit.get('text_match', 0)
            })
        
        response = {
            'found': len(results),
            'results': results
        }
        
        # Return formatted response
        content = types.TextContent(
            type="text",
            text=json.dumps(response, indent=2),
            title=f"IMO search results for '{query}'",
            format="json"
        )
        
        return [content]
    except Exception as e:
        logger.error(f"Error searching for vessel IMO: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error querying vessels: {str(e)}"
        )]
    
async def get_vessel_details(arguments: dict):
    """
    Lookup vessel details by name in the 'fleet-vessel-lookup' Typesense collection,
    returning vessel name, IMO, class, flag, DOC, and V3 status.
    
    Args:
        arguments: Tool arguments including vessel name query
        
    Returns:
        List containing vessel details as TextContent
    """
    query = arguments.get("query")
      
    if not query:
        return [types.TextContent(
            type="text",
            text="Error: 'query' parameter is required for vessel details search"
        )]
   
    try:
        logger.info(f"Searching for vessel details with vessel name: {query}")
      
        # Set up search parameters for the fleet-vessel-lookup collection
        search_parameters = {
            'q': query,
            'query_by': 'vesselName',
            'collection': 'fleet-vessel-lookup',
            'per_page': 1,
            'include_fields': 'vesselName,imo,class,flag,shippalmDoc,isV3',
            'prefix': False,
            'num_typos': 2,
        }
      
        # Execute search
        client = TypesenseClient()
        raw = client.collections['fleet-vessel-lookup'].documents.search(search_parameters)
        hits = raw.get('hits', [])
      
        if not hits:
            return [types.TextContent(
                type="text",
                text=f"No vessels found named '{query}'."
            )]
      
        # Process and format results
        doc = hits[0].get('document', {})
        results = {
            'vesselName': doc.get('vesselName'),
            'imo': doc.get('imo'),
            'class': doc.get('class'),
            'flag': doc.get('flag'),
            'shippalmDoc': doc.get('shippalmDoc'),
            'isV3': doc.get('isV3'),
            'score': hits[0].get('text_match', 0)
        }
      
        # Return formatted response
        content = types.TextContent(
            type="text",
            text=json.dumps(results, indent=2),
            title=f"Vessel details for '{query}'",
            format="json"
        )
      
        return [content]
    except Exception as e:
        logger.error(f"Error searching for vessel details: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error querying vessel details: {str(e)}"
        )]


async def parse_document_link(arguments: dict, llama_api_key = LLAMA_API_KEY, vendor_model = VENDOR_MODEL):
    """
    Parse a document from a URL using LlamaParse and return the parsed content.
    
    Args:
        arguments: Dictionary containing the URL of the document to parse
        
    Returns:
        List containing the parsed content as TextContent
    """
    url = arguments.get("document_link")
    if not url:
        raise ValueError("URL is required")
    
    try:
        # Call the parse_to_document_link function to process the document
        success, md_content = parse_to_document_link(
            document_link=url,
            llama_api_key=llama_api_key,
            vendor_model=vendor_model
        )
        
        if not success or not md_content:
            return [types.TextContent(
                type="text",
                text=f"Failed to parse document from URL: {url}",
                title="Document Parsing Error"
            )]
        
        # Return the parsed content as TextContent
        return [types.TextContent(
            type="text",
            text=str(md_content),
            title=f"Parsed document from {url}",
            format="markdown"
        )]
    except ValueError as ve:
        # Handle specific ValueErrors that might be raised due to missing API keys
        error_message = str(ve)
        if "API_KEY is required" in error_message:
            logger.error(f"API key configuration error: {error_message}")
            return [types.TextContent(
                type="text",
                text=f"API configuration error: {error_message}",
                title="API Configuration Error"
            )]
        else:
            logger.error(f"Value error when parsing document from URL {url}: {ve}")
            return [types.TextContent(
                type="text",
                text=f"Error parsing document: {str(ve)}",
                title="Document Parsing Error"
            )]
    except Exception as e:
        logger.error(f"Error parsing document from URL {url}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error parsing document: {str(e)}",
            title="Document Parsing Error"
        )] 

async def smart_voyage_search_handler(arguments: dict):
    """
    Handle smart voyage search tool.

    Args:
        arguments: Tool arguments following the smart_voyage_search schema.

    Returns:
        List containing the results and artifacts as TextContent.
    """
    collection = "voyage"
    session_id = arguments.get("session_id", "testing")
    query_text = arguments.get("query", "").strip() or "*"
    filters = arguments.get("filters", {})
    sort_by = arguments.get("sort_by", "relevance")
    sort_order = arguments.get("sort_order", "desc")
    max_results = arguments.get("max_results", 10)

    try:
        # Compose `filter_by` string from filters
        filter_parts = []

        if filters:
            for key, value in filters.items():
                if key == "reportdate_range" and isinstance(value, dict):
                    start_date = value.get("start_date")
                    end_date = value.get("end_date")
                    
                    if start_date:
                        # Convert to Unix timestamp if it's not already
                        if isinstance(start_date, str):
                            try:
                                dt_obj = dt.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                                start_ts = int(dt_obj.timestamp())
                                filter_parts.append(f"reportdate:>={start_ts}")
                            except ValueError:
                                logger.warning(f"Invalid start_date format: {start_date}")
                        else:
                            filter_parts.append(f"reportdate:>={start_date}")
                    
                    if end_date:
                        # Convert to Unix timestamp if it's not already
                        if isinstance(end_date, str):
                            try:
                                dt_obj = dt.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                                end_ts = int(dt_obj.timestamp())
                                filter_parts.append(f"reportdate:<={end_ts}")
                            except ValueError:
                                logger.warning(f"Invalid end_date format: {end_date}")
                        else:
                            filter_parts.append(f"reportdate:<={end_date}")
                
                elif key == "steamingTime_range" and isinstance(value, dict):
                    min_hours = value.get("min_hours")
                    max_hours = value.get("max_hours")
                    
                    if min_hours is not None:
                        filter_parts.append(f"steamingTime:>={min_hours}")
                    
                    if max_hours is not None:
                        filter_parts.append(f"steamingTime:<={max_hours}")
                
                elif value is not None:
                    filter_parts.append(f"{key}:={value}")

        filter_by = " && ".join(filter_parts) if filter_parts else ""

        # Prepare query parameters
        query_by = "vesselName,event,eventtype,fromport,toport,location,vesselActivity,vesselstatus,headcharterer"
        
        # Exclude fields to reduce response size
        exclude_fields = "vesselId,docId,fleetId,fleetManagerId,technicalSuperintendentId,_id,ownerId"
        
        query = {
            "q": query_text,
            "query_by": query_by,
            "per_page": max_results,
            "exclude_fields": exclude_fields
        }
        
        if filter_by:
            query["filter_by"] = filter_by

        # Apply sorting if not relevance
        if sort_by != "relevance":
            sort_direction = "" if sort_order == "asc" else ":desc"
            query["sort_by"] = f"{sort_by}{sort_direction}"

        # Execute the search
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        # Process results
        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get('document', {})
            document = convert_voyage_dates(document)  # Convert Unix timestamps to readable dates
            filtered_hits.append({
                "id": document.get("id"),
                "score": hit.get("text_match", 0),
                "document": document
            })

        # Format the results
        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }

        # Create the response
        formatted_text = json.dumps(formatted_results, indent=2)
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Voyage search results for '{query_text}'",
            format="json"
        )

        # Generate artifact for visualization if there are results
        if filtered_hits:
            link = get_data_link([doc["document"] for doc in filtered_hits])
            artifact_data = get_artifact("smart_voyage_search", link)
            
            artifact = types.TextContent(
                type="text",
                text=json.dumps(artifact_data, indent=2, default=str),
                title=f"Voyage search results for '{query_text}'",
                format="json"
            )
            
            return [content, artifact]
        
        return [content]

    except Exception as e:
        logger.error(f"Error in smart_voyage_search_handler: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error searching voyage data: {str(e)}",
            title="Voyage Search Error"
        )]
    

async def get_vessel_fuel_consumption_history(arguments: dict):
    """
    Handle get vessel fuel consumption history tool
    """
    imo = arguments.get("imo")
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    session_id = arguments.get("session_id","testing")

    if not imo:
        raise ValueError("IMO number is required")

    try:
        # Convert start_date and end_date to datetime if provided
        if start_date:
            start_date = dt.datetime.strptime(start_date, "%Y-%m-%d")
        
        if end_date:
            end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")
        
        mongo_uri = r'mongodb://syia-etl-dev-readonly:S42tH5iVm3H8@db.syia.ai/?authMechanism=DEFAULT&authSource=syia-etl-dev'
        db_name = 'syia-etl-dev'
        mongo_client = MongoClient(mongo_uri)
        db = mongo_client[db_name]
        collection = db['common_consumption_log_api']

        query = {
            "IMO No": int(imo)
        }

        # Add date filters only if they are provided
        if start_date and end_date:
            query["Report Date"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query["Report Date"] = {"$gte": start_date}
        elif end_date:
            query["Report Date"] = {"$lte": end_date}

        projection = {
            "_id":0,
            "Report Date":1,
            "Vessel Name":1,
            "data.Steaming time (HRS)" : 1,
            "data.ME Total Consumption":1,
            "data.AE Total Consumption":1,
            "data.BLR Total Consumption":1,
            "data.Total Consumption HSFO":1,
            "data.Total Consumption ULSFO":1,
            "data.Total Consumption MDO":1,
            "data.Total Consumption LSMGO":1,
            "data.Total Consumption VLSFO": 1,
            "data.Total Consumption LNG": 1,
            "data.AE HSFO consumption (MT)":1,
            "data.ME HSFO consumption (MT)":1,
            "data.BLR HSFO consumption (MT)":1,
            "data.AE ULSFO consumption (MT)":1,
            "data.ME ULSFO consumption (MT)":1,
            "data.BLR ULSFO consumption (MT)":1,
            "data.AE MDO consumption (MT)":1,
            "data.ME MDO consumption (MT)":1,
            "data.BLR MDO consumption (MT)":1,
            "data.AE LS MGO consumption (MT)":1,
            "data.ME LS MGO consumption (MT)":1,
            "data.BLR LS MGO consumption (MT)":1,
            "data.AE VLSFO consumption (MT)":1,
            "data.ME VLSFO consumption (MT)":1,
            "data.BLR VLSFO consumption (MT)":1,
            "data.AE LNG consumption (MT)":1,
            "data.ME LNG consumption (MT)":1,
            "data.BLR LNG consumption (MT)":1,
            "data.ROB HSFO":1,
            "data.ROB ULSFO":1,
            "data.ROB MDO":1,
            "data.ROB LS MGO":1,
            "data.ROB VLSFO":1,
            "data.ROB LNG":1,
            "data.ChartererPartySpeed":1,
            "data.ChartererPartyConsumption":1
        }
        documents = list(collection.find(query, projection))

        if not documents:
            return [types.TextContent(
                type="text",
                text=f"No fuel consumption data found for vessel with IMO {imo}",
                title=f"Fuel consumption history for IMO {imo}"
            )]
            
        documents = sorted(documents, key=lambda x: x['Report Date'], reverse=True)

        # Convert documents to json
        documents_json = json.dumps(documents, indent=2, default=str)
        
        # Create text content
        content = types.TextContent(
            type="text",
            text=documents_json,
            title=f"Fuel consumption history for IMO {imo}",
            format="json"
        )

        vessel_name = documents[0].get("Vessel Name")

        data_link = get_data_link(documents_json)
        insert_data_link_to_mongodb(data_link, "Vessel fuel consumption history", session_id, imo, vessel_name)

        artifact_data = get_artifact("get_vessel_fuel_consumption_history", data_link)
        
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Fuel consumption history for IMO {imo}",
            format="json"
        )
        return [content, artifact]
    
    except Exception as e:
        logger.error(f"Error getting vessel fuel consumption history: {e}")
        raise ValueError(f"Error getting vessel fuel consumption history: {str(e)}")


async def create_update_casefile(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    try:
        S3_API_TOKEN = (
                        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
                        'eyJkYXRhIjp7ImlkIjoiNjRkMzdhMDM1Mjk5YjFlMDQxOTFmOTJhIiwiZmlyc3ROYW1lIjoiU3lpYSIsImxhc3ROYW1lIjoiRGV2Ii'
                        'wiZW1haWwiOiJkZXZAc3lpYS5haSIsInJvbGUiOiJhZG1pbiIsInJvbGVJZCI6IjVmNGUyODFkZDE4MjM0MzY4NDE1ZjViZiIsIml'
                        'hdCI6MTc0MDgwODg2OH0sImlhdCI6MTc0MDgwODg2OCwiZXhwIjoxNzcyMzQ0ODY4fQ.'
                        '1grxEO0aO7wfkSNDzpLMHXFYuXjaA1bBguw2SJS9r2M'
                    )
        S3_GENERATE_HTML_URL = "https://dev-api.siya.com/v1.0/s3bucket/generate-html"

        imo = arguments.get("imo")
        raw_content = arguments.get("content")
        casefile = arguments.get("casefile")
        session_id = arguments.get("session_id", "11111")
        user_id = arguments.get("user_id")  

        if not imo:
            raise ValueError("IMO is required")
        if not raw_content:
            raise ValueError("content is required")
        if not casefile:
            raise ValueError("casefile is required")
        if not session_id:
            raise ValueError("session_id is required")

        def get_prompt(agent_name: str) -> str:
            try:
                client = MongoClient(MONGODB_URI)
                db = client[MONGODB_DB_NAME]
                collection = db["mcp_agent_store"]

                document = collection.find_one(
                    {"name": agent_name},
                    {"answerprompt": 1, "_id": 0}
                )

                return document.get(
                    "answerprompt",
                    "get the relevant response based on the task in JSON format {{answer: answer for the task, topic: relevant topic}}"
                ) if document else "get the relevant response based on the task"

            except Exception as e:
                logger.error(f"Error accessing MongoDB in get_prompt: {e}")
                return None

        def generate_html_and_get_final_link(body: str, imo: str) -> Union[str, None]:
            headers = {
                'Authorization': f'Bearer {S3_API_TOKEN}',
                'Content-Type': 'application/json'
            }

            current_unix_time = int(time.time())
            filename = f"answer_content_{imo}_{current_unix_time}"

            payload = {
                "type": "reports",
                "fileName": filename,
                "body": body
            }

            try:
                response = requests.post(S3_GENERATE_HTML_URL, headers=headers, json=payload)
                response.raise_for_status()
                return response.json().get("url")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to generate HTML: {e}")
                return None

        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        casefile_db = db.casefiles

        try:
            prompt = get_prompt("casefilewriter")
            if not prompt:
                raise RuntimeError("Failed to load prompt from database")
            

            format_instructions = '''
        Respond in the following JSON format:
        {
        "content": "<rewritten or cleaned summarized version of the raw content>",
        "topic": "<short summary of the case>",
        "flag": "<value of the flag generated by LLM",
        "importance": "<low/medium/high>"
        }
        '''.strip()

            system_message = f"{prompt}\n\n{format_instructions}"
            user_message = f"Casefile: {casefile}\n\nRaw Content: {raw_content}"

            llm_client = LLMClient(openai_api_key=OPENAI_API_KEY)

            try:
                result = await llm_client.ask(
                    query=user_message,
                    system_prompt=system_message,
                    model_name="gpt-4o",
                    json_mode=True,
                    temperature=0 
                )

                # Validate output keys
                if not all(k in result for k in ["content", "topic", "flag", "importance"]):
                    raise ValueError(f"Missing keys in LLM response: {result}")

            except Exception as e:
                raise ValueError(f"Failed to generate or parse LLM response: {e}")

            # response = getfields(prompt, raw_content, casefile)

            summary = result['topic']
            content = result['content']
            flag = result['flag']
            importance = result['importance']

            client = MongoClient(MONGODB_URI)
            db = client[MONGODB_DB_NAME]
            collection = db["casefile_data"]
            link_document = collection.find_one(
                    {"sessionId": session_id},
                    {"links": 1, "_id": 0}
                )
            
            existing_links = link_document.get('links', []) if link_document else []

            
            for entry in existing_links:
                entry.pop('synergy_link', None)

            content_link = generate_html_and_get_final_link(content, imo)
            link = ([{'link': content_link, 'linkHeader': 'Answer Content'}] if content_link else []) + existing_links

            now = datetime.now(timezone.utc)
            vessel_doc = db.vessels.find_one({"imo": imo}) or {}
            vessel_name = vessel_doc.get("name", "Unknown Vessel")

            # def get_suffix(day): 
            #     return 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

            # date_str = f"{now.day}{get_suffix(now.day)} {now.strftime('%B %Y')}"
            # casefile_title = f"Casefile Status as of {date_str}"
            color = {"high": "#FFC1C3", "medium": "#FFFFAA"}.get(importance)

            # # Fuzzy match logic for casefile
            search_query = {"imo": imo}
            if user_id:
                search_query["userId"] = user_id
            all_casefiles = list(casefile_db.find(search_query))
            best_match = None
            best_score = 0
            for doc in all_casefiles:
                doc_casefile = doc.get("casefile", "").lower()
                score = difflib.SequenceMatcher(None, doc_casefile, casefile.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = doc
            
            if best_score >= 0.9 and best_match is not None:
                filter_query = {"_id": best_match["_id"]}
                existing = best_match
                old_casefile = best_match["casefile"]
            else:
                filter_query = {"imo": imo, "casefile": casefile}
                if user_id:
                    filter_query["userId"] = user_id
                else:
                    filter_query["userId"] = {"$exists": False}
                existing = None
                old_casefile = None
            
            new_index = {
                "pagenum": len(existing.get("pages", [])) if existing else 0,
                "sessionId": session_id,
                "type": "task",
                "summary": summary,
                "createdAt": now
            }
            
            new_page = {
                "pagenum": new_index["pagenum"],
                "sessionId": session_id,
                "type": "task",
                "summary": summary,
                "flag": flag,
                "importance": importance,
                "color": color,
                "content": content,
                "link": link,
                "createdAt": now
            }

            result = casefile_db.update_one(
                filter_query,
                {
                    "$setOnInsert": {
                        "vesselName": vessel_name,
                        **({"userId": user_id} if user_id else {})
                    },
                    "$push": {
                        "pages": new_page,
                        "index": new_index
                    }
                },
                upsert=True
            )

            # Fetch the document to get its _id
            doc = casefile_db.find_one(filter_query, {"_id": 1})
            mongo_id = str(doc["_id"]) if doc and "_id" in doc else None

            if result.matched_count == 0:
                status_message = f"Created new entry in database with casefile - {casefile}"
            else:
                if old_casefile.lower().strip() == casefile.lower().strip():
                    status_message = f"Updated an existing entry in database with casefile - {old_casefile}"
                else:
                    status_message = f"Updated an existing entry in database, old casefile {old_casefile} has been replaced by {casefile}"

            return [
                types.TextContent(
                    type="text", 
                    text=f"{status_message}. MongoID: {mongo_id}"
                )
            ]
        
        except Exception as e:
            logger.error(f"casefile_writer failed: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error in create_update_casefile: {str(e)}"
            )]
    except Exception as e:
        logger.error(f"casefile_writer failed: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error in create_update_casefile: {str(e)}"
        )]



async def google_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:

    query = arguments.get("query")
    if not query:
        raise ValueError("Search query is required")
    

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}"
    }
    payload = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert assistant helping with reasoning tasks."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": None,
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "week",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "response_format": None
    }

    try:
        timeout = httpx.Timeout(connect=10, read=100, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                citations = result.get("citations", [])
                content = result['choices'][0]['message']['content']
                return [
                    types.TextContent(
                        type="text", 
                        text=f"Response: {content}\n\nCitations: {citations}"
                    )
                ]
            else:
                error_text = response.text
                return [
                    types.TextContent(
                        type="text", 
                        text=f"Error: {response.status_code}, {error_text}"
                    )
                ]

    except Exception as e:
        logger.error(f"Failure to execute the search operation: {e}")
        raise



 # ─────────────────────────────────────────────────────────────────────────────
 # SHIPPALM Tools
 # ─────────────────────────────────────────────────────────────────────────────


# ── Credentials ───────────────────────────────────────────────────────────
load_dotenv()
EMAIL = os.getenv("SHIPPALM_EMAIL", "")
PASSWORD = os.getenv("SHIPPALM_PASSWORD", "")
# DOC LIST
norden_doc_list =['SDK', 'NSSM']
synergy_group_doc_list = ['SMGGH']

# ─────────────────────────────────────────────────────────────────────────────
# Position Book Report
# ─────────────────────────────────────────────────────────────────────────────
 
async def _position_book_automation(vessel_name: str, outfile: Path, shippalm_doc: str) -> dict:
    # Determine base URL based on doc
    if shippalm_doc in norden_doc_list:
        base_url = f"https://shippalmv3.norden-synergy.com/?company={shippalm_doc}"
    elif shippalm_doc in synergy_group_doc_list:
        base_url = f"https://shippalmv3.synergygroup.sg/?company={shippalm_doc}"
    else:
        base_url = f"https://shippalmv3.synergymarinegroup.com/?company={shippalm_doc}"

    # Microsoft SSO login URL remains the same
    login_url = (
        "https://login.microsoftonline.com/common/wsfed?"
        "wa=wsignin1.0&wtrealm=https%3a%2f%2fshippalmv3.synergymarinegroup.com"
        "&wreply=https%3a%2f%2fshippalmv3.synergymarinegroup.com%2fSignIn%3fReturnUrl%3d%252f"
        "&sso_reload=true"
    )

    # Initialize result dictionary
    result = {
        "table_data": [],
        "error": None,
        "screenshot_path": None  # Initialize screenshot path
    }

    async with async_playwright() as p:
        logger.info("launch browser (non-headless)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width":1280, "height":900})
        page = await context.new_page()

        try:
            # 1. Login
            logger.info("goto login URL")
            await page.goto(login_url, timeout=60000)

            # Optional account tile
            tile = page.locator(f'div[data-test-id="accountTile"] >> text="{EMAIL}"')
            if await tile.count():
                await tile.first.click()

            # Email input
            await page.fill('input[type="email"], input[name="loginfmt"]', EMAIL)
            await page.click('button[type="submit"], input[type="submit"][value="Next"]')
            # Password input
            await page.fill('input[type="password"]', PASSWORD)
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle", timeout=60000)

            # After successful login, navigate to the specific company URL
            logger.info(f"Navigating to base URL: {base_url}")
            logger.info(f"DOC NAME: {shippalm_doc}")
            await page.goto(base_url)
            await page.wait_for_load_state("networkidle", timeout=60000)

            # 2. Enter main iframe
            iframe = page.frame_locator('iframe[title="Main Content"]')

            # 3. Navigate to Voyage
            logger.info("navigating to Voyage")
            await iframe.get_by_role("menuitem", name="Voyage").click()
            await sleep(1)
            
            # 4. Click on Position Book Report
            logger.info("clicking on Position Book Report")
            try:
                # Try first with exact name matching
                position_book = iframe.get_by_role("menuitem", name="Position Book Report").first
                await position_book.wait_for(state="visible", timeout=10000)
                await position_book.click()
                logger.info("Clicked Position Book Report using role selector")
            except Exception as e:
                logger.warning(f"Failed to click using role selector: {str(e)}")
                
                try:
                    # Try with link title
                    position_book_link = iframe.locator('a[title="Position Book Report"]').first
                    await position_book_link.wait_for(state="visible", timeout=10000)
                    await position_book_link.click()
                    logger.info("Clicked Position Book Report using link selector")
                except Exception as e2:
                    logger.warning(f"Failed to click using link selector: {str(e2)}")
                    
                    try:
                        # Try with text content
                        position_text = iframe.locator('text="Position Book Report"').first
                        await position_text.wait_for(state="visible", timeout=10000)
                        await position_text.click()
                        logger.info("Clicked Position Book Report using text selector")
                    except Exception as e3:
                        logger.error(f"All methods to click Position Book Report failed: {str(e3)}")
                        raise Exception("Could not find or click Position Book Report element")
            
            await sleep(2)  # Wait for page to load
            
            # 5. Click on filter button
            logger.info("clicking filter button")
            try:
                filter_button = iframe.get_by_role("menuitemcheckbox", name="Toggle filter").first
                await filter_button.wait_for(state="visible", timeout=10000)
                await filter_button.click()
                logger.info("Clicked filter button")
            except Exception as e:
                logger.error(f"Failed to click filter button: {str(e)}")
                raise
            
            await sleep(1)
            
            # 6. Click on All (might be a button or option)
            logger.info("clicking All option")
            try:
                all_button = iframe.get_by_role("menuitem", name="All", exact=True).first
                if await all_button.count() > 0:
                    await all_button.click()
                    logger.info("Clicked All button")
                else:
                    all_option = iframe.locator('text="All"').first
                    await all_option.click()
                    logger.info("Clicked All text option")
            except Exception as e:
                logger.warning(f"Failed to click All option: {str(e)}")
            
            await sleep(1)
            
            # 7. Add Vessel Name filter
            logger.info(f"applying Vessel Name filter: {vessel_name}")
            
            # Add a filter field
            await iframe.get_by_role("button", name="Add a new filter on a field").click()
            await sleep(1)
            
            # Select Vessel Name option
            try:
                await iframe.get_by_role("option", name="Vessel Name", exact=True).click()
                logger.info("Selected Vessel Name filter")
            except Exception:
                # Try with just Vessel if Vessel Name is not available
                await iframe.get_by_role("option", name="Vessel", exact=True).click()
                logger.info("Selected Vessel filter")
            
            await sleep(1)
            
            # Fill the Vessel combobox
            try:
                combo_v = iframe.get_by_role("combobox", name="Vessel Name").first
                if await combo_v.count() == 0:
                    combo_v = iframe.get_by_role("combobox", name="Vessel").first
                
                await combo_v.fill(vessel_name)
                logger.info(f"Filled vessel name: {vessel_name}")
            except Exception as e:
                logger.error(f"Failed to fill vessel name: {str(e)}")
                raise
            
            # Wait for dropdown and click
            dropdown_v = iframe.locator('div.spa-view.spa-lookup')
            await dropdown_v.wait_for(state="visible", timeout=30000)
            await sleep(2)  # Give time for dropdown to populate
            
            # Try to select the vessel from dropdown
            try:
                vessel_option = dropdown_v.locator(f'tr:has-text("{vessel_name}")').first
                if await vessel_option.count() > 0:
                    logger.info(f"Found vessel by name")
                    await vessel_option.click()
                else:
                    # Try with exact text
                    vessel_option = dropdown_v.locator(f'text="{vessel_name}"').first
                    await vessel_option.click()
                
                logger.info(f"Successfully selected vessel {vessel_name}")
                await sleep(2)  # Wait for selection to take effect
            
            except Exception as e:
                logger.error(f"Error selecting vessel: {str(e)}")
                raise

            # Get table data
            logger.info("Getting table data")
            try:
                # Get content from result browser
                logger.info("Getting result browser content")
                result_browser = iframe.locator('#b3q')
                
                # Wait for the table to be visible
                await result_browser.wait_for(state="visible", timeout=30000)
                logger.info("Table is visible")
                
                # Get both text and HTML content
                result_content = await result_browser.inner_text()
                result_html = await result_browser.evaluate('el => el.outerHTML')
                
                logger.info("Successfully got result browser content")
                
                # Store both text and HTML in the result
                result["table_data"] = [
                    {
                        "text_content": result_content,
                        "html_content": result_html
                    }
                ]

                # Take screenshot and save it
                logger.info("Taking screenshot")
                screenshots_dir = Path("screenshots")
                screenshots_dir.mkdir(exist_ok=True)
                screenshot_path = screenshots_dir / outfile.name
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved at: {screenshot_path}")

                # Add screenshot path to result
                result["screenshot_path"] = str(screenshot_path.resolve())

            except Exception as e:
                logger.error(f"Error getting table data: {str(e)}")
                result["error"] = f"Error getting table data: {str(e)}"

        except Exception as e:
            logger.error(f"Failed to retrieve position book data: {str(e)}")
            result["error"] = str(e)
        finally:
            await context.close()
            await browser.close()
            
    return result


async def position_book_report_from_shippalm(vessel_name: str, shippalm_doc: str) -> list[dict]:
    """Return text content blocks containing table data and screenshot file path for Position Book Report.
    
    Args:
        vessel_name: The name of the vessel to filter by
        shippalm_doc: Document type for determining login URL
        
    Returns:
        List of content blocks containing table data and screenshot path
    """
    out = timestamped_filename(prefix=f"{vessel_name}_position_book")
    result = await _position_book_automation(vessel_name, out, shippalm_doc)
    
    # Format the response as a list of content blocks
    content_blocks = []
    
    # Add table data if available
    if result.get("table_data"):
        content_blocks.append({
            "type": "text",
            "text": json.dumps(result["table_data"], indent=2)
        })
    
    # Add screenshot path if available
    if result.get("screenshot_path"):
        content_blocks.append({
            "type": "text",
            "text": f"Screenshot saved at: {result['screenshot_path']}"
        })
    
    # Add any error messages
    if result.get("error"):
        content_blocks.append({
            "type": "text",
            "text": f"Error: {result['error']}"
        })
    
    # If no content blocks were added, add an error message
    if not content_blocks:
        content_blocks.append({
            "type": "text",
            "text": "No data could be retrieved from ShipPalm"
        })
    
    return content_blocks


########## casefile update ##########


def make_text_response(text: str, title: str = "Filesystem Response"):
    return [{
        "type": "text",
        "text": text,
        "title": title,
        "format": "json"
    }]
# Configuration constants
API_BASE_URL = "https://dev-api.siya.com"
API_TOKEN = (
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
    'eyJkYXRhIjp7ImlkIjoiNjRkMzdhMDM1Mjk5YjFlMDQxOTFmOTJhIiwiZmlyc3ROYW1lIjoiU3lpYSIsImxhc3ROYW1lIjoiRGV2Ii'
    'wiZW1haWwiOiJkZXZAc3lpYS5haSIsInJvbGUiOiJhZG1pbiIsInJvbGVJZCI6IjVmNGUyODFkZDE4MjM0MzY4NDE1ZjViZiIsIml'
    'hdCI6MTc0MDgwODg2OH0sImlhdCI6MTc0MDgwODg2OCwiZXhwIjoxNzcyMzQ0ODY4fQ.'
    '1grxEO0aO7wfkSNDzpLMHXFYuXjaA1bBguw2SJS9r2M'
)
COLLECTION_NAME = "casefiles"
TYPESENSE_COLLECTION = "emailCasefile"


def convert_importance(importance: float) -> str:
    """Convert numeric importance to descriptive level."""
    if importance is None:
        return "low"
    try:
        imp = float(importance)
        if imp <= 50:
            return "low"
        if imp < 80:
            return "medium"
        return "high"
    except (TypeError, ValueError):
        return "low"


def generate_casefile_weblink(casefile_id: str) -> str:
    """Call the diary API to generate a casefile HTML weblink."""
    endpoints = [
        f"{API_BASE_URL}/v1.0/diary/casefile-html/{casefile_id}",
        f"{API_BASE_URL}/v1.0/diary/casefilehtml/{casefile_id}"
    ]
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    for url in endpoints:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            body = resp.json()
            data = body.get("resultData", {})
            if body.get("status") == "OK" and data.get("url"):
                return data["url"]
    raise ValueError(f"Could not generate weblink for casefile {casefile_id}")


def push_to_typesense(res:dict, action:str):
    id = res['id']
    casefile_txt = res['casefile']
    summary_txt = res['summary']    
    embedding_text = (
        f"Below casefile {casefile_txt} with following summary {summary_txt} "
    )
    link = generate_casefile_weblink(id)

     ## update the casefile in mongodb
    client = MongoDBClient()
    collection = client.db["casefiles"]
    collection.update_one({"_id": ObjectId(id)}, {"$set": {"link": link}})
    data = {
        "id":str(id),
        "_id":str(id),
        "casefile":res['casefile'],
        "currentStatus":res['currentStatus'],
        "casefileInitiationDate":int(res['createdAt'].timestamp()),
        "category":res['category'],
        "conversationTopic":[],
        "embedding_text":embedding_text,
        "imo":int(res['imo']),
        "importance":convert_importance(res['importance']),
        "importance_score":res['importance'],
        "lastcasefileUpdateDate":int(res['updatedAt'].timestamp()),
        "summary":res['summary'],
        "vesselId":str(res['vesselId']),
        "vesselName":str(res['vesselName']),
        "link":link,
        "followUp":res.get("followUp",""),
        "pages":str(res.get("pages",[])[-2:]),
        "index":str(res.get("index",[])[-2:])

}
    if res.get("plan_status",None):
        data["plan_status"] = res.get("plan_status",None)
    try:
        client = TypesenseClient()
        logger.info(f"data pushed to typsesne {data}")
        
        result = client.collections["emailCasefile"].documents.import_([data],{"action":action})
        logger.info(result)
        return result
    except Exception as e:
        logger.error(f"Error updating casefile: {e}")
        raise ValueError(f"Error updating casefile: {e}")
    

async def get_vessel_name(imo: Union[str, int]):
    """Fetch vessel name and ID by IMO from MongoDB."""
    client = MongoDBClient()
    vessel = await client.db["vessels"].find_one({"imo": imo})
    if vessel:
        return vessel.get("name"), vessel.get("_id")
    return None, None


async def link_to_id(casefile_url: str) -> str:
    """Extract the ObjectId string from a casefile URL."""
    return casefile_url.split('/')[-1].replace('.html', '')

async def read_mail(arguments: dict) -> dict:
    """Retrieve and parse email data for updating a casefile."""
    mail_id = arguments.get("mailId")
    if not mail_id or not ObjectId.is_valid(mail_id):
        raise ValueError("Valid mailId is required")
    client = MongoDBClient()
    mail = await client.db["mail_temp"].find_one({"_id": ObjectId(mail_id)})
    if not mail:
        raise ValueError(f"Mail {mail_id} not found")
    generator = MailBodyLinkGenerator()
    link = await generator.generate_mail_link(mail)
    return {
        "referenceId": str(mail["_id"]),
        "createdAt": mail.get("DateTimeReceived"),
        "toRecipientsEmailAddresses": mail.get("ToRecipients_EmailAddresses", []),
        "senderEmailAddress": mail.get("SenderEmailAddress", []),
        "subject": mail.get("Subject"),
        "attachments": mail.get("attachments", []),
        "link": link,
        "tags": []
    }

async def create_casefile(arguments:dict):
    casefile_name = arguments.get("casefileName",None)
    casefile_summary = arguments.get("casefileSummary",None)
    current_status = arguments.get("currentStatus",None)
    originalImportance = arguments.get("importance",0)
    category = arguments.get("category","charterParty")
    role = arguments.get("role",None)
    imo = arguments.get("imo",None)

    if imo:
        vessel_name,vessel_id = await get_vessel_name(imo)
    else:
        vessel_name = None
        vessel_id = None

    logger.info(f"Creating casefile for vessel {vessel_name} with imo {imo}")
    client = MongoDBClient()
    logger.info(f"mongodb client: {client.__dict__}")

    collection = client.db["casefiles"]
    data ={
        "vesselId": vessel_id,
        "imo": imo,
        "vesselName": vessel_name,
        "casefile": casefile_name,
        "currentStatus":current_status,
        "summary": casefile_summary,
        "originalImportance": originalImportance,
        "importance": originalImportance,
        "category": category,
        "role": role,
        "followUp":"",
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
        "index":[],
        "pages":[]
       }
    logger.info(data)
    result = await collection.insert_one(data)
    logger.error(f"result after insert in mongodb: {result}")
    
    casefile_id = str(result.inserted_id)
    casefile_url = generate_casefile_weblink(casefile_id)
    logger.info(f"casefile_url: {casefile_url}")

    await collection.update_one({"_id": ObjectId(casefile_id)}, {"$set": {"link": casefile_url}})


    ## typesense update
    client = TypesenseClient()
    data.pop("index")
    data.pop("pages")
    data.pop("_id")
    data["id"] = str(casefile_id)
    data["vesselId"] = str(vessel_id)
    # data['createdAt'] = int(data['createdAt'].timestamp())
    # data['updatedAt'] = int(data['updatedAt'].timestamp())
    try:
       logger.info(data)
       #result =client.collections[typesense_collection].documents.import_([data],{"action":"create"})
       # push to typesense
       result = push_to_typesense(data, "create")

       logger.info(result)
    except Exception as e:
        logger.error(f"Error importing data to typesense: {e}")
    try:
        return make_text_response(f"Casefile created with casefile url: {casefile_url}",title="create casefile")
    except Exception as e:
        logger.error(f"Error creating casefile: {e}")
        


async def update_casefile(arguments: dict):
    casefile_url = arguments.get("casefile_url")
    casefile_summary = arguments.get("casefileSummary")
    importance = arguments.get("importance")
    plan_status = "unprocessed"
    tags = arguments.get("tags", [])
    topic = arguments.get("topic")
    summary = arguments.get("summary")
    mail_id = arguments.get("mailId")
    current_status = arguments.get("currentStatus",None)
    casefile_name = arguments.get("casefileName",None)
    facts = arguments.get("facts",None)
    links = arguments.get("links",[])
    detailed_report=arguments.get("detailed_report","")
    links=[{"link": i} for i in links]
    links=[{"link":markdown_to_html_link(detailed_report)}]+links
    

    client = MongoDBClient()
    collection = client.db["casefiles"]

    if not casefile_url:
        raise ValueError("Casefile URL is required")

    if not ObjectId.is_valid(casefile_url):
        casefile_id = await link_to_id(casefile_url)
        if not ObjectId.is_valid(casefile_id):
            raise ValueError("Valid Casefile ID is required")
    else:
        casefile_id = casefile_url 


    # Normalize tags: string to list if needed
    if isinstance(tags, str):
        tags = [tags]

    # mail_info = await read_mail(arguments)

    ### fetch the casefile
   # casefile = await collection.find_one({"_id": ObjectId(casefile_id)})
    
    if facts:
        # if not topic:
        #     topic = ""
        # topic = topic + " : " + facts
        summary = summary + " <br> " + facts

    # ------------------- AGGREGATION PIPELINE ---------------------
    update_pipeline = []

    # Stage 1: Conditional base field updates
    set_stage = {}
    set_stage["updatedAt"] = datetime.now(UTC)
    if casefile_name is not None:
        set_stage["casefile"] = casefile_name
    if current_status is not None:
        set_stage["currentStatus"] = current_status
    if casefile_summary is not None:
        set_stage["summary"] = casefile_summary
    if importance is not None:
        set_stage["importance"] = importance
    if plan_status is not None:
        set_stage["plan_status"] = plan_status
    if set_stage:
        update_pipeline.append({ "$set": set_stage })

    # Stage 2: Ensure arrays exist and compute new pagenum
    update_pipeline.append({
        "$set": {
            "pages": { "$ifNull": ["$pages", []] },
            "index": { "$ifNull": ["$index", []] },
            "_nextPageNum": {
                "$add": [
                    {
                        "$max": [
                            { "$ifNull": [{ "$max": "$pages.pagenum" }, 0] },
                            { "$ifNull": [{ "$max": "$index.pagenum" }, 0] }
                        ]
                    },
                    1
                ]
            }
        }
    })

    # Stage 3: Update tags as a unique set
    if tags:
        update_pipeline.append({
            "$set": {
                "tags": {
                    "$setUnion": [
                        { "$ifNull": ["$tags", []] },
                        tags
                    ]
                }
            }
        })

    # Stage 4: Append to pages and index arrays
    update_pipeline.append({
        "$set": {
            "pages": {
                "$concatArrays": [
                    "$pages",
                    [
                        {
                            "pagenum": "$_nextPageNum",
                            
                            "summary": summary,
                            "createdAt":datetime.now(UTC),
                            "subject": topic,
                            "flag": topic,
                            "type": "QA_Agent",
                            "link": links,
                            "plan_status": plan_status
                        }
                    ]
                ]
            },
            "index": {
                "$concatArrays": [
                    "$index",
                    [
                        {
                            "pagenum": "$_nextPageNum",
                            "type": "QA_Agent",
                            "createdAt": datetime.now(UTC),
                            "topic": topic,
                            "plan_status": plan_status
                        }
                    ]
                ]
            }
        }
    })

    # Stage 5: Cleanup temporary field
    update_pipeline.append({ "$unset": "_nextPageNum" })

    # ------------------- EXECUTE UPDATE ---------------------
    result = await collection.update_one(
        { "_id": ObjectId(casefile_id) },
        update_pipeline
    )

    ## synergy core update
    # synergy_core_client = SynergyMongoDBClient()
    # synergy_collection = synergy_core_client.db["casefiles"]
    # await synergy_collection.update_one({"_id": ObjectId(casefile_id)}, update_pipeline)

    ## typesense update
    try:
        # client = TypesenseClient()
        mongoresult = await collection.find_one({"_id": ObjectId(casefile_id)})
        updated_at = mongoresult.get("updatedAt",None)

            
        update_fields = {
            "id":str(casefile_id),
            "summary": mongoresult.get("summary",None),
            "originalImportance": mongoresult.get("originalImportance",None),
            "importance": mongoresult.get("importance",0),
            "plan_status": mongoresult.get("plan_status",None),
            "tag": mongoresult.get("tag",None),
            "createdAt":mongoresult.get("createdAt",None),
            "updatedAt": mongoresult.get("updatedAt",None),
            "casefile": mongoresult.get("casefile",None),
            "currentStatus": mongoresult.get("currentStatus",None),
            "vesselId": str(mongoresult.get("vesselId",None)),
            "imo": mongoresult.get("imo",None),
            "vesselName": mongoresult.get("vesselName",None),
            "category": mongoresult.get("category",None),
            "conversationTopic": mongoresult.get("conversationTopic",None),
            "role": mongoresult.get("role",None),
            "followUp": mongoresult.get("followUp",""),
            "pages": mongoresult.get("pages",[])[-2:],
            "index": mongoresult.get("index",[])[-2:]
            
        }
        if mongoresult.get("importance",None):
            update_fields["importance"] = mongoresult.get("importance",0)
        logger.info(update_fields)

        #result = client.collections[typesense_collection].documents.import_([update_fields],{"action":"upsert"})
        result = push_to_typesense(update_fields, "upsert")
        return make_text_response(f"Casefile updated with casefile url: {casefile_url}",title="update casefile")
    
    except Exception as e:
        logger.error(f"Error updating casefile: {e}")


async def write_casefile_data(arguments: dict):
    """
    Dispatcher for write operations: creates or updates a casefile based on arguments.

    Expects 'operation' in arguments: 'write_casefile' or 'write_page'.
    """
    op = arguments.get("operation")
    if op == "write_casefile":
        return await create_casefile(arguments)
    if op == "write_page":
        return await update_casefile(arguments)
    raise ValueError(f"Unsupported operation for write_casefile_data: '{op}'")




async def getcasefile(arguments: dict):
    query = arguments.get("query")
    imo = arguments.get("imo",None)
    category = arguments.get("category","charterParty")
    min_importance = arguments.get("min_importance",0)
    page_size = arguments.get("page_size",10)
    pagination = arguments.get("pagination",1)
 
    filter_by = []
    if imo: # imo is a string
        filter_by.append(f"imo:{imo}")
    if min_importance: # min_importance is a float
        filter_by.append(f"importance_score:>{min_importance}")
    if category: # category is a string
        filter_by.append(f"category:{category}")
 
    if filter_by:
        filter_by = "&&".join(filter_by)
 
 
    if query:
        typesense_query = {"q":query,
                       "query_by":"embedding, embedding_text",
                       "per_page":page_size,
                       "exclude_fields":"embedding",
                       "prefix":False,
                       "filter_by":filter_by,
                       "page":pagination}
    else:
        typesense_query = {"q":"*",
                       "query_by":"embedding, embedding_text",
                       "per_page":page_size,
                       "exclude_fields":"embedding",
                       "prefix":False,
                       "filter_by":filter_by,
                       "page":pagination}
       
    try:   
    
        client = TypesenseClient()
        result = client.collections["emailCasefile"].documents.search(typesense_query)
        
        formatted_result = []
        for item in result["hits"]:
            doc = item["document"]
            formatted_result.append({
            "casefile_id":doc["id"],
            "casefile_name":doc["casefile"],
            "current_status":doc.get("currentStatus",""),
            "summary":doc["summary"],
            "importance":doc["importance_score"],
            "casefile_url":doc["link"],
            "pages":doc["pages"]
            })
        return make_text_response(json.dumps(formatted_result),title="Casefile Search Results")
    except Exception as e:
        logger.error(f"Error searching casefiles: {e}")

 
 
async def link_to_id(casefile_url):
    return casefile_url.split("/")[-1].replace(".html","")


async def get_casefile_plan(arguments: dict):
    casefile_url = arguments.get("casefile_url")
    try:
        if not ObjectId.is_valid(casefile_url):
            casefile_id = await link_to_id(casefile_url)
            if not ObjectId.is_valid(casefile_id):
                raise ValueError("Invalid Casefile ID")
        else:
            casefile_id = casefile_url
 
        client = MongoDBClient()
        collection = client.db["casefiles"]
        query = {"_id": ObjectId(casefile_id)}
        if not collection.find_one(query):
            return [types.TextContent(
                type="text",
                text=f"Casefile {str(casefile_url)} not found"
            )]
        # get the latest entry in casefilePlans array
      ## check pages in casefile
        pipeline = [
            {"$match": {"_id": ObjectId(casefile_id)}},
            {
                "$project": {
                    "_id": 0,
                    "latest_plan": {
                        "$arrayElemAt": ["$casefilePlans", -1]
                    }
                }
            }
        ]
        
        results = await collection.aggregate(pipeline).to_list()
 
        return [types.TextContent(
            type="text",
            text=str(results),
            title=f"Casefile Plans for {str(casefile_url)}"
        )]
    except Exception as e:
        logger.error(f"Error getting casefile plans: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error getting casefile plans: {str(e)}"
        )]
 

 
