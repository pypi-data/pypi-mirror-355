from mcp_survey.databases import *
import json
from typing import Dict, Any, TypedDict
from enum import Enum
from typing import Union, Sequence, Optional

import mcp.types as types
from mcp_survey import mcp, logger
import requests
from mcp_survey.tool_schema import tool_definitions
import datetime as dt
from mcp_survey.utils import timestamped_filename
from playwright.async_api import async_playwright
from asyncio import sleep
import os
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId
import re
import time
from datetime import datetime,timezone,UTC #import for casefile update 

from . import logger
from typing import Dict, Any, List, Union, Optional

import openai


import pickle
import base64
from pydantic import BaseModel, EmailStr, HttpUrl, Field

from typing import List, Literal
from typing import Optional, List, Literal

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
# import for casefile update 

from bson import ObjectId
from .databases import MongoDBClient, TypesenseClient
from .generate_mail_html import MailBodyLinkGenerator
from . import logger
from .html_link_from_md import markdown_to_html_link
#-------

from .constants import MONGODB_URI, MONGODB_DB_NAME, OPENAI_API_KEY, LLAMA_API_KEY, VENDOR_MODEL, PERPLEXITY_API_KEY

MONGO_URI = r'mongodb://syia-etl-dev:SVWvsnr6wAqKG1l@db-etl.prod.syia.ai:27017/?authSource=syia-etl-dev'
DB_NAME = 'syia-etl-dev'

from utils.llm import LLMClient
from document_parse.main_file_s3_to_llamaparse import parse_to_document_link

import difflib
import httpx

server_tools = tool_definitions
async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        try:
            # MongoDB tool handlers
            if name == "get_certificate_table_schema":
                return await get_typesense_schema(arguments)
            elif name == "mongodb_find":
                return await mongodb_find(arguments)
            elif name == "vessel_info_search":
                return await vessel_info_search(arguments)
            elif name == "get_user_associated_vessels":
                return await get_user_associated_vessels(arguments)
            elif name == "smart_certificate_search":
                return await smart_certificate_search_handler(arguments)
            # elif name == "get_vessel_imo_number":
            #     return await imo_search(arguments)
            elif name == "get_vessel_details":
                return await get_vessel_details(arguments)
            elif name == "get_class_survey_report":
                return await get_class_survey_report(arguments)
            elif name == "get_class_certificate_status":
                return await get_class_certificate_status(arguments)
            elif name == "get_class_survey_status":
                return await get_class_survey_status(arguments)
            elif name == "get_coc_notes_memo_status":
                return await get_coc_notes_memo_status(arguments)
            elif name == "get_vessel_dry_docking_status":
                return await get_vessel_dry_docking_status(arguments)
            elif name == "get_next_periodical_survey_details":
                return await get_next_periodical_survey_details(arguments)
            elif name == "get_cms_items_status":
                return await get_cms_items_status(arguments)
            elif name == "get_expired_certificates_from_shippalm":
                return await get_expired_certificates_from_shippalm(arguments)
            elif name == "get_vessel_class_by_imo":
                return await get_vessel_class_by_imo(arguments)

            # Typesense tool handlers
            elif name == "certificate_table_search":
                return await typesense_query(arguments)
            elif name == "get_survey_casefiles":
                return await get_survey_casefiles(arguments)
            elif name == "get_survey_emails":
                return await get_survey_emails(arguments)
            elif name == "list_extended_certificate_records":
                return await list_extended_certificate_records(arguments)
            elif name == "list_records_expiring_within_days":
                return await list_records_expiring_within_days(arguments)
            elif name == "list_records_by_status":
                return await list_records_by_status(arguments)
            
            
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            elif name == "google_search":
                return await google_search(arguments)
            # Document Parsing Tool Handlers
            elif name == "parse_document_link":
                return await parse_document_link(arguments)
            
            # class tool handlers
            elif name == "class_ccs_survey_status_download":
                return await class_ccs_survey_status_download(arguments["vessel_name"])
            elif name == "class_nk_survey_status_download":
                return await class_nk_survey_status_download(arguments["vessel_name"])
            elif name == "class_kr_survey_status_download":
                return await class_kr_survey_status_download(arguments["vessel_name"])
            elif name == "class_dnv_survey_status_download":
                return await class_dnv_survey_status_download(arguments["vessel_name"])
            elif name == "class_lr_survey_status_download":
                return await class_lr_survey_status_download(arguments["vessel_name"])
            elif name == "class_bv_survey_status_download":
                return await class_bv_survey_status_download(arguments["vessel_name"])
            elif name == "class_abs_survey_status_download":
                return await class_abs_survey_status_download(arguments["vessel_name"])
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
    


# ------------------- MongoDB Tool Handlers -------------------

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


async def mongodb_find(arguments: dict):
    """
    Handle MongoDB find tool
    
    Args:
        arguments: Tool arguments including collection name, query, limit, and skip

    Returns:
        List containing the records as TextContent
    """
    collection = arguments.get("collection")
    query = arguments.get("query")
    limit = arguments.get("limit", 10)
    skip = arguments.get("skip", 0)
    projection = arguments.get("projection", {})

    if not collection:
        raise ValueError("Collection name is required")

    try:
        # Execute the query
        mongo_client = MongoDBClient()
        db = mongo_client.db
        collection = db[collection] 
        cursor = collection.find(query, projection=projection, limit=limit, skip=skip)
        documents = [doc async for doc in cursor]

        # Format the results
        formatted_results = {
            "count": len(documents),
            "limit": limit,
            "skip": skip,
            "documents": documents
        }
        
        formatted_text = json.dumps(formatted_results, indent=2)
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

async def vessel_info_search(arguments: dict):
    """
    Handle vessel info search tool
    
    Args:
        arguments: Tool arguments including vessel name

    Returns:
        List containing the records as TextContent
    """
    query = arguments.get("query")
        
    if not query:
        raise ValueError("'query' parameter is required for vessel_info_search")
        
        
    try:
        endpoint = "https://ranking.syia.ai/search"
        headers = {"Content-Type": "application/json"}
        request_data = {"query": query}
        
        logger.info(f"Querying vessel info API with: {query}")
        response = requests.post(endpoint, json=request_data, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        
        if not results:
            return [types.TextContent(
                type="text", 
                text=f"No vessel information found for query: '{query}'"
            )]
        
        # Format the results as JSON
        formatted_text = json.dumps(results, indent=2, default=str)
        
        # Create TextContent
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Vessel information for '{query}'",
            format="json"
        )
        
        return [content]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to vessel info API: {e}")
        return [types.TextContent(
            type="text", 
            text=f"Error connecting to vessel API: {str(e)}"
        )]
    except Exception as e:
        logger.error(f"Error processing vessel information: {e}")
        return [types.TextContent(
            type="text", 
            text=f"Error: {str(e)}"
        )]
    

async def get_user_associated_vessels(arguments: dict):
    """
    Handle get user associated vessels tool
    
    Args:
        arguments: Tool arguments including user ID
        
    Returns:
        List containing vessels associated with the user as TextContent
    """
    user_id = arguments.get("user_id")
    
    if not user_id:
        raise ValueError("User ID is required")
    
    try:
        # MongoDB connection for dev-syia-api
        MONGO_URI_dev_syia_api = r'mongodb://dev-syia:m3BFsUxaPTHhE78@13.202.154.63:27017/?authMechanism=DEFAULT&authSource=dev-syia-api'
        DB_NAME_dev_syia_api = 'dev-syia-api'
        
        # Create connection to dev-syia-api database
        client = MongoClient(MONGO_URI_dev_syia_api)
        db = client[DB_NAME_dev_syia_api]
        
        # Fetch user details from users collection
        user_collection = db["users"]
        user_info = user_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user_info:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "User not found"}, indent=2),
                title=f"Error for user {user_id}",
                format="json"
            )]
        
        # Get associated vessel IDs from user info
        associated_vessel_ids = user_info.get("associatedVessels", [])
        
        # Query the fleet_distributions_overviews collection
        fleet_distributions_overviews_collection = db["fleet_distributions_overviews"]
        vessels = list(fleet_distributions_overviews_collection.find(
            {"vesselId": {"$in": associated_vessel_ids}}, 
            {"_id": 0, "vesselName": 1, "imo": 1}
        ).limit(5))
        
        # Format vessel info
        def format_vessel_info(vessels):
            if not vessels:
                return "No vessels found associated with this user."
            
            formatted_text = [f"- Associated Vessels: {len(vessels)} vessels"]
            
            for i, vessel in enumerate(vessels, 1):
                formatted_text.append(f"{i}. {vessel.get('vesselName', 'Unknown')}")
                formatted_text.append(f"   • IMO: {vessel.get('imo', 'Unknown')}")
            
            return "\n".join(formatted_text)
        
        formatted_text = format_vessel_info(vessels)
        
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Vessels associated with user {user_id}"
        )
        
        return [content]
    except Exception as e:
        logger.error(f"Error retrieving vessels for user {user_id}: {e}")
        raise ValueError(f"Error retrieving associated vessels: {str(e)}")

# ------------------- Survey QnA MongoDB Tool Handlers -------------------

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
    
def fetch_qa_details(imo, questionNo):

    def get_component_data(component_id: str):
        # Parse the component_id into parts
        match = re.match(r"(\d+)_(\d+)_(\d+)", component_id)
        if not match:
            return f"⚠️ Invalid component_id format: {component_id}"

        component_number, question_number, imo = match.groups()
        component_no = f"{component_number}_{question_number}_{imo}"

        # Connect to MongoDB
        MONGO_URI = r'mongodb://syia-etl-dev:SVWvsnr6wAqKG1l@db-etl.prod.syia.ai:27017/?authSource=syia-etl-dev'
        DB_NAME = 'syia-etl-dev'
        client = MongoClient(MONGO_URI)  # update URI as needed
        db = client[DB_NAME]  # replace with actual DB name
        collection = db["vesselinfocomponents"]

        # Fetch document
        doc = collection.find_one({"componentNo": component_no})
        if not doc:
            return f"⚠️ No component found for ID: {component_id}"

        # Extract table data without lineitems
        if "data" in doc and doc['data']:
            headers = [h["name"] for h in doc["data"]["headers"] if h["name"] != "lineitem"] # exclude lineitem
        
            rows = doc["data"]["body"]

            # Build markdown table
            md = "| " + " | ".join(headers) + " |\n"
            md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

            for row in rows:
                formatted_row = []
                for cell in row:
                    if isinstance(cell, dict) and ("value" in cell) and ("link" in cell):
                        # Handle links
                        value = cell["value"]
                        link = cell.get("link")
                        formatted = f"[{value}]({link})" if link else value
                        formatted_row.append(formatted)
                    elif isinstance(cell, dict) and ("status" in cell) and ("color" in cell):
                        formatted_row.append(str(cell["status"]))
                    elif isinstance(cell, dict) and("lineitem" in cell): # exclude lineitem
                        pass
                    else:
                        formatted_row.append(str(cell))
                md += "| " + " | ".join(formatted_row) + " |\n"

            return md
        else:
            return "No data found in the table component"

    def add_component_data(answer: str, imo: int) -> str:
        # Regex pattern to match URLs like 'httpsdev.syia.ai/chat/ag-grid-table?component=10_9'
        pattern = r"httpsdev\.syia\.ai/chat/ag-grid-table\?component=(\d+_\d+)"
        
        # Function to replace matched URL with a get_component_data call
        def replace_link(match):
            component = match.group(1)
            return get_component_data(f"{component}_{imo}")
        
        # Replace all occurrences
        return re.sub(pattern, replace_link, answer)


    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    vesselinfos = db['vesselinfos']
    imo = int(imo)
    query = {
        'imo': imo,
        'questionNo': questionNo
    }
    projection = {
        '_id': 0,  # Optional: exclude MongoDB's default _id field
        'imo': 1,
        'vesselName': 1,
        'refreshDate': 1,
        'answer': 1
    }
    res = vesselinfos.find_one(query, projection)
    if res is None:
        res = {
            'imo': imo,
            'vesselName': None,
            'refreshDate': None,
            'answer': None
        }
    if isinstance(res.get("refreshDate"), datetime):
        datestr = res["refreshDate"].strftime("%-d-%b-%Y")
        res["refreshDate"] = datestr

    if res['answer'] is not None:
        res['answer'] = add_component_data(res['answer'], imo)
    try:
        link = get_vessel_qna_snapshot(str(imo), str(questionNo))
    except Exception:
        link = None
    res['link'] = link
    return res


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

def convert_certificate_dates(document: dict) -> dict:
    """Convert Unix timestamps to human readable format for certificate date fields."""
    date_fields = [
        'issueDate',
        'extensionDate',
        'expiryDate',
        'windowStartDate',
        'windowEndDate'
    ]
    
    for field in date_fields:
        if field in document:
            try:
                document[field] = dt.datetime.fromtimestamp(document[field]).strftime('%Y-%m-%d %H:%M:%S')
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to convert {field}: {e}")
    
    return document



import time

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


{
  "content": "Viewed page: Browser Page",
  "artifacts": [
    {
      "id": "artifact_webpage_1746018877304_994",
      "type": "browser_view",
      "content": {
        "url": "https://example.com",
        "title": "Browser Page",
        "screenshot": "",
        "textContent": "Observed output of cmd `cua` executed:",
        "extractedInfo": {}
      },
      "metadata": {
        "domainName": "example.com",
        "visitTimestamp": 1746018877304,
        "category": "web_page"
      }
    }
  ]
}

async def get_class_survey_report(arguments: dict):
    """
    Handle get class survey report tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the class survey report as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 19)
    
    # Get link and vessel name for MongoDB
    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "class survey report", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Class survey report for IMO {imo}",
        format="json"
    )
    artifact_data = get_artifact("get_class_survey_report", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Class survey report for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_class_certificate_status(arguments: dict):
    """
    Handle get class certificate status tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the class certificate status as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 20)
    context = arguments.get("context", "short")


    
    # Get link and vessel name for MongoDB
    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "class certificate status", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Class certificate status for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_class_certificate_status", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Class certificate status for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_class_survey_status(arguments: dict):
    """
    Handle get class survey status tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the class survey status as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 21)
    
    # Get link and vessel name for MongoDB
    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "class survey status", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Class survey status for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_class_survey_status", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Class survey status for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_coc_notes_memo_status(arguments: dict):
    """
    Handle get CoC notes memo status tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the CoC notes memo status as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 22)
    
    # Get link and vessel name for MongoDB
    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "coc notes memo status", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"CoC notes memo status for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_coc_notes_memo_status", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"CoC notes memo status for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_vessel_dry_docking_status(arguments: dict):
    """
    Handle get vessel dry docking status tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the vessel dry docking status as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 23)
    
    # Get link and vessel name for MongoDB
    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "vessel dry docking status", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Vessel dry docking status for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_vessel_dry_docking_status", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Vessel dry docking status for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_next_periodical_survey_details(arguments: dict):
    """
    Handle get next periodical survey details tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the next periodical survey details as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 24)
    
    # Get link and vessel name for MongoDB
    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "next periodical survey details", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Next periodical survey details for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_next_periodical_survey_details", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Next periodical survey details for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_cms_items_status(arguments: dict):
    """
    Handle get CMS items status tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the CMS items status as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 25)
    
    # Get link and vessel name for MongoDB
    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "cms items status", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"CMS items status for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_cms_items_status", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"CMS items status for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_expired_certificates_from_shippalm(arguments: dict):
    """
    Handle get expired certificates from Ship Palm tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing information about expired certificates from Ship Palm as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 115)
    
    # Get link and vessel name for MongoDB
    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "expired certificates from shippalm", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Expired certificates from Ship Palm for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_expired_certificates_from_shippalm", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Expired certificates from Ship Palm for IMO {imo}",
        format="json"
    )
    return [content, artifact]


# ------------------- Typesense Tool Handlers -------------------

# async def typesense_query(arguments: dict):
#     """
#         Handle Typesense query tool
        
#         Args:
#             arguments: Tool arguments including collection and query parameters
            
#         Returns:
#             List containing the search results as TextContent
#         """
#     collection = arguments.get("collection")
#     query = arguments.get("query", {})
#     if not collection:
#             raise ValueError("Collection name is required")
        
#     try:
#         client = TypesenseClient()
#         results = client.collections[collection].documents.search(query)
#         hits = results.get("hits", [])
#         formatted_hits = []
        
#         for hit in hits:
#             document = hit.get("document", {})
#             # Convert dates if this is a certificate collection query
#             if collection == "certificate":
#                 document = convert_certificate_dates(document)
#             formatted_hits.append(document)
            
#         # Format the results
#         formatted_results = {
#             "found": results.get("found", 0),
#             "out_of": results.get("out_of", 0),
#             "page": results.get("page", 1),
#             "hits": formatted_hits
#         }
        
#         # Convert the results to JSON string
#         formatted_text = json.dumps(formatted_results, indent=2)
        
#         # Create TextContent with all required fields in correct structure
#         content = types.TextContent(
#             type="text",                # Required field
#             text=formatted_text,        # The actual text content
#             title=f"Search results for '{collection}'",
#             format="json"
#         )
        
            
#         return [content]
#     except Exception as e:
#         logger.error(f"Error searching collection {collection}: {e}")
#         raise ValueError(f"Error searching collection: {str(e)}")
    

async def typesense_query(arguments: dict):
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
            if collection == "certificate":
                document = convert_certificate_dates(document)
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
        artifact_data = get_artifact("typesense_query", link)

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
    

async def get_survey_emails(arguments: dict):
    """
    Handle get survey emails tool
    
    Args:
        arguments: Tool arguments including IMO number and lookback hours   
    Returns:
        List containing the records as TextContent
    """
    imo = arguments.get("imo")
    lookbackHours = arguments.get("lookback_hours") or arguments.get("lookbackHours")
    per_page = arguments.get("per_page", 10)
    include_fields = "vesselName,dateTime,subject,importance,casefile,narrative,senderEmailAddress,toRecipientsEmailAddresses,imo,tags"
    tag = arguments.get("tag", "survey")

    if not imo:
        return [types.TextContent(
            type="text",
            text="Error: IMO number is required for survey email search."
        )]
    if not tag:
        return [types.TextContent(
            type="text",
            text="Error: Tag is required for survey email search."
        )]
    try:
        collection = "diary_mails"
        # Build filter_by string
        filter_by = f"imo:{imo} && tags:=[\"{tag}\"]"
        if lookbackHours:
            lookbackHours = int(lookbackHours)
            start_utc = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=lookbackHours)
            start_ts = int(start_utc.timestamp())*1000
            filter_by = f"imo:{imo} && dateTime:>{start_ts} && tags:=[\"{tag}\"]"

        query = {
            "q": "*",
            "filter_by": filter_by,
            "per_page": per_page,
            "include_fields": include_fields,
            "sort_by": "dateTime:desc",
            "prefix": False
        }

        # Execute the search
        logger.info(f"Searching for {tag}-tagged emails for vessel {imo}" + (f" in the last {lookbackHours} hours" if lookbackHours else " (no lookback filter)"))
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)
        
        hits = results.get("hits", [])
        filtered_hits = []
        
        for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size
            document.pop('embedding', None)
            #convert datetime from unix timestamp to human readable format
            document['dateTime'] = dt.datetime.fromtimestamp(document['dateTime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            filtered_hits.append({
                'id': document.get('id'),
                'score': hit.get('text_match', 0),
                'document': document
            })  
        
        # Format the results
        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }   
        
        # Convert the results to JSON string
        formatted_text = json.dumps(formatted_results, indent=2)
        
        # Create TextContent with all required fields in correct structure
        title = f"Survey-related emails for vessel {imo}"
        if lookbackHours:
            title += f" in the last {lookbackHours} hours"
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=title,
            format="json"
        )
        
        return [content]
    except Exception as e:
        logger.error(f"Error retrieving survey-related emails for {imo}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving survey-related emails: {str(e)}"
        )]

async def list_extended_certificate_records(arguments: dict):
    """
    Handle list extended certificate records tool
    Args:
        arguments: Tool arguments including IMO numbers and record types        
    Returns:
        List containing the records as TextContent
    """
    imo = arguments.get("imo")
    record_type = arguments.get("recordType","")
    per_page = arguments.get("per_page", 250)
    session_id = arguments.get("session_id", "testing")
 
    if not imo:
        raise ValueError("IMO number is required")
    
    try:
        collection = "certificate"      
        include_fileds = "imo,vesselName,certificateSurveyEquipmentName,isExtended,issuingAuthority,currentStatus,dataSource,type,issueDate,expiryDate,windowStartDate,windowEndDate,postponedDate,daysToExpiry"
 
        # Build filter_by string
        filter_by = f"imo:{imo} && isExtended:true"
        if record_type:
            # Support both a single string and a list of types
            if isinstance(record_type, list):
                # Join multiple types with comma for Typesense syntax
                types_str = ','.join(record_type)
                filter_by += f" && type:=[{types_str}]"
            else:
                filter_by += f" && type:{record_type}"
 
        query = {
            "q": "*",
            "filter_by": filter_by,
            "include_fields": include_fileds,
            "per_page": per_page
        }  
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)
        # Convert results to JSON string
        hits = results.get("hits", [])
        filtered_hits = []
        
        for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size if it exists
            document.pop('embedding', None)
            # Convert date fields to human readable format
            document = convert_certificate_dates(document)
            filtered_hits.append({
                'id': document.get('id'),
                'score': hit.get('text_match', 0),
                'document': document
            })
        
        # Get documents for data link
        documents = [hit['document'] for hit in filtered_hits]
        
        # Get data link
        data_link = get_data_link(documents)
        
        # Get vessel name from hits
        try:
            vessel_name = hits[0]['document'].get('vesselName', None)
        except:
            vessel_name = None
            
        # Insert the data link to mongodb collection
        link_header = f"extended certificates of type {record_type}" if record_type else "extended certificates (all types)"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
        
        # Format the results
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
        return [content]
    except Exception as e:
        logger.error(f"Error searching collection {collection}: {e}")
        raise ValueError(f"Error searching collection: {str(e)}")

async def list_records_expiring_within_days(arguments: dict):
    """
    Handle list records expiring within days tool
    
    Args:
        arguments: Tool arguments including IMO numbers, record types, and days to expiry

    Returns:
        List containing the records as TextContent
    """
    imo = arguments.get("imo")
    record_type = arguments.get("recordType")
    days_to_expiry = arguments.get("daysToExpiry")
    per_page = arguments.get("per_page", 250)
    session_id = arguments.get("session_id", "testing")

    if not imo or not record_type or not days_to_expiry:
            raise ValueError("IMO numbers, record types, and days to expiry are required")
            
    try:

        # Convert days_to_expiry to integer
        days_to_expiry = int(days_to_expiry)

        # Calculate expiry date as current date plus days_to_expiry
        cutoff_date = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days_to_expiry)
        cutoff_date_ts = int(cutoff_date.timestamp())

        # Format expiry date as YYYY-MM-DD
        collection = "certificate"
        include_fileds = "imo,vesselName,certificateSurveyEquipmentName,isExtended,issuingAuthority,currentStatus,dataSource,type,issueDate,expiryDate,windowStartDate,windowEndDate,postponedDate,daysToExpiry"

        query = {
            "q": "*",
            "filter_by": f"imo:{imo} && type: {record_type} && daysToExpiry:<{cutoff_date_ts}",
            "include_fields": include_fileds,
            "per_page": per_page
        }
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        # Convert results to JSON string
        hits = results.get("hits", [])
        filtered_hits = []
        
        for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size if it exists   
            document.pop('embedding', None)
            # Convert date fields to human readable format
            document = convert_certificate_dates(document)
            filtered_hits.append({
                'id': document.get('id'),
                'score': hit.get('text_match', 0),
                'document': document
            })  
        
        # Get documents for data link
        documents = [hit['document'] for hit in filtered_hits]
        
        # Get data link
        data_link = get_data_link(documents)
        
        # Get vessel name from hits
        try:
            vessel_name = hits[0]['document'].get('vesselName', None)
        except:
            vessel_name = None
            
        # Insert the data link to mongodb collection
        link_header = f"certificates of type {record_type} expiring within {days_to_expiry} days"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
            
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
        
        artifact_data = get_artifact("list_records_expiring_within_days", data_link)

        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Records expiring within {days_to_expiry} days for IMO {imo}",
            format="json"
        )
        return [content, artifact]
    except Exception as e:
        logger.error(f"Error searching collection {collection}: {e}")
        raise ValueError(f"Error searching collection: {str(e)}")
    


async def smart_certificate_search_handler(arguments: dict):
    """
    Handle smart certificate search tool.

    Args:
        arguments: Tool arguments following the smart_certificate_search schema.

    Returns:
        List containing the results and artifacts as TextContent.
    """
    collection = "certificate"
    session_id = arguments.get("session_id", "testing")
    search_type = arguments.get("search_type", "keyword")
    query_text = arguments.get("query", "").strip() or "*"
    filters = arguments.get("filters", {})
    sort_by = arguments.get("sort_by", "relevance")
    sort_order = arguments.get("sort_order", "asc")
    max_results = arguments.get("max_results", 10)

    try:
        # Compose `filter_by` string from filters
        filter_parts = []

        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                if key.endswith("_range"):
                    # Handle range filters
                    field_base = key.replace("_range", "")
                    min_val = value.get("min_days") or value.get("start_date")
                    max_val = value.get("max_days") or value.get("end_date")

                    # Convert date strings to Unix timestamps
                    if isinstance(min_val, str):
                        min_val = int(dt.datetime.strptime(min_val, '%Y-%m-%d').timestamp())
                    if isinstance(max_val, str):
                        max_val = int(dt.datetime.strptime(max_val, '%Y-%m-%d').timestamp())

                    if min_val is not None:
                        filter_parts.append(f"{field_base}:>={min_val}")
                    if max_val is not None:
                        filter_parts.append(f"{field_base}:<={max_val}")
                elif isinstance(value, bool):
                    filter_parts.append(f"{key}:={str(value).lower()}")
                elif isinstance(value, str):
                    filter_parts.append(f"{key}:={json.dumps(value).strip('"')}")
                else:
                    filter_parts.append(f"{key}:={value}")

        filter_by = " && ".join(filter_parts) if filter_parts else None

        # Decide query behavior
        q = "*" if search_type == "browse" else query_text
        query_by = "certificateSurveyEquipmentName,certificateNumber,issuingAuthority"

        # Sort expression
        sort_by_expr = None
        if sort_by != "relevance":
            sort_by_expr = f"{sort_by}:{sort_order}"

        # Fields to return
        include_fields = (
            "imo,vesselName,certificateSurveyEquipmentName,isExtended,issuingAuthority,currentStatus,"
            "dataSource,type,issueDate,expiryDate,windowStartDate,windowEndDate,daysToExpiry,certificateNumber,certificateLink"
        )

        query = {
            "q": q,
            "query_by": query_by,
            "include_fields": include_fields,
            "per_page": max_results,
        }
        if filter_by:
            query["filter_by"] = filter_by
        if sort_by_expr:
            query["sort_by"] = sort_by_expr

        logger.debug(f"[Typesense Query] {query}")

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get('document', {})
            document.pop('embedding', None)
            document = convert_certificate_dates(document)
            filtered_hits.append({
                'id': document.get('id', document.get('_id')),
                'score': hit.get('text_match', 0),
                'document': document
            })
 
        documents = [hit['document'] for hit in filtered_hits]
        data_link = get_data_link(documents)
        vessel_name = hits[0]['document'].get('vesselName') if hits else None
        link_header = f"Smart search result for query: '{query_text}'"
        insert_data_link_to_mongodb(data_link, link_header, session_id, filters.get("imo"), vessel_name)

        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }

        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Search results for '{collection}'",
            format="json"
        )

        artifact_data = get_artifact("smart_certificate_search", data_link)
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Smart certificate search artifact for query '{query_text}'",
            format="json"
        )

        return [content, artifact]

    except Exception as e:
        logger.error(f"Error executing smart certificate search: {e}")
        raise ValueError(f"Error performing smart certificate search: {str(e)}")

async def list_records_by_status(arguments: dict):
    """
    Handle list records by status tool
    
    Args:
        arguments: Tool arguments including IMO numbers, record types, and (optionally) status

    Returns:
        List containing the records as TextContent
    """
    imo = arguments.get("imo")
    record_type = arguments.get("recordType")
    status = arguments.get("status")
    per_page = arguments.get("perPage", 100)
    session_id = arguments.get("session_id", "testing")

    # Only require imo and recordType
    if not imo or not record_type:
        raise ValueError("IMO numbers and record types are required")
        
    try:
        collection = "certificate"
        include_fileds = "imo,vesselName,certificateSurveyEquipmentName,isExtended,issuingAuthority,currentStatus,dataSource,type,issueDate,expiryDate,windowStartDate,windowEndDate,postponedDate,daysToExpiry"
        # Build filter_by string
        filter_by = f"imo:{imo} && type: {record_type}"
        if status:
            filter_by += f" && currentStatus: {status}"
        query = {
            "q": "*",
            "filter_by": filter_by,
            "include_fields": include_fileds,
            "per_page": per_page
        }
        
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)
        # Convert results to JSON string
        hits = results.get("hits", [])
        filtered_hits = []
        
        for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size if it exists
            document.pop('embedding', None)
            # Convert date fields to human readable format
            document = convert_certificate_dates(document)
            filtered_hits.append({
                'id': document.get('id'),
                'score': hit.get('text_match', 0),
                'document': document
            })
        
        # Get documents for data link
        documents = [hit['document'] for hit in filtered_hits]
        
        # Get data link
        data_link = get_data_link(documents)
        
        # Get vessel name from hits
        try:
            vessel_name = hits[0]['document'].get('vesselName', None)
        except:
            vessel_name = None
            
        # Insert the data link to mongodb collection
        link_header = f"certificates of type {record_type}" + (f" with status {status}" if status else "")
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
            
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
        
        artifact_data = get_artifact("list_records_by_status", data_link)

        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Records with status {status} for IMO {imo}" if status else f"Records for IMO {imo}",
            format="json"
        )
        return [content, artifact]
    except Exception as e:
        logger.error(f"Error searching collection {collection}: {e}")
        raise ValueError(f"Error searching collection: {str(e)}")

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

async def get_survey_casefiles(arguments: dict):
    """
    Handle get survey casefiles tool
    
    Args:
        arguments: Tool arguments including IMO numbers and lookback hours

    Returns:
        List containing the records as TextContent
    """
    imo = arguments.get("imo")
    lookback_hours = arguments.get("lookback_hours")
    per_page = arguments.get("per_page", 10)
    query_keyword = arguments.get("query_keyword", "survey")  

    if not imo or not lookback_hours:
        raise ValueError("IMO numbers and lookback hours are required")
    
    try:
        # Convert lookback_hours to integer
        lookback_hours = int(lookback_hours)

        # Calculate cutoff_date as current date-and-time minus lookback_hours
        cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=lookback_hours)
        cutoff_date_ts = int(cutoff_date.timestamp())
        
        collection = "caseFiles"
        include_fields = "vesselName,lastCasefileUpdateDate,subject,importance,casefile,narrative,senderEmailAddress,toRecipientsEmailAddresses,imo,link"

        query = {
            "q": query_keyword,
            "query_by": "embedding",
            "filter_by": f"imo:{imo} && lastCasefileUpdateDate:>{cutoff_date_ts}",
            "per_page": per_page,
            "sort_by": "lastCasefileUpdateDate:desc",
            "include_fields": include_fields,
            "prefix": False
        }
        
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)
        # Convert results to JSON string
        hits = results.get("hits", [])
        filtered_hits = []
        link_data = []
        
        for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size if it exists
            document.pop('embedding', None)
            # Convert date fields to human readable format
            document = convert_casefile_dates(document)
            filtered_hits.append({
                'id': document.get('id'),   
                'score': hit.get('text_match', 0),
                'document': document
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

        artifacts = get_list_of_artifacts("get_survey_casefiles", link_data)
        
        return [content] + artifacts
    except Exception as e:
        logger.error(f"Error searching collection {collection}: {e}")
        raise ValueError(f"Error searching collection: {str(e)}")
        
   
        


  



async def get_vessel_class_by_imo(arguments: dict):
    """
    Fetch the class (classification society) recorded for a vessel.
    The tool looks up the document whose `imo` field matches the supplied IMO number
    in MongoDB database `dev-syia-api`, collection `fleet_distributions_overviews`,
    and returns the value of its `class` field (plus the IMO for reference).
    
    Args:
        arguments: Tool arguments including IMO number
        
    Returns:
        List containing the vessel class information as TextContent
    """
    imo = arguments.get("imo")
    
    if not imo:
        raise ValueError("IMO number is required")
    
    try:
        # MongoDB connection details
        MONGO_URI = "mongodb://dev-syia:m3BFsUxaPTHhE78@13.202.154.63:27017/?authSource=dev-syia-api&directConnection=true"
        DB_NAME = "dev-syia-api"
        COLLECTION = "fleet_distributions_overviews"
        
        # Create MongoDB client
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION]
        
        # Query the collection
        query = {"imo": imo}
        projection = {"_id": 0, "imo": 1, "vesselName": 1, "class": 1}
        
        result = collection.find_one(query, projection)
        
        if not result:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"No vessel found with IMO {imo}"
                }, indent=2),
                title=f"Vessel class lookup for IMO {imo}",
                format="json"
            )]
        
        # Format the response
        response = {
            "imo": result.get("imo"),
            "vesselName": result.get("vesselName"),
            "class": result.get("class")
        }
        
        formatted_text = json.dumps(response, indent=2)
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Vessel class for IMO {imo}",
            format="json"
        )
        
        client.close()  # Close the MongoDB connection
        return [content]
        
    except Exception as e:
        logger.error(f"Error retrieving vessel class for IMO {imo}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": f"Error retrieving vessel class: {str(e)}"
            }, indent=2),
            title=f"Error for IMO {imo}",
            format="json"
        )]
    



async def create_update_casefile(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:

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
    
        # if existing:
        #     casefile_db.update_one(
        #         {"imo": imo, "casefile": casefile},
        #         {"$push": {"pages": new_page, "index": new_index}}
        #     )
        #     return [types.TextContent("Updated an existing entry in database")]
        # else:
        #     casefile_db.insert_one({
        #         "imo": imo,
        #         "vesselName": vessel_name,
        #         "casefile": casefile,
        #         "index": [new_index],
        #         "pages": [new_page]
        #     })
        #     return [types.TextContent("Created new entry in database")]

    except Exception as e:
        logger.error(f"casefile_writer failed: {e}")
        raise


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
    
### Class Tool Handlers
# ------------------- Captcha Solver -------------------

async def _captcha_numbers_solver(captcha_content: bytes) -> str:
    """Solve a captcha image using GPT-4o via LLMClient."""
    
    # Import necessary modules
    import base64
    import json
    from utils.llm import LLMClient
    
    # Initialize LLMClient
    llm_client = LLMClient(openai_api_key=OPENAI_API_KEY)
    
    # Create a prompt for GPT-4o to extract only numbers from the captcha
    prompt = "This is a captcha image containing only numbers. Please extract and return only the numbers you see in the image, nothing else."
    
    try:
        # Convert image to base64 if it's not already
        if isinstance(captcha_content, bytes):
            captcha_base64 = base64.b64encode(captcha_content).decode('utf-8')
        else:
            captcha_base64 = captcha_content
            
        # Create messages with image content for vision model
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{captcha_base64}"
                        }
                    }
                ]
            }
        ]
        
        # Use the chat_completion method directly with the custom messages format
        # This allows us to pass the vision-specific message format
        result = await llm_client.chat_completion(
            messages=messages,
            model_name="gpt-4.1-mini"
        )
        
    except Exception as e:
        logger.error(f"An error occurred while processing the captcha image: {e}")
        raise
    
    # Extract the captcha numbers from the response and trim whitespace
    captcha_numbers = result.strip()
    return captcha_numbers

# Class CCS Automation

async def _class_ccs_automation(vessel_name: str) -> str:
    """Access CCS website to Download Survey Status Report for a vessel and return download path."""
    logger.info(f"Starting CCS automation for vessel: {vessel_name}")
    
    async with async_playwright() as p:
        logger.info("launch browser (visible with frame support)")
        browser = await p.chromium.launch(
            headless=False,
            chromium_sandbox=False,
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            # 1. Go to CCS login page
            logger.info("Going to CCS login page")
            await page.goto("https://www.ccs-service.net/loginNewEn.jsp", timeout=60000)

            # 2. Fill in credentials
            logger.info("Filling in credentials")
            await page.get_by_role("textbox", name="USERNAME").click()
            await page.get_by_role("textbox", name="USERNAME").clear()
            await page.get_by_role("textbox", name="USERNAME").fill("Synergy Maritime")
            await page.get_by_role("textbox", name="PASSWORD").click()
            await page.get_by_role("textbox", name="PASSWORD").clear()
            await page.get_by_role("textbox", name="PASSWORD").fill("Pra92981")
            # Get the captcha image
            logger.info("Getting captcha image")
            captcha_img = page.locator("img#verifi_code[src*='/veriCode/getVerificationCode']")
            # Take a screenshot of the captcha
            captcha_screenshot = await captcha_img.screenshot()
            captcha_base64 = base64.b64encode(captcha_screenshot).decode('utf-8')
            
            # Process the captcha using OpenAI
            while True:
                logger.info("Processing captcha with OpenAI")
                try:
                    captcha_text = await _captcha_numbers_solver(captcha_base64)
                    logger.info(f"Captcha recognized as: {captcha_text}")
                    if len(captcha_text) != 4:
                        continue
                except Exception as e:
                    logger.error(f"Failed to process captcha: {str(e)}")
                    raise
                await page.get_by_role("textbox", name="Verification Code").click()
                await page.get_by_role('textbox', name='Verification Code').clear()
                await page.get_by_role("textbox", name="Verification Code").fill(captcha_text)
                await page.get_by_role("button", name="Login").click()
                # Wait for page to load after login attempt
                logger.info("Waiting for 2 seconds")
                # Wait for 2 seconds to allow the page to process login
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("networkidle")
                logger.info(f"Page URL: {page.url}")
                if page.url == "https://www.ccs-service.net/loginNewEn.jsp":
                    logger.info("Login failed")
                    continue
                else:
                    logger.info("Login successful")
                    break

            # 3. Navigate to 'My Fleet'
            logger.info("Navigating to My Fleet")
            await page.get_by_role("link", name="My Fleet").click();
            time.sleep(2)

            csrf_token = await page.evaluate("document.querySelector('meta[name=\"_csrf\"]')?.getAttribute('content')")
            
            # Get cookies from the page
            cookies = await page.context.cookies()
            setcookie = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            url = "https://www.ccs-service.net/ship/findShipFleetWithPage"
            payload = "name_class_imo_or=&flagId=&shipType=&gross1=&gross2=&rows=20&page=1&sortOrder=asc"
            headers = {
                'Cookie': setcookie,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'x-csrf-token': csrf_token,
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            
            response = requests.post(url, headers=headers, data=payload)
            fleet_data = response.json()
            
            ship_list = fleet_data.get("rows", [])
            
            for ship in ship_list:
                if ship.get("SPNAME") != vessel_name:
                    continue
                ccsno = ship.get("CCSNO")
                
                if ccsno:
                    survey_url = f"https://www.ccs-service.net/ship/surveyInfoTableAll?ccsno={ccsno}&type=all&formCode=SurveyStatus(E,F)&lan=en"
                    
                    survey_response = requests.get(survey_url, headers={'Cookie': setcookie})
                    if survey_response.status_code == 200:
                        file_url = survey_response.text
                        print(file_url)
                        if file_url:
                            # Adding a wait time before attempting to download the file
                            time.sleep(2)
                            retry_count = 0
                            max_retries = 3
                            
                            while retry_count < max_retries:
                                file_response = requests.get(file_url, headers={'Cookie': setcookie}, stream=True)
                                time.sleep(3)
                                try:
                                    if file_response.status_code == 200:
                                        file = file_response.content
                                        downloads_dir = Path("downloads/CCS")
                                        downloads_dir.mkdir(exist_ok=True, parents=True)
                                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                                        download_path = downloads_dir / f"{vessel_name.replace(' ', '_')}_CCS_{timestamp}.pdf"
                                        with open(download_path, "wb") as f:
                                            f.write(file)
                                        logger.info(f"Download successful: {download_path}")
                                        return str(download_path.resolve())
                                except Exception as e:
                                    print(f"Error uploading to S3: {str(e)}")
                                    retry_count += 1
                                    time.sleep(5)
        except Exception as e:
            logger.error(f"Error during CCS automation: {str(e)}")
            error_path = f"debug_ccs_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=error_path)
            logger.error(f"Error screenshot saved to: {error_path}")
            raise
        finally:
            await context.close()
            await browser.close()

async def class_ccs_survey_status_download(vessel_name: str) -> str:
    try:
        pdf_path = await _class_ccs_automation(vessel_name)
        formatted_results = {"download_path": pdf_path}
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Download Path for {vessel_name}",
            format="json"
            )
        return [content]
    except Exception as e:
        logger.error(f"Failed to download CCS Ship Status PDF: {str(e)}")
        return [
            types.TextContent(
                type="text", 
                text=f"Error: {str(e)}"
            )
        ]

# Class NK Automation

async def _class_nk_automation(vessel_name: str) -> str:
    """Access NK website to Download Survey Status Report for a vessel and return download path."""
    logger.info(f"Starting NK automation for vessel: {vessel_name}")
    
    async with async_playwright() as p:
        logger.info("launch browser (visible with frame support)")
        browser = await p.chromium.launch(
            headless=False,
            chromium_sandbox=False,
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            # 1. Go to NK portal login page
            logger.info("Going to NK portal login page")
            await page.goto("https://portal.classnk.or.jp/portal/", timeout=60000)

            # 2. Fill in credentials
            logger.info("Filling in credentials")
            await page.locator('#UserID').click()
            await page.locator('#UserID').fill("sy0069")  # TODO: Replace with real user ID
            await page.locator('#pwd').click()
            await page.locator('#pwd').fill("NKKchennai1")  # TODO: Replace with real password

            # Get the captcha image
            logger.info("Getting captcha image")
            captcha_img = page.locator("#authImage")
            # Take a screenshot of the captcha
            captcha_screenshot = await captcha_img.screenshot()
            captcha_base64 = base64.b64encode(captcha_screenshot).decode('utf-8')

            # Process the captcha using OpenAI
            while True:
                logger.info("Processing captcha with OpenAI")
                try:
                    captcha_text = await _captcha_numbers_solver(captcha_base64)
                    logger.info(f"Captcha recognized as: {captcha_text}")
                    if len(captcha_text) != 4:
                        continue
                except Exception as e:
                    logger.error(f"Failed to process captcha: {str(e)}")
                    raise
                await page.locator('#authImageString').click()
                await page.locator('#authImageString').fill(captcha_text)
                await page.get_by_role('button', name='Submit').click()

                # Wait for page to load after login attempt
                logger.info("Waiting for 2 seconds")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("networkidle")
                if page.get_by_role('link', name='NK-SHIPS').is_visible():
                    logger.info("Login successful")
                    break
                else:
                    logger.info("Login failed")
                    continue

            # 3. Click NK-SHIPS link (opens popup)
            logger.info("Clicking NK-SHIPS link and waiting for popup")
            async with page.expect_popup() as page1_info:
                await page.get_by_role('link', name='NK-SHIPS').click()
            page1 = await page1_info.value
            # page1_promise = page.wait_for_event('popup')
            # page1 = await page1_promise

            # 4. In popup, click List of ships>>
            logger.info("Clicking List of ships>> in popup")
            await page1.get_by_role('link', name='List of ships>>').click()

            # Wait for the page to load
            await page1.wait_for_selector("table.list_row3", timeout=20000)
            
            # Wait for the pagination selector
            await page1.wait_for_selector("#gotoSelectPage", timeout=20000)
            
            # Extract max page number (e.g. from "1 / 4")
            pagination_text = await page1.locator("input[name='PageDownButton']").locator("..").inner_text()
            match = re.search(r'/\s*(\d+)', pagination_text)
            total_pages = int(match.group(1)) if match else 1
            
            for current_page in range(1, total_pages + 1):
                logger.info(f"Checking page {current_page}")
                time.sleep(1)
                logger.info(f"vessel name: ' {vessel_name} '")
                locator = page1.get_by_text(f' {vessel_name} ')
                if await locator.count() > 0:
                    logger.info(f"Found vessel {vessel_name} on page {current_page}")
                    await locator.click()
                    logger.info("Clicking specific image in table")
                    await page1.locator('td > table > tbody > tr > td:nth-child(2) > img:nth-child(5)').click()
                    # 8. Click #clsdbAll
                    logger.info("Clicking #clsdbAll")
                    await page1.locator('#clsdbAll').click()

                    # 9. Click Print Out to trigger download
                    logger.info("Clicking Print Out to trigger download")
                    download_promise = page1.wait_for_event('download')
                    await page1.get_by_role('button', name='Print Out').first.click()
                    download = await download_promise
                    break
                else:
                    logger.info(f"Vessel {vessel_name} not found on page {current_page}")
                    # Navigate to the specific page
                    await page1.locator("#gotoSelectPage").click()
                    await page1.locator("#gotoSelectPage").fill(str(current_page))
                    await page1.locator("#gotoSelectPage").press("Enter")
                    
                    # Wait for the page to load - increased timeout and added more robust checks
                    await page1.wait_for_timeout(3000)  # Increased timeout for page load
                    continue

            # Save the file
            downloads_dir = Path("downloads/NK")
            downloads_dir.mkdir(exist_ok=True, parents=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            download_path = downloads_dir / f"{vessel_name.replace(' ', '_')}_NK_{timestamp}.pdf"
            await download.save_as(download_path)
            logger.info(f"Download successful: {download_path}")
            return str(download_path.resolve())
        except Exception as e:
            logger.error(f"Error during NK automation: {str(e)}")
            error_path = f"debug_nk_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=error_path)
            logger.error(f"Error screenshot saved to: {error_path}")
            raise
        finally:
            await context.close()
            await browser.close()

async def class_nk_survey_status_download(vessel_name: str) -> str:
    try:
        pdf_path = await _class_nk_automation(vessel_name)
        formatted_results = {"download_path": pdf_path}
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Download Path for {vessel_name}",
            format="json"
            )
        return [content]
    except Exception as e:
        logger.error(f"Failed to download NK Ship Status PDF: {str(e)}")
        return [
            types.TextContent(
                type="text", 
                text=f"Error: {str(e)}"
            )
        ]

# Class KR Automation

async def _class_kr_automation(vessel_name: str) -> str:
    """Access KR website to Download Survey Status Report for a vessel and return download path."""
    logger.info(f"Starting KR automation for vessel: {vessel_name}")
    
    async with async_playwright() as p:
        logger.info("launch browser (visible with frame support)")
        browser = await p.chromium.launch(
            headless=False,
            chromium_sandbox=False,
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            # 1. Go to KR login page
            logger.info("Going to KR login page")
            await page.goto("https://e-fleet.krs.co.kr/View/Login/CheckMember_New_V2.aspx", timeout=60000)

            # 2. Fill in credentials
            logger.info("Filling in credentials")
            await page.locator('#ctl00_MainContent_txtUser_Id').click()
            await page.locator('#ctl00_MainContent_txtUser_Id').fill("synergy")  # TODO: Replace with real user ID
            await page.locator('#ctl00_MainContent_txtPassword').click()
            await page.locator('#ctl00_MainContent_txtPassword').fill("KRchennai1")  # TODO: Replace with real password

            # 3. Click Sign In and wait for popup
            logger.info("Clicking Sign In and waiting for popup")
            page1_promise = page.wait_for_event('popup')
            await page.get_by_role('button', name='Sign In').click()
            page1 = await page1_promise

            
            # 4. In popup, handle additional sign-ins
            logger.info("Handling additional sign-ins in popup")
            await page1.get_by_role('button', name='Sign In (Close)').click()
            await page1.get_by_role('textbox', name='id@hostname.com').click()
            await page1.get_by_role('textbox', name='id@hostname.com').fill('sp_vg@synergyship.com')
            await page1.get_by_role('textbox', name='Enter your password').click()
            await page1.get_by_role('textbox', name='Enter your password').fill('Synergy@123')
            await page1.get_by_role('button', name='Sign in').click()

            # 5. Click e-Fleet and wait for popup
            logger.info("Clicking e-Fleet and waiting for popup")
            page2_promise = page1.wait_for_event('popup')
            await page1.locator('a').filter(has_text='e-Fleet').click()
            page2 = await page2_promise

            # 6. In new popup, search for vessel
            logger.info("Navigating to VESSEL and searching for vessel")
            await page2.get_by_role('link', name='VESSEL').click()
            await page2.locator('#search_kind').select_option('S')
            await page2.get_by_role('textbox', name='Search').click()
            await page2.get_by_role('textbox', name='Search').fill(vessel_name)
            await page2.get_by_role('button', name='').click()
            cookies = await context.cookies()
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            print(f"Extracted cookies")
            time.sleep(2)

            # Use the extracted cookie to get vessel details
            vessel_url = "https://e-fleet.krs.co.kr/View/VESSEL/DataHandler/Vessel_List.ashx"
            headers = {
                'Cookie': cookie_string
            }

            response = requests.get(vessel_url, headers=headers)
            response.raise_for_status()

            response_data = response.json()

            for vessel in response_data:
                time.sleep(2)
                shipname = vessel.get('SHIPNAME')
                if shipname != vessel_name:
                    continue
                class_no = vessel.get('CLASS')
                
                file_url = f"https://e-fleet.krs.co.kr/View/eShip/PopUp/FileDownPage2.aspx?ClassNo={class_no}&CMS=Y&RECMD=Y&NOTE=Y&CHS=Y&AUDIT=Y"
                headers = {
                    'Cookie': cookie_string
                }
                file_response = requests.get(file_url, headers=headers)
                file_response.raise_for_status()
                file = file_response.content
                logger.info(f"File content: {len(file)}")
                if file_response.status_code == 200:
                    downloads_dir = Path("downloads/KR")
                    downloads_dir.mkdir(exist_ok=True, parents=True)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    download_path = downloads_dir / f"{vessel_name.replace(' ', '_')}_KR_{timestamp}.pdf"
                    with open(download_path, "wb") as f:
                        f.write(file)
                    logger.info(f"Download successful: {download_path}")
                    return str(download_path.resolve())
        except Exception as e:
            logger.error(f"Error during KR automation: {str(e)}")
            error_path = f"debug_kr_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=error_path)
            logger.error(f"Error screenshot saved to: {error_path}")
            raise
        finally:
            await context.close()
            await browser.close()

async def class_kr_survey_status_download(vessel_name: str) -> str:
    try:
        pdf_path = await _class_kr_automation(vessel_name)
        formatted_results = {"download_path": pdf_path}
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Download Path for {vessel_name}",
            format="json"
            )
        return [content]
    except Exception as e:
        logger.error(f"Failed to download KR Ship Status PDF: {str(e)}")
        return [
            types.TextContent(
                type="text", 
                text=f"Error: {str(e)}"
            )
        ]

# Class DNV Automation

async def _class_dnv_automation(vessel_name: str) -> str:
    """Access DNV website to Download Survey Status Report for a vessel and return download path."""
    logger.info(f"Starting DNV automation for vessel: {vessel_name}")
    
    async with async_playwright() as p:
        logger.info("launch browser (visible with frame support)")
        browser = await p.chromium.launch(
            headless=False,
            chromium_sandbox=False,
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            # 1. Go to DNV login page
            logger.info("Going to DNV login page")
            await page.goto("https://www.veracity.com/auth/login", timeout=60000)

            # 2. Click Sign in
            logger.info("Clicking Sign in link")
            await page.get_by_role('link', name='Sign in').click()

            # 3. Fill in credentials
            logger.info("Filling in credentials")
            await page.get_by_role('textbox', name='Email address or username').click()
            await page.get_by_role('textbox', name='Email address or username').fill('SYNERGY1')  # TODO: Replace with real username
            await page.get_by_role('button', name='Continue').click()
            await page.get_by_role('textbox', name='Password').click()
            await page.get_by_role('textbox', name='Password').fill('Marine123')  # TODO: Replace with real password
            await page.get_by_role('button', name='Log in').click()

            # 4. Go to My services
            logger.info("Navigating to My services")
            await page.get_by_role('link', name='My services').click()

            # 5. Click Fleet Status (opens popup)
            logger.info("Clicking Fleet Status and waiting for popup")
            page1_promise = page.wait_for_event('popup')
            await page.get_by_role('link', name='Fleet Status', exact=True).click()
            page1 = await page1_promise

            # 6. In popup, go to Fleet page
            logger.info("Navigating to Fleet page in popup")
            await page1.goto('https://maritime.dnv.com/Fleet')

            # 7. Accept cookies
            logger.info("Accepting cookies")
            await page1.get_by_role('button', name='Accept All Cookies').click()

            # 8. Go to Vessel list
            logger.info("Navigating to Vessel list")
            await page1.get_by_role('link', name='Vessel list').click()

            # 9. Click vessel link
            logger.info(f"Clicking vessel link: {vessel_name}")
            await page1.get_by_role('link', name=vessel_name).click()

            # 10. Export to Excel (optional, as in JS)
            logger.info("Clicking export to Excel")
            await page1.locator('#exportToExcel').click()

            # 11. Click status div (optional, as in JS)
            logger.info("Clicking status div")
            await page1.locator('#layoutCompanyPageContent div').filter(has_text='In DNV Class In Operation').first.click()

            # 12. Open menu and download class status report
            logger.info("Opening menu and clicking Download class status report")
            await page1.get_by_role('button', name='Menu ').click()
            await page1.locator('#megaMenu').get_by_text('Download class status report').click()

            # 13. Download with Memorandum to Owner
            logger.info("Clicking With Memorandum to Owner and waiting for download")
            download_promise = page1.wait_for_event('download')
            await page1.get_by_role('button', name='With Memorandum to Owner').click()
            download = await download_promise

            # Save the file
            downloads_dir = Path("downloads/DNV")
            downloads_dir.mkdir(exist_ok=True, parents=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            download_path = downloads_dir / f"{vessel_name.replace(' ', '_')}_DNV_{timestamp}.pdf"
            await download.save_as(download_path)
            logger.info(f"Download successful: {download_path}")
            return str(download_path.resolve())
        except Exception as e:
            logger.error(f"Error during DNV automation: {str(e)}")
            error_path = f"debug_dnv_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=error_path)
            logger.error(f"Error screenshot saved to: {error_path}")
            raise
        finally:
            await context.close()
            await browser.close()

async def class_dnv_survey_status_download(vessel_name: str) -> str:
    try:
        pdf_path = await _class_dnv_automation(vessel_name)
        formatted_results = {"download_path": pdf_path}
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Download Path for {vessel_name}",
            format="json"
            )
        return [content]
    except Exception as e:
        logger.error(f"Failed to download DNV Ship Status PDF: {str(e)}")
        return [
            types.TextContent(
                type="text", 
                text=f"Error: {str(e)}"
            )
        ]
    
# Class LR Automation

async def _class_lr_automation(vessel_name: str) -> str:
    """Automate LR website to download Survey Status for a vessel."""
    logger.info(f"Starting LR automation for vessel: {vessel_name}")
    
    async with async_playwright() as p:
        logger.info("launch browser (visible with frame support)")
        browser = await p.chromium.launch(
            headless=False,
            chromium_sandbox=False,
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            # 1. Go to LR login page
            logger.info("Going to LR login page")
            await page.goto("https://www.lr.org/en/client-support/sign-in-client-portal/", timeout=60000)

            # 2. Accept cookies
            logger.info("Accepting cookies")
            await page.get_by_role('button', name='Allow all').click()

            # 3. Click Login and wait for popup
            logger.info("Clicking Login and waiting for popup")
            page1_promise = page.wait_for_event('popup')
            await page.get_by_role('link', name='Login').nth(1).click()
            page1 = await page1_promise

            # 4. Go to login URL
            logger.info("Navigating to login URL in popup")

            # 5. Fill in credentials
            logger.info("Filling in credentials")
            await page1.get_by_role('textbox', name='Email').click()
            await page1.get_by_role('textbox', name='Email').fill('rohan.p@synergyship.com')  # TODO: Replace with real email
            await page1.get_by_role('button', name='Continue').click()
            await page1.get_by_role('textbox', name='Enter User password').click()
            await page1.get_by_role('textbox', name='Enter User password').fill('Synergy123$')  # TODO: Replace with real password
            await page1.get_by_role('button', name='Continue').click()

            # 6. Click Fleet
            logger.info("Clicking Fleet")
            await page1.get_by_role('button', name='Fleet').click()

            # 7. Click LR Class Direct and wait for popup
            logger.info("Clicking LR Class Direct and waiting for popup")
            page2_promise = page1.wait_for_event('popup')
            await page1.get_by_role('link', name='LR Class Direct').click()
            page2 = await page2_promise

            # 8. Search for vessel
            logger.info(f"Searching for vessel: {vessel_name}")
            await page2.get_by_role('textbox', name='Type here to search').click()
            await page2.get_by_role('textbox', name='Type here to search').fill(vessel_name)
            await page2.get_by_role('textbox', name='Type here to search').press('Enter')

            # 10. Click Survey Status Report and Add all
            logger.info("Clicking Survey Status Report and Add all")
            await page2.get_by_role('button', name='Survey Status Report').click()
            await page2.get_by_role('button', name='Add all').click()

            # 11. Click Survey Status Report to trigger download
            logger.info("Clicking Survey Status Report to trigger download")
            download_promise = page2.wait_for_event('download')
            await page2.get_by_role('button', name='Survey Status Report').click()
            download = await download_promise

            # Save the file
            downloads_dir = Path("downloads/LR")
            downloads_dir.mkdir(exist_ok=True, parents=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            download_path = downloads_dir / f"{vessel_name.replace(' ', '_')}_LR_{timestamp}.pdf"
            await download.save_as(download_path)
            logger.info(f"Download successful: {download_path}")
            return str(download_path.resolve())
        except Exception as e:
            logger.error(f"Error during LR automation: {str(e)}")
            error_path = f"debug_lr_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=error_path)
            logger.error(f"Error screenshot saved to: {error_path}")
            raise
        finally:
            await context.close()
            await browser.close()

async def class_lr_survey_status_download(vessel_name: str) -> str:
    try:
        pdf_path = await _class_lr_automation(vessel_name)
        formatted_results = {"download_path": pdf_path}
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Download Path for {vessel_name}",
            format="json"
            )
        return [content]
    except Exception as e:
        logger.error(f"Failed to download LR Ship Status PDF: {str(e)}")
        return [
            types.TextContent(
                type="text", 
                text=f"Error: {str(e)}"
            )
        ]
# Class BV Automation

async def _class_bv_automation(vessel_name: str) -> str:
    """Download vessel Ship Status PDF from Bureau Veritas."""
    logger.info(f"Starting Bureau Veritas automation for vessel: {vessel_name}")
    
    async with async_playwright() as p:
        logger.info("launch browser (visible with frame support)")
        # Configure browser to work with frame display
        browser = await p.chromium.launch(
            headless=False,  # Keep visible
            chromium_sandbox=False,  # May help with frame display
        )
        # Set explicit viewport size for better frame display
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        try:
            # 1. Go to BV website and login
            logger.info("Going to BV website")
            await page.goto("https://move.bureauveritas.com/#/cms", timeout=60000)
            
            # Click Connect Now
            logger.info("Clicking Connect Now")
            await page.get_by_role("button", name="Connect Now").click()
            await sleep(2)
            
            # Enter credentials
            logger.info("Entering login credentials")
            await page.get_by_role("textbox", name="Username").fill("survey@synergyship.com")
            await page.get_by_role("textbox", name="Password").fill("BVchennai1")
            await page.get_by_role("button", name="Sign In").click()
            
            # Wait for login to complete
            await page.wait_for_load_state("networkidle", timeout=60000)
            logger.info("Login successful")
            
            # 2. Navigate to Fleet in Service
            logger.info("Navigating to Fleet in Service")
            await page.get_by_text("FLEET IN SERVICE Monitor the").click()
            await sleep(2)

            # 3. Click the vessel and download the PDF
            logger.info("Clicking the vessel and downloading the PDF")
            await page.get_by_label('Fleet Info').get_by_text(vessel_name, exact=True).click();
            await page.get_by_role('button', name='Download Ship Status PDF').click();
            downloadPromise = page.wait_for_event('download');
            await page.get_by_role('button', name='Download PDF').click();
            download = await downloadPromise;
            
            # Create downloads directory if it doesn't exist
            downloads_dir = Path("downloads/BV")
            downloads_dir.mkdir(exist_ok=True, parents=True)
            
            # Save the file with a descriptive filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            download_path = downloads_dir / f"{vessel_name.replace(' ', '_')}_BV_{timestamp}.pdf"
            await download.save_as(download_path)
            
            logger.info(f"Download successful: {download_path}")
            return str(download_path.resolve())
            
        except Exception as e:
            logger.error(f"Error during BV automation: {str(e)}")
            # Take error state screenshot
            error_path = f"debug_bv_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=error_path)
            logger.error(f"Error screenshot saved to: {error_path}")
            raise
        
        finally:
            await context.close()
            await browser.close()

async def class_bv_survey_status_download(vessel_name: str) -> str:
    try:
        pdf_path = await _class_bv_automation(vessel_name)
        formatted_results = {"download_path": pdf_path}
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Download Path for {vessel_name}",
            format="json"
            )
        return [content]
    except Exception as e:
        logger.error(f"Failed to download BV Ship Status PDF: {str(e)}")
        return [
            types.TextContent(
                type="text", 
                text=f"Error: {str(e)}"
            )
        ]

# Class ABS Automation

async def _class_abs_automation(vessel_name: str) -> str:
    """Download vessel Ship Status PDF from ABS."""
    logger.info(f"Starting ABS automation for vessel: {vessel_name}")
    
    async with async_playwright() as p:
        logger.info("launch browser (visible with frame support)")
        browser = await p.chromium.launch(
            headless=False,
            chromium_sandbox=False,
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            # 1. Go to ABS login page
            logger.info("Going to ABS login page")
            await page.goto('https://ww2.eagle.org/en.html');
            await page.wait_for_load_state("networkidle")
            await page.get_by_role('link', name='Login Login').click();
            
            # 2. Login
            logger.info("Filling in credentials")
            await page.get_by_role("textbox", name="Username").click()
            await page.get_by_role("textbox", name="Username").fill("synergyship")
            await page.get_by_role("textbox", name="Password").click()
            await page.get_by_role("textbox", name="Password").fill("abschennai1")
            await page.get_by_role("button", name="LOG IN", exact=True).click()
            time.sleep(40)
            # Check for popup and close it if present
            logger.info("Checking for popup and closing if present")
            try:
                popup_close_button = page.locator('span[aria-label="Close"][role="button"]')
                if await popup_close_button.count() > 0:
                    logger.info("Found popup, attempting to close it")
                    await popup_close_button.click()
                    logger.info("Popup closed successfully")
                    time.sleep(20)
                else:
                    logger.info("No popup detected")
                    time.sleep(10)
            except Exception as popup_error:
                logger.warning(f"Error handling popup: {str(popup_error)}")
            

            # 3. Go to dashboard
            logger.info("Navigating to dashboard")
            await page.goto("https://www.eagle.org/portal/#/portal/dashboard", timeout=100000)
            time.sleep(5)
            

            
            # 4. Go to Vessels
            logger.info("Clicking Vessels tab")
            await page.get_by_text("Fleet", exact=True).first.click();
            await page.get_by_text("Vessels", exact=True).click()
            
            # 5. Search and select vessel
            await page.get_by_text('Clear All').click();
            logger.info(f"Selecting vessel: {vessel_name}")
            await page.get_by_role('textbox', name='Search').click();
            await page.get_by_role('textbox', name='Search').fill(vessel_name);
            await page.get_by_role('textbox', name='Search').press('Enter');
            await page.get_by_text(vessel_name).click()
            
            # 6. Download Vessel Status
            logger.info("Clicking file_download Vessel Status")
            await page.get_by_role("button", name="file_download Vessel Status").click()
            await page.get_by_text('With Asset').click();
            await page.get_by_text('With Compartments - Conditions').click();
            
            # 7. Generate and download report
            logger.info("Generating and downloading report")
            async with page.expect_download() as download_info:
                await page.get_by_text("file_downloadGenerate Report").click()
                await page.locator('[data-test="modal-footer"] [data-test="button"]').click();
            download = await download_info.value
            logger.info(f"Downloaded file: {download.path()}")
            
            # Create downloads directory if it doesn't exist
            downloads_dir = Path("downloads/ABS")
            downloads_dir.mkdir(exist_ok=True, parents=True)
            
            # Save the file with a descriptive filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            download_path = downloads_dir / f"{vessel_name.replace(' ', '_')}_ABS_{timestamp}.pdf"
            await download.save_as(download_path)
            
            logger.info(f"Download successful: {download_path}")
            return str(download_path.resolve())
        except Exception as e:
            logger.error(f"Error during ABS automation: {str(e)}")
            # Take error state screenshot
            error_path = f"debug_abs_error_{time.strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=error_path)
            logger.error(f"Error screenshot saved to: {error_path}")
            raise
        finally:
            await context.close()
            await browser.close()

async def class_abs_survey_status_download(vessel_name: str) -> str:
    try:
        pdf_path = await _class_abs_automation(vessel_name)
        formatted_results = {"download_path": pdf_path}
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=f"Download Path for {vessel_name}",
            format="json"
            )
        return [content]
    except Exception as e:
        logger.error(f"Failed to download ABS Ship Status PDF: {str(e)}")
        return [
            types.TextContent(
                type="text", 
                text=f"Error: {str(e)}"
            )
        ]

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


def push_to_typesense(document: dict, action: str):
    """Upsert or create a Typesense document and sync the MongoDB link."""
    casefile_id = document["id"]
    link = generate_casefile_weblink(casefile_id)
    # Update MongoDB link
    mongo = MongoDBClient()
    mongo.db[COLLECTION_NAME].update_one(
        {"_id": ObjectId(casefile_id)},
        {"$set": {"link": link}}
    )
    # Prepare payload
    payload = {
        **document,
        "link": link,
        "importance": convert_importance(document.get("importance"))
    }
    # Import into Typesense
    ts = TypesenseClient()
    result = ts.collections[TYPESENSE_COLLECTION].documents.import_(
        [payload],
        {"action": action}
    )
    logger.info(f"Typesense import result: {result}")
    return result

async def get_vessel_name(imo: Union[str, int]):
    """Fetch vessel name and ID by IMO from MongoDB."""
    client = MongoDBClient()
    vessel = await client.db["vessels"].find_one({"imo": imo})
    if vessel:
        return vessel.get("name"), vessel.get("_id")
    return None, None


def link_to_id(casefile_url: str) -> str:
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
    category = arguments.get("category","General")
    role = arguments.get("role",None)
    imo = arguments.get("imo",None)

    if imo:
        vessel_name,vessel_id = await get_vessel_name(imo)
    else:
        vessel_name = None
        vessel_id = None

    client = MongoDBClient()
    collection = client.db[COLLECTION_NAME]
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
    logger.info(result)
    
    casefile_id = str(result.inserted_id)
    casefile_url = generate_casefile_weblink(casefile_id)
    await collection.update_one({"_id": ObjectId(casefile_id)}, {"$set": {"link": casefile_url}})


    ## synergy core update
    # synergy_core_client = SynergyMongoDBClient()
    # synergy_collection = synergy_core_client.db["casefiles"]
    # data['_id'] = ObjectId(casefile_id)
    # await synergy_collection.insert_one(data)


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
    collection = client.db[COLLECTION_NAME]

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
            "pages": str(mongoresult.get("pages",[])[-2:]),
            "index": str(mongoresult.get("index",[])[-2:])
            
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
    category = arguments.get("category","classSurveyAndCertificateStatus")
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
 
