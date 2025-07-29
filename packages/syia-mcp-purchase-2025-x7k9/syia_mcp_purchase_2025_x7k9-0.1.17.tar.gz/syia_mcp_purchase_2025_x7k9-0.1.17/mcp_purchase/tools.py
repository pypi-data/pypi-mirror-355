from asyncio import sleep
from mcp_purchase.databases import *
import json
from typing import Dict, Any, TypedDict
from enum import Enum
from typing import Union, Sequence, Optional
import mcp.types as types
import datetime as dt
from mcp_purchase import mcp, logger
import requests
from mcp_purchase.tool_schema import tool_definitions
from pathlib import Path   
from playwright.async_api import async_playwright
from mcp_purchase.utils import timestamped_filename
from dotenv import load_dotenv
import os   
import re
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import time

import os
import time
import json
import requests
from datetime import datetime, timezone, UTC
from typing import Dict, Any, List, Union
from pymongo import MongoClient
from . import logger
from typing import Dict, Any, List, Union, Optional
import mcp.types as types # Assumes types.TextContent is defined or imported elsewhere

from typing import Dict, Any
import openai
import json

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

from .constants import LLAMA_API_KEY, VENDOR_MODEL, PERPLEXITY_API_KEY

import os

import re
import requests

from .constants import MONGODB_URI, MONGODB_DB_NAME, OPENAI_API_KEY

from utils.llm import LLMClient
from document_parse.main_file_s3_to_llamaparse import parse_to_document_link

import difflib
# import aiohttp
import httpx


# import for casefile update 

from bson import ObjectId
from .databases import MongoDBClient, TypesenseClient
from .generate_mail_html import MailBodyLinkGenerator
from . import logger
from .html_link_from_md import markdown_to_html_link

MONGO_URI = r'mongodb://syia-etl-dev:SVWvsnr6wAqKG1l@db-etl.prod.syia.ai:27017/?authSource=syia-etl-dev'
DB_NAME = 'syia-etl-dev'

server_tools = tool_definitions

async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        try:
            # MongoDB tool handlers
            if name == "get_purchase_budget_expense_table_schema":
                return await get_typesense_schema(arguments)
            elif name == "mongodb_find":
                return await mongodb_find(arguments)
            elif name == "vessel_info_search":
                return await vessel_info_search(arguments)
            elif name == "get_monthly_opex_budget_variance":
                return await get_monthly_opex_budget_variance(arguments)
            elif name == "get_current_year_commited_cost":
                return await get_current_year_commited_cost(arguments)
            elif name == "get_budget_status_summary_ytd":
                return await get_budget_status_summary_ytd(arguments)
            elif name == "get_vessel_eta_from_email":
                return await get_vessel_eta_from_email(arguments)
            elif name == "get_purchase_orders_with_forwarders":
                return await get_purchase_orders_with_forwarders(arguments)
            elif name == "purchase_orders_open_more_than_180_days":
                return await purchase_orders_open_more_than_180_days(arguments)
            elif name == "get_user_associated_vessels":
                return await get_user_associated_vessels(arguments)
            elif name == "get_vessel_budget_data":
                return await get_vessel_budget_data(arguments)
         
            
            # Typesense tool handlers
            elif name == "budget_expense_table_search":
                return await typesense_query(arguments)
            elif name == "smart_purchase_table_search":
                return await smart_purchase_table_search_handler(arguments)
            elif name == "smart_budget_search":
                return await smart_budget_search_handler(arguments)
            elif name == "smart_expense_search":
                return await smart_expense_search_handler(arguments)
            elif name == "list_recent_vessel_purchase_requisitions":
                return await list_recent_vessel_purchase_requisitions(arguments)
            elif name == "get_purchase_emails":
                return await get_purchase_emails(arguments)
            elif name == "get_purchase_casefiles":
                return await get_purchase_casefiles(arguments)
            elif name == "get_purchase_requisition_details":
                return await get_purchase_requisition_details(arguments)
            elif name == "get_purchase_order_details":
                return await get_purchase_order_details(arguments)
            elif name == "list_requisitions_by_status":
                return await list_requisitions_by_status(arguments)
            elif name == "get_vessel_details":
                return await get_vessel_details(arguments)
            elif name == "list_overdue_open_requisitions":
                return await list_overdue_open_requisitions(arguments)
            elif name == "list_purchase_orders_by_status":
                return await list_purchase_orders_by_status(arguments)
            elif name == "list_requisitions_by_type_and_stage":
                return await list_requisitions_by_type_and_stage(arguments)
            elif name == "list_recent_requisitions_by_order_priority":
                return await list_recent_requisitions_by_order_priority(arguments)
            elif name == "list_top_expenses_by_category":
                return await list_top_expenses_by_category(arguments)
            elif name == "list_committed_cost_expenses":
                return await list_committed_cost_expenses(arguments)
            elif name == "get_vessel_purchase_log_table":
                return await get_vessel_purchase_log_table(arguments)
            elif name == "list_recent_urgent_requisitions":
                return await list_recent_urgent_requisitions(arguments)

            # Document Parsing Tool Handlers
            elif name == "parse_document_link":
                return await parse_document_link(arguments)
              
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            elif name == "google_search":
                return await google_search(arguments)
            
                        # Vendor tool handlers
            elif name == "find_relevant_vendors":
                return await vendor_search(arguments)
            elif name == "get_vendor_contact_details":
                return await get_vendor_contact_info(arguments)
            
            elif name == "write_casefile_data":
                return await write_casefile_data(arguments)
            
            elif name == "retrieve_casefile_data":
                if arguments.get("operation") == "get_casefiles":
                    return await getcasefile(arguments)
                elif arguments.get("operation") == "get_casefile_plan":
                    return await get_casefile_plan(arguments)
                else:
                    raise ValueError(f"Error calling tool {name} and  {arguments.get('operation')}: it is not implemented")
            elif name == "get_all_vessel_purchase_requisitions":
                return await get_all_vessel_purchase_requisitions_handler(arguments)
            elif name == "get_vessel_expense_data":
                return await get_vessel_expense_data_handler(arguments)
            elif name == "get_complete_vessel_budget_data":
                return await get_complete_vessel_budget_data_handler(arguments)
            else: 
                raise ValueError(f"Unknown tool: {name}")
            
            
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise


def register_tools():
    @mcp.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return server_tools

    @mcp.call_tool()
    async def mcp_call_tool(tool_name: str, arguments: dict):
        return await handle_call_tool(tool_name, arguments)
    
# ------------------- MongoDB Tool Handlers -------------------

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



async def get_typesense_schema(arguments: dict):
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
      cursor = db[collection].find(query, projection=projection)
      documents = [doc async for doc in cursor]

      # Format the results
      formatted_results = {
         "count": len(documents),
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

async def mongodb_find(arguments: dict):
   collection = arguments.get("collection")
   query = arguments.get("query")
   limit = arguments.get("limit", 10)
   skip = arguments.get("skip", 0)
   projection = arguments.get("projection", {})

   if not collection or not query:
      raise ValueError("Collection and query are required")

   try:
      # Execute the query
      mongo_client = MongoDBClient()
      db = mongo_client.db
      cursor = db[collection].find(query, projection=projection, limit=limit, skip=skip)
      documents = [doc async for doc in cursor] 

      # Format the results
      formatted_results = {
         "count": len(documents),
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
   query = arguments.get("query")
   if not query:
      raise ValueError("Query is required")

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

      formatted_text = json.dumps(results, indent=2, default=str)
      content = types.TextContent(
         type="text",
         text=formatted_text,   
         title=f"Vessel information for '{query}'", 
         format="json"
      )

      return [content]
   except Exception as e:
      logger.error(f"Error querying vessel info API: {e}")
      raise ValueError(f"Error querying vessel info API: {str(e)}")

# ------------------- QnA MongoDB Tool Handlers -------------------

 
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
    


async def get_monthly_opex_budget_variance(arguments: dict):
    """
    Handle get monthly OPEX budget variance analysis tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the OPEX budget variance analysis as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 9)

    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "monthly opex budget variance", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Monthly OPEX budget variance for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_monthly_opex_budget_variance", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Monthly OPEX budget variance for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_current_year_commited_cost(arguments: dict):
    """
    Handle get current year committed cost status tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the committed cost status as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 12)

    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "current year committed cost", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Current year committed cost status for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_current_year_commited_cost", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Current year committed cost status for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_budget_status_summary_ytd(arguments: dict):
    """
    Handle get budget status summary year-to-date tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the budget status summary as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 17)

    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "budget status summary ytd", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Budget status summary YTD for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_budget_status_summary_ytd", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Budget status summary YTD for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_vessel_eta_from_email(arguments: dict):
    """
    Handle get vessel schedule, ETA and cargo activity tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the vessel schedule, ETA and cargo activity as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 32)

    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "vessel schedule, eta and cargo activity", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Vessel schedule, ETA and cargo activity for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_vessel_eta_from_email", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Vessel schedule, ETA and cargo activity for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def get_purchase_orders_with_forwarders(arguments: dict):
    """
    Handle get POs with forwarders tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the POs with forwarders as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 122)

    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "po with forwarders", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"POs with forwarders for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("get_purchase_orders_with_forwarders", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"POs with forwarders for IMO {imo}",
        format="json"
    )
    return [content, artifact]

async def purchase_orders_open_more_than_180_days(arguments: dict):
    """
    Handle get purchase orders open more than 180 days tool
    
    Args:
        arguments: Tool arguments including vessel IMO
        
    Returns:
        List containing the purchase orders open more than 180 days as TextContent
    """
    imo = arguments.get("imo")
    result = fetch_qa_details(imo, 123)

    link = result.get('link', None)
    vessel_name = result.get('vesselName', None)
    session_id = arguments.get("session_id", "testing")
    insert_data_link_to_mongodb(link, "purchase orders open more than 180 days", session_id, imo, vessel_name)
    
    # Format the results as JSON
    formatted_text = json.dumps(result, indent=2, default=str)
    
    # Create TextContent
    content = types.TextContent(
        type="text",
        text=formatted_text,
        title=f"Purchase orders open more than 180 days for IMO {imo}",
        format="json"
    )
    
    artifact_data = get_artifact("purchase_orders_open_more_than_180_days", link)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2, default=str),
        title=f"Purchase orders open more than 180 days for IMO {imo}",
        format="json"
    )
    return [content, artifact]

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
            title=f"Vessels associated with user {user_id}",
        )
        
        return [content]
    except Exception as e:
        logger.error(f"Error retrieving vessels for user {user_id}: {e}")
        raise ValueError(f"Error retrieving associated vessels: {str(e)}")

# ------------------- Typesense Tool Handlers -------------------

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

async def list_recent_vessel_purchase_requisitions(arguments: dict):
   """
   Handle list recent vessel purchase requisitions tool
   
   Args:
      arguments: Tool arguments including IMO number and purchase requisition date
      
   Returns:
      List containing the purchase requisitions as TextContent
   """
   imo = arguments.get("imo")
   lookbackHours = arguments.get("lookbackHours")
   per_page = arguments.get("per_page", 250)
   session_id = arguments.get("session_id", "testing")

   if not imo or not lookbackHours:
      raise ValueError("IMO number and lookback hours are required")
   
   try:
      start_utc  = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=lookbackHours)
      start_ts   = int(start_utc.timestamp())  
      collection = "purchase"
      query = {
            "q": "*",                                          # wildcard token
            "query_by": "vesselName",                          # any indexed string
            "filter_by": (
      f"imo:={imo} && "
      f"purchaseRequisitionDate:>={start_ts}"
   ),
   "per_page": per_page,
   "sort_by": "purchaseRequisitionDate:desc"
      }
      # Execute the search
      client = TypesenseClient()
      results = client.collections[collection].documents.search(query)

      hits = results.get("hits", [])
      filtered_hits = []
      
      for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size
            document.pop('embedding', None)
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
      link_header = "recent vessel purchase requisitions"
      insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
      
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
      content = types.TextContent(
            type="text",                # Required field
            text=formatted_text,        # The actual text content
            title=f"Purchase requisitions for {imo} in the last {lookbackHours} hours",
            format="json"
      )
      
      artifact_data = get_artifact("list_recent_vessel_purchase_requisitions", data_link)

      artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Purchase requisitions for {imo} in the last {lookbackHours} hours",
          format="json"
      )
      return [content, artifact]
   except Exception as e:
      logger.error(f"Error retrieving purchase requisitions for {imo} in the last {lookbackHours} hours", e)
      raise ValueError(f"Error retrieving purchase requisitions: {str(e)}")


async def get_purchase_emails(arguments: dict):
   """
   Handle get purchase emails tool
   
   Args:
      arguments: Tool arguments including IMO number and lookback hours       
   Returns:
      List containing the purchase emails as TextContent
   """
   imo = arguments.get("imo")
   lookbackHours = arguments.get("lookbackHours")
   per_page = arguments.get("per_page", 10)
   include_fields = "vesselName,dateTime,subject,importance,casefile,narrative,senderEmailAddress,toRecipientsEmailAddresses,imo,tags"
   tag = arguments.get("tag", "purchase")
   session_id = arguments.get("session_id", "testing")

   if not imo or not lookbackHours:
      raise ValueError("IMO number and lookback hours are required")
   
   try:
      start_utc = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=lookbackHours)
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
      
      # Execute the search
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
      content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Purchase-related emails for vessel {imo} in the last {lookbackHours} hours",  # Updated title to be more accurate
            format="json"   
      )
      
      return [content]
   except Exception as e:
      logger.error(f"Error retrieving purchase-related emails for {imo} in the last {lookbackHours} hours", e)
      raise ValueError(f"Error retrieving purchase-related emails: {str(e)}")



async def get_purchase_requisition_details(arguments: dict):
   """
   Handle get purchase requisition details tool
   
   Args:
      arguments: Tool arguments including purchase requisition number

   Returns:
      List containing the purchase requisition details as TextContent
   """
   purchaseRequisitionNumber = arguments.get("purchaseRequisitionNumber")
   per_page = arguments.get("per_page", 250)
   session_id = arguments.get("session_id", "testing")

   if not purchaseRequisitionNumber:
      raise ValueError("Purchase requisition number is required")
   
   
   try:
      collection = "purchase"
      query = {
            "q": "*",
            "filter_by": f"purchaseRequisitionNumber:{purchaseRequisitionNumber}",
            "per_page": per_page
      }
      client = TypesenseClient()
      results = client.collections[collection].documents.search(query)
      document = results.get("hits", [])[0].get("document", {})
      document.pop('embedding', None)

      # Get documents for data link
      documents = [document]
      
      # Get data link
      data_link = get_data_link(documents)
      
      # Get vessel name and imo from document
      vessel_name = document.get('vesselName', None)
      imo = document.get('imo', None)
         
      # Insert the data link to mongodb collection
      link_header = "purchase requisition details"
      insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)

      # Convert the results to JSON string
      formatted_text = json.dumps(document, indent=2)
      
      # Create TextContent with all required fields in correct structure
      content = types.TextContent(
            type="text",                # Required field
            text=formatted_text,        # The actual text content
            title=f"Purchase requisition details for {purchaseRequisitionNumber}",
            format="json"
      )
      
      artifact_data = get_artifact("get_purchase_requisition_details", data_link)

      artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Purchase requisition details for {purchaseRequisitionNumber}",
          format="json"
      )
      
      return [content, artifact]    
   except Exception as e:
      logger.error(f"Error retrieving purchase requisition details for {purchaseRequisitionNumber}", e)
      raise ValueError(f"Error retrieving purchase requisition details: {str(e)}")


async def get_purchase_order_details(arguments: dict):
   """
   Handle get purchase order details tool
   
   Args:
      arguments: Tool arguments including purchase order number

   Returns:
      List containing the purchase order details as TextContent
   """
   purchaseOrderNumber = arguments.get("purchaseOrderNumber")
   per_page = arguments.get("per_page", 250)
   session_id = arguments.get("session_id", "testing")

   if not purchaseOrderNumber:
      raise ValueError("Purchase order number is required")
   
   try:
      collection = "purchase"
      query = {
            "q": "*",
            "filter_by": f"purchaseOrderNumber:{purchaseOrderNumber}",
            "per_page": per_page
      }
      client = TypesenseClient()
      results = client.collections[collection].documents.search(query)
      document = results.get("hits", [])[0].get("document", {})
      document.pop('embedding', None)

      # Get documents for data link
      documents = [document]
      
      # Get data link
      data_link = get_data_link(documents)
      
      # Get vessel name and imo from document
      vessel_name = document.get('vesselName', None)
      imo = document.get('imo', None)
         
      # Insert the data link to mongodb collection
      link_header = "purchase order details"
      insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)

      # Convert the results to JSON string
      formatted_text = json.dumps(document, indent=2)

      # Create TextContent with all required fields in correct structure
      content = types.TextContent(
            type="text",                # Required field
            text=formatted_text,        # The actual text content
            title=f"Purchase order details for {purchaseOrderNumber}",
            format="json"
      )

      artifact_data = get_artifact("get_purchase_order_details", data_link)

      artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Purchase order details for {purchaseOrderNumber}",
          format="json"
      )

      return [content, artifact]
   except Exception as e:
      logger.error(f"Error retrieving purchase order details for {purchaseOrderNumber}", e)
      raise ValueError(f"Error retrieving purchase order details: {str(e)}")



async def list_requisitions_by_status(arguments: dict):
   """
   Hande list reguisitions by status tools
   Args:
      arguments: Tool arguments including purchase requisition status and imo number

   Returns:
      List containing the purchase order details as TextContent
   """

   purchaseRequisitionStatus = arguments.get("purchaseRequisitionStatus")
   imo = arguments.get("imo")
   per_page = arguments.get("per_page",250)
   session_id = arguments.get("session_id", "testing")

   if not purchaseRequisitionStatus or not imo:
      raise ValueError("Purchase requisition status and imo number are required")
   
   try:
      collection = "purchase"
      query = {
            "q": "*",
            "filter_by": f"purchaseRequisitionStatus:{purchaseRequisitionStatus} && imo:={imo}",
            "per_page": per_page
      }
      client = TypesenseClient()
      results = client.collections[collection].documents.search(query)
      hits = results.get("hits", [])
      filtered_hits = []

      for hit in hits:
            document = hit.get('document', {})
            document.pop('embedding', None)
            document = convert_unix_dates(document)
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
      link_header = "requisitions by status"
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
            title=f"Purchase requisitions for {imo} with status {purchaseRequisitionStatus}",
            format="json"
      )

      artifact_data = get_artifact("list_requisitions_by_status", data_link)

      artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Purchase requisitions for {imo} with status {purchaseRequisitionStatus}",
          format="json"     
      )

      return [content, artifact]
   
   except Exception as e:
      logger.error(f"Error retrieving purchase requisitions for {imo} with status {purchaseRequisitionStatus}", e)
      raise ValueError(f"Error retrieving purchase requisitions: {str(e)}")

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

async def list_overdue_open_requisitions(arguments: dict):
   """
   Handle list overdue open requisitions tool
   
   Args:
      arguments: Tool arguments including IMO number, days overdue, and stage
      
   Returns:
      List containing the overdue requisitions as TextContent
   """
   imo = arguments.get("imo")
   days_overdue = arguments.get("daysOverdue")
   stage = arguments.get("stage")
   per_page = arguments.get("per_page", 250)
   session_id = arguments.get("sessionId","testing")
   if not imo or not days_overdue or not stage:
      raise ValueError("IMO number, days overdue, and stage are required")
   
   try:
      # Calculate cutoff date based on days overdue
      cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_overdue)
      cutoff_ts = int(cutoff_date.timestamp())
      
      collection = "purchase"
      
      # Include fields as specified in the base URL
      include_fields = ("imo,vesselName,purchaseRequisitionDate,purchaseRequisitionDescription,"
                        "purchaseRequisitionStatus,purchaseOrderAmount,purchaseOrderIssuedDate,"
                        "vendorOrsupplierName,invoiceStatus,invoiceValue,orderReadinessDate,"
                        "purchaseRequisitionNumber,purchaseRequisitionLink,purchaseOrderNumber,"
                        "purchaseOrderLink,purchaseRequisitionType,scanID,scanIDLink,"
                        "purchaseOrderStatus,poCreatedBy,orderType,invoiceApproverName,"
                        "forwarderName,forwarderRemarks,warehouseLocation,cargoType,weight,"
                        "purchaseRequisitionSummary,orderPriority,accountCode")
      
      query = {
            "q": "*",                                         # wildcard token
            "query_by": "vesselName",                         # any indexed string
            "filter_by": (
               f"imo:={imo} && "
               f"purchaseOrderStage:={stage} && "
               f"purchaseRequisitionDate:<{cutoff_ts}"
            ),
            "per_page": per_page,
            "sort_by": "purchaseRequisitionDate:asc",         # oldest first
            "include_fields": include_fields
      }
      
      # Execute the search
      logger.info(f"Searching for overdue requisitions with params: {query}")
      client = TypesenseClient()
      results = client.collections[collection].documents.search(query)

      hits = results.get("hits", [])
      filtered_hits = []
      
      for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size if it exists
            document.pop('embedding', None)
            document = convert_unix_dates(document)
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
      documents = [d['document'] for d in filtered_hits]
      #get the data link for the purchase requisition
      data_link = get_data_link(documents)

      #get vesselname from hits
      try:
         vessel_name = hits[0]['document'].get('vesselName',None)
      except:
         vessel_name = None

      #insert the data link to mongodb collection casefile_data
      link_header = "list overdue open requisitions"
      insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)

      # Convert the results to JSON string
      formatted_text = json.dumps(formatted_results, indent=2)
      
      # Create human-readable timestamp for the title
      cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')
      
      # Create TextContent with all required fields in correct structure
      content = types.TextContent(
            type="text",                # Required field
            text=formatted_text,        # The actual text content
            title=f"Overdue {stage} requisitions for vessel {imo} older than {days_overdue} days",
            format="json"
      )
      
      artifact_data = get_artifact("list_overdue_open_requisitions", data_link)

      artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Overdue {stage} requisitions for vessel {imo} older than {days_overdue} days",
          format="json"
      )
      return [content, artifact]    
   except Exception as e:
      logger.error(f"Error retrieving overdue requisitions for {imo} with stage {stage}", e)
      return [types.TextContent(
            type="text",
            text=f"Error retrieving overdue requisitions: {str(e)}"
      )]

async def list_purchase_orders_by_status(arguments: dict):
   """
   Handle list purchase orders by status tool
   
   Args:
      arguments: Tool arguments including IMO number and purchase order status
      
   Returns:
      List containing the purchase orders as TextContent
   """
   imo = arguments.get("imo")
   purchase_order_status = arguments.get("purchaseOrderStatus")
   per_page = arguments.get("per_page", 250)
   session_id = arguments.get("session_id", "testing")

   if not imo or not purchase_order_status:
      raise ValueError("IMO number and purchase order status are required")
   
   try:
      collection = "purchase"
      
      # Include fields as specified in the base URL
      include_fields = ("imo,vesselName,purchaseRequisitionDate,purchaseRequisitionDescription,"
                        "purchaseRequisitionStatus,purchaseOrderAmount,purchaseOrderIssuedDate,"
                        "vendorOrsupplierName,invoiceStatus,invoiceValue,orderReadinessDate,"
                        "purchaseRequisitionNumber,purchaseRequisitionLink,purchaseOrderNumber,"
                        "purchaseOrderLink,purchaseRequisitionType,scanID,scanIDLink,"
                        "purchaseOrderStatus,poCreatedBy,orderType,invoiceApproverName,"
                        "forwarderName,forwarderRemarks,warehouseLocation,cargoType,weight,"
                        "purchaseRequisitionSummary,orderPriority,accountCode")
      
      query = {
            "q": "*",                                         # wildcard token
            "query_by": "vesselName",                         # any indexed string
            "filter_by": (
               f"imo:={imo} && "
               f"purchaseOrderStatus:={purchase_order_status}"
            ),
            "per_page": per_page,
            "sort_by": "purchaseOrderIssuedDate:desc",        # newest first
            "include_fields": include_fields
      }
      
      # Execute the search
      logger.info(f"Searching for purchase orders with status {purchase_order_status} for vessel {imo}")
      client = TypesenseClient()
      results = client.collections[collection].documents.search(query)

      hits = results.get("hits", [])
      filtered_hits = []
      
      for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size if it exists
            document.pop('embedding', None)
            document = convert_unix_dates(document)
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
      link_header = "purchase orders by status"
      insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
      
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
      content = types.TextContent(
            type="text",                # Required field
            text=formatted_text,        # The actual text content
            title=f"Purchase orders with status '{purchase_order_status}' for vessel {imo}",
            format="json"
      )
      
      artifact_data = get_artifact("list_purchase_orders_by_status", data_link)

      artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Purchase orders with status '{purchase_order_status}' for vessel {imo}",
          format="json"
      )
      return [content, artifact]    
   except Exception as e:
      logger.error(f"Error retrieving purchase orders with status {purchase_order_status} for vessel {imo}", e)
      return [types.TextContent(
            type="text",
            text=f"Error retrieving purchase orders: {str(e)}"
      )]

async def list_requisitions_by_type_and_stage(arguments: dict):
   """
   Handle list requisitions by type and stage tool
   
   Args:
      arguments: Tool arguments including IMO, purchase requisition type, and purchase order stage
      
   Returns:
      List containing the requisitions as TextContent
   """
   imo = arguments.get("imo")
   requisition_type = arguments.get("purchaseRequisitionType")
   order_stage = arguments.get("purchaseOrderStage")
   vessel_name = arguments.get("vesselName")
   per_page = arguments.get("per_page", 250)
   session_id = arguments.get("session_id", "testing")

   if not imo or not requisition_type or not order_stage:
      raise ValueError("IMO number, purchase requisition type, and purchase order stage are required")
   
   try:
      collection = "purchase"
      
      # Include fields as specified in the base URL
      include_fields = ("imo,vesselName,purchaseRequisitionDate,purchaseRequisitionDescription,"
                        "purchaseRequisitionStatus,purchaseOrderAmount,purchaseOrderIssuedDate,"
                        "vendorOrsupplierName,invoiceStatus,invoiceValue,orderReadinessDate,"
                        "purchaseRequisitionNumber,purchaseRequisitionLink,purchaseOrderNumber,"
                        "purchaseOrderLink,purchaseRequisitionType,scanID,scanIDLink,"
                        "purchaseOrderStatus,poCreatedBy,orderType,invoiceApproverName,"
                        "forwarderName,forwarderRemarks,warehouseLocation,cargoType,weight,"
                        "purchaseRequisitionSummary,orderPriority,accountCode")
      
      # Build filter_by based on required and optional parameters
      filter_by = f"imo:={imo} && purchaseRequisitionType:={requisition_type} && purchaseOrderStage:={order_stage}"
      
      # Add vessel name filter if provided
      if vessel_name:
            filter_by += f" && vesselName:={vessel_name}"
            
      query = {
            "q": "*",                                  # wildcard token
            "query_by": "vesselName",                  # any indexed string
            "filter_by": filter_by,
            "per_page": per_page,
            "sort_by": "purchaseRequisitionDate:desc", # newest first as specified
            "include_fields": include_fields
      }
      
      # Execute the search
      logger.info(f"Searching for requisitions of type {requisition_type} in stage {order_stage} for vessel {imo}")
      client = TypesenseClient()
      results = client.collections[collection].documents.search(query)

      hits = results.get("hits", [])
      filtered_hits = []
      
      for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size if it exists
            document.pop('embedding', None)
            document = convert_unix_dates(document)
            filtered_hits.append({
               'id': document.get('id'),
               'score': hit.get('text_match', 0),
               'document': document
            })
      
      # Get documents for data link
      documents = [hit['document'] for hit in filtered_hits]
      
      # Get data link
      data_link = get_data_link(documents)
      
      # Get vessel name from hits if not provided in arguments
      if not vessel_name:
          try:
             vessel_name = hits[0]['document'].get('vesselName', None)
          except:
             vessel_name = None
         
      # Insert the data link to mongodb collection
      link_header = "requisitions by type and stage"
      insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
      
      # Format the results
      formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
      }   
      
      # Convert the results to JSON string
      formatted_text = json.dumps(formatted_results, indent=2)
      
      # Create descriptive title
      title = f"{requisition_type} requisitions in {order_stage} stage for vessel {imo}"
      if vessel_name:
            title += f" ({vessel_name})"
      
      # Create TextContent with all required fields in correct structure
      content = types.TextContent(
            type="text",
            text=formatted_text,
            title=title,
            format="json"
      )
      
      artifact_data = get_artifact("list_requisitions_by_type_and_stage", data_link)

      artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=title,
          format="json"
      )
      return [content, artifact]    
   except Exception as e:
      logger.error(f"Error retrieving requisitions of type {requisition_type} in stage {order_stage} for vessel {imo}", e)
      return [types.TextContent(
            type="text",
            text=f"Error retrieving requisitions: {str(e)}"
      )]

async def list_recent_requisitions_by_order_priority(arguments: dict):
   """
   Handle list recent requisitions by order priority tool
   
   Args:
      arguments: Tool arguments including IMO number, days ago, and optional order priority
      
   Returns:
      List containing the requisitions as TextContent
   """
   imo = arguments.get("imo")
   days_ago = arguments.get("daysAgo")
   order_priority = arguments.get("orderPriority")  # This is optional
   per_page = arguments.get("per_page", 250)
   session_id = arguments.get("session_id", "testing")

   if not imo or days_ago is None:
      raise ValueError("IMO number and days ago are required")
   
   try:
      # Calculate cutoff date based on days ago
      cutoff_date = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)
      cutoff_ts = int(cutoff_date.timestamp())
      
      collection = "purchase"
      
      # Include fields as specified in the base URL
      include_fields = ("imo,vesselName,purchaseRequisitionDate,purchaseRequisitionDescription,"
                        "purchaseRequisitionStatus,purchaseOrderAmount,purchaseOrderIssuedDate,"
                        "vendorOrsupplierName,invoiceStatus,invoiceValue,orderReadinessDate,"
                        "purchaseRequisitionNumber,purchaseRequisitionLink,purchaseOrderNumber,"
                        "purchaseOrderLink,purchaseRequisitionType,scanID,scanIDLink,"
                        "purchaseOrderStatus,poCreatedBy,orderType,invoiceApproverName,"
                        "forwarderName,forwarderRemarks,warehouseLocation,cargoType,weight,"
                        "purchaseRequisitionSummary,orderPriority,accountCode")
      
      # Build filter_by based on required and optional parameters
      filter_by = f"imo:={imo} && purchaseRequisitionDate:>={cutoff_ts}"
      
      # Add order priority filter if provided
      if order_priority:
            filter_by += f" && orderPriority:={order_priority}"
            
      query = {
            "q": "*",                                         # wildcard token
            "query_by": "vesselName",                         # any indexed string
            "filter_by": filter_by,
            "per_page": per_page,
            "sort_by": "purchaseRequisitionDate:desc",        # newest first
            "include_fields": include_fields
      }
      
      # Execute the search
      logger.info(f"Searching for recent requisitions with params: {query}")
      client = TypesenseClient()
      results = client.collections[collection].documents.search(query)

      hits = results.get("hits", [])
      filtered_hits = []
      
      for hit in hits:
            document = hit.get('document', {})
            # Remove embedding field to reduce response size if it exists
            document.pop('embedding', None)
            document = convert_unix_dates(document)
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
      link_header = "recent requisitions by order priority"
      insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
      
      # Format the results
      formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
      }   
      
      # Convert the results to JSON string
      formatted_text = json.dumps(formatted_results, indent=2)
      
      # Create human-readable date for the title
      cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')
      
      # Create descriptive title
      title = f"Recent requisitions for vessel {imo} in the last {days_ago} days"
      if order_priority:
            title = f"{order_priority} priority {title}"
      
      # Create TextContent with all required fields in correct structure
      content = types.TextContent(
            type="text",                # Required field
            text=formatted_text,        # The actual text content
            title=title,
            format="json"
      )
      
      artifact_data = get_artifact("list_recent_requisitions_by_order_priority", data_link)

      artifact = types.TextContent(
          type="text",
          text=json.dumps(artifact_data, indent=2, default=str),
          title=f"Recent {order_priority} requisitions for vessel {imo} from the last {days_ago} days   ",
          format="json"
      )
      return [content, artifact]
   except Exception as e:
      error_msg = f"Error retrieving recent requisitions for vessel {imo}"
      if order_priority:
            error_msg += f" with {order_priority} priority"
      logger.error(f"{error_msg}: {e}")
      return [types.TextContent(
            type="text",
            text=f"Error retrieving requisitions: {str(e)}"
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

async def get_purchase_casefiles(arguments: dict):
    """
    Handle get purchase casefiles tool
    
    Args:
        arguments: Tool arguments including IMO numbers and lookback hours

    Returns:
        List containing the records as TextContent
    """
    imo = arguments.get("imo")
    lookback_hours = arguments.get("lookback_hours")
    per_page = arguments.get("per_page", 10)
    query_keyword = arguments.get("query_keyword", "purchase")  

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

        artifacts = get_list_of_artifacts("get_purchase_casefiles", link_data)
        
        return [content] + artifacts
    except Exception as e:
        logger.error(f"Error searching collection {collection}: {e}")
        raise ValueError(f"Error searching collection: {str(e)}")
        
   
              
   







async def list_top_expenses_by_category(arguments: dict):
    """Return a vessel's highest-value expense records (expenseCategory = "ACTUAL EXPENSES") so the user can pick the top N items in each budget category."""
    try:
        imo = arguments.get("imo")
        session_id = arguments.get("session_id", "testing")
        if not imo:
            raise ValueError("IMO number is required")
 
        # Build filter_by string
        filter_by = f"imo:{imo} && expenseCategory:\"ACTUAL EXPENSES\""
        
        # Add optional filters
        if "group" in arguments:
            filter_by += f" && group:{arguments['group']}"
        if "dateFrom" in arguments:
            filter_by += f" && expenseDate:>={arguments['dateFrom']}"
        if "dateTo" in arguments:
            filter_by += f" && expenseDate:<={arguments['dateTo']}"
 
        # Execute search
        search_parameters = {
            "q": "*",
            "filter_by": filter_by,
            "sort_by": "expenseAmount:desc",
            "per_page": arguments.get("per_page", 100),
            "include_fields": "imo,vesselName,group,category,accountNo,accountDescription,expenseDate,poAmount,expenseAmount,expenseCategory,scanID,remarks,vendor,poNumber,poDate,poDescription"
        }
 
        client = TypesenseClient()
        search_result = client.collections["expense"].documents.search(search_parameters)
        
        if not search_result or "hits" not in search_result:
            return [types.TextContent(
                type="text",
                text="No expense records found for the specified criteria.",
                title="No Expenses Found",
                format="json"
            )]
 
        # Process results
        expenses = []
        hits = search_result.get("hits", [])
        for hit in hits:
            document = hit.get("document", {})
            document = convert_unix_dates(document)
            expenses.append(document)
 
        # Get documents for data link
        documents = [hit["document"] for hit in hits]
        
        # Get data link
        data_link = get_data_link(documents)
        
        # Get vessel name from hits
        try:
            vessel_name = hits[0]['document'].get('vesselName', None)
        except:
            vessel_name = None
            
        # Insert the data link to mongodb collection
        link_header = "top expenses by category"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
        
        # Format results
        formatted_text = json.dumps(expenses, indent=2, default=str)
        
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title="Top Expenses by Category",
            format="json"
        )
        
        artifact_data = get_artifact("list_top_expenses_by_category", data_link)

        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title="Top Expenses by Category",
            format="json"
        )
        return [content, artifact]
 
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving top expenses: {str(e)}",
            title="Error",
            format="json"
        )]
 
async def list_committed_cost_expenses(arguments: dict):
    """Retrieve expense records for a vessel that are classified as "COMMITTED COST"."""
    try:
        imo = arguments.get("imo")
        session_id = arguments.get("session_id", "testing")
        if not imo:
            raise ValueError("IMO number is required")
 
        # Build filter_by string
        filter_by = f"imo:{imo} && expenseCategory:\"COMMITTED COST\""
        
        # Add optional filters
        if "group" in arguments:
            filter_by += f" && group:{arguments['group']}"
        if "category" in arguments:
            filter_by += f" && category:{arguments['category']}"
        if "dateFrom" in arguments:
            filter_by += f" && expenseDate:>={arguments['dateFrom']}"
        if "dateTo" in arguments:
            filter_by += f" && expenseDate:<={arguments['dateTo']}"
 
        # Execute search
        search_parameters = {
            "q": "*",
            "filter_by": filter_by,
            "per_page": arguments.get("per_page", 50),
            "include_fields": "imo,vesselName,group,category,accountNo,accountDescription,expenseDate,poAmount,expenseAmount,expenseCategory,scanID,remarks,vendor,poNumber,poDate,poDescription"
        }
 
        client = TypesenseClient()
        search_result = client.collections["expense"].documents.search(search_parameters)
        
        if not search_result or "hits" not in search_result:
            return [types.TextContent(
                type="text",
                text="No committed cost records found for the specified criteria.",
                title="No Committed Costs Found",
                format="json"
            )]

        hits = search_result.get("hits", [])
        # Process results
        committed_costs = []
        for hit in hits:
            document = hit.get("document", {})
            document = convert_unix_dates(document)
            committed_costs.append(document)
 
        # Get documents for data link
        documents = [hit["document"] for hit in hits]
        
        # Get data link
        data_link = get_data_link(documents)
        
        # Get vessel name from hits
        try:
            vessel_name = hits[0]['document'].get('vesselName', None)
        except:
            vessel_name = None
            
        # Insert the data link to mongodb collection
        link_header = "committed cost expenses"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
        
        # Format results
        formatted_text = json.dumps(committed_costs, indent=2, default=str)
        
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title="Committed Cost Expenses",
            format="json"
        )
        
        artifact_data = get_artifact("list_committed_cost_expenses", data_link)

        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title="Committed Cost Expenses",
            format="json"
        )
        return [content, artifact]
 
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving committed cost expenses: {str(e)}",
            title="Error",
            format="json"
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

async def get_vessel_purchase_log_table(arguments: dict):
    """Get the purchase log table for a vessel."""
    try:
        imo = arguments.get("imo")
        if not imo:
            raise ValueError("IMO number is required")
 
        # Build filter_by string
        filter_by = f"imo:{imo}"
 
        # Execute search
        search_parameters = {
            "q": "*",
            "filter_by": filter_by,
            "per_page": arguments.get("per_page", 100),
            "include_fields": "imo,vesselName,purchaseRequisitionDate,purchaseRequisitionDescription,purchaseRequisitionStatus,purchaseOrderAmount,purchaseOrderIssuedDate,vendorOrsupplierName,invoiceStatus,invoiceValue,orderReadinessDate,purchaseRequisitionNumber,purchaseRequisitionLink,purchaseOrderNumber,purchaseOrderLink,purchaseRequisitionType,scanID,scanIDLink,purchaseOrderStatus,poCreatedBy,orderType,invoiceApproverName,forwarderName,forwarderRemarks,warehouseLocation,cargoType,weight,purchaseRequisitionSummary,orderPriority,accountCode"
        }
 
        try:
            client = TypesenseClient()
            search_result = client.collections["purchase"].documents.search(search_parameters)
        except Exception as e:
            if "404" in str(e):
                return [types.TextContent(
                    type="text",
                    text="The purchase collection is not available. Please check if the collection exists and is properly configured.",
                    title="Collection Not Found",
                    format="json"
                )]
            raise e
        
        if not search_result or "hits" not in search_result:
            return [types.TextContent(
                type="text",
                text=f"No purchase requisitions found for vessel with IMO {imo}.",
                title="No Purchase Requisitions Found",
                format="json"
            )]
 
        # Process results
        requisitions = []
        for hit in search_result["hits"]:
            document = hit["document"]
            
            # Convert dates from unix timestamp to human readable format
            if 'purchaseRequisitionDate' in document:
                document['purchaseRequisitionDate'] = dt.datetime.fromtimestamp(document['purchaseRequisitionDate']).strftime('%Y-%m-%d %H:%M:%S')
            if 'purchaseOrderIssuedDate' in document:
                document['purchaseOrderIssuedDate'] = dt.datetime.fromtimestamp(document['purchaseOrderIssuedDate']).strftime('%Y-%m-%d %H:%M:%S')
            if 'orderReadinessDate' in document:
                document['orderReadinessDate'] = dt.datetime.fromtimestamp(document['orderReadinessDate']).strftime('%Y-%m-%d %H:%M:%S')
                
            requisitions.append(document)
 
        # Format results
        formatted_text = json.dumps(requisitions, indent=2, default=str)
        
        return [types.TextContent(
            type="text",
            text=formatted_text,
            title="Purchase Requisition Log Table",
            format="json"
        )]
 
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving purchase requisition log table: {str(e)}",
            title="Error",
            format="json"
        )]
      


# async def google_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:

#     query = arguments.get("query")
#     if not query:
#         raise ValueError("Search query is required")
    

#     url = "https://api.perplexity.ai/chat/completions"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "Bearer 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"
#     }
#     payload = {
#         "model": "sonar-reasoning-pro",
#         "messages": [
#             {
#                 "role": "system",
#                 "content": "You are an expert assistant helping with reasoning tasks."
#             },
#             {
#                 "role": "user",
#                 "content": query
#             }
#         ],
#         "max_tokens": 2000,
#         "temperature": 0.2,
#         "top_p": 0.9,
#         "search_domain_filter": None,
#         "return_images": False,
#         "return_related_questions": False,
#         "search_recency_filter": "week",
#         "top_k": 0,
#         "stream": False,
#         "presence_penalty": 0,
#         "frequency_penalty": 1,
#         "response_format": None
#     }

#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.post(url, headers=headers, json=payload) as response:
#                 if response.status == 200:
#                     result = await response.json()
#                     citations = result.get("citations", [])
#                     content = result['choices'][0]['message']['content']
#                     return [
#                         types.TextContent(
#                             type="text", 
#                             text=f"Response: {content}\n\nCitations: {citations}"
#                         )
#                     ]
#                 else:
#                     error_text = await response.text()
#                     return [
#                         types.TextContent(
#                             type="text", 
#                             text=f"Error: {response.status}, {error_text}"
#                         )
#                     ]

#     except Exception as e:
#         logger.error(f"Failure to execute the search operation: {e}")
#         raise


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

async def list_recent_urgent_requisitions(arguments: dict):
    """Returns purchase-requisition records whose orderPriority is URGENT and whose purchaseRequisitionDate falls within the last N days for a specified vessel."""
    try:
        imo = arguments.get("imo")
        days_ago = arguments.get("daysAgo")
        per_page = arguments.get("per_page", 20)
        session_id = arguments.get("session_id", "testing")

        if not imo:
            raise ValueError("IMO number is required")
        if not days_ago:
            raise ValueError("daysAgo is required")

        # Calculate the date N days ago
        cutoff_date = datetime.now(timezone.utc) - dt.timedelta(days=days_ago)
        # Convert to Unix timestamp (integer)
        cutoff_timestamp = int(cutoff_date.timestamp())

        # Build filter_by string using the integer timestamp
        filter_by = f"imo:{imo} && orderPriority:URGENT && purchaseRequisitionDate:>={cutoff_timestamp}"

        # Execute search
        search_parameters = {
            "q": "*",
            "filter_by": filter_by,
            "sort_by": "purchaseRequisitionDate:desc",
            "per_page": per_page,
            "include_fields": "imo,vesselName,purchaseRequisitionNumber,purchaseRequisitionDate,orderPriority,purchaseRequisitionStatus,purchaseRequisitionType"
        }

        client = TypesenseClient()
        search_result = client.collections["purchase"].documents.search(search_parameters)

        if not search_result or "hits" not in search_result:
            return [types.TextContent(
                type="text",
                text=f"No urgent requisitions found for vessel {imo} in the last {days_ago} days.",
                title="No Urgent Requisitions Found",
                format="json"
            )]

        # Format results
        hits = search_result.get("hits", [])
        documents = []
        for hit in hits:
            document = hit["document"]
            document = convert_unix_dates(document)
            documents.append(document)
        
        # Get data link
        data_link = get_data_link(documents)
        
        # Get vessel name from documents
        vessel_name = documents[0].get("vesselName", "") if documents else ""
        
        # Insert the data link to mongodb collection
        link_header = f"urgent requisitions in last {days_ago} days"
        insert_data_link_to_mongodb(data_link, link_header, arguments.get("session_id", "testing"), imo, documents[0].get("vesselName", ""))

        formatted_text = json.dumps({
            "count": len(documents),
            "documents": documents
        }, indent=2, default=str)

        return [types.TextContent(
            type="text",
            text=formatted_text,
            title="Recent Urgent Requisitions",
            format="json"
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving urgent requisitions: {str(e)}",
            title="Error",
            format="json"
        )]

async def get_vessel_budget_data(arguments: dict):
    """Returns budget figures for a specified vessel from the budget table collection in Typesense, with optional filters for budget category, group, period, and a custom date range."""
    try:
        imo = arguments.get("imo")
        category = arguments.get("category")
        group = arguments.get("group")
        period = arguments.get("period")
        date_from = arguments.get("dateFrom")
        date_to = arguments.get("dateTo")
        per_page = arguments.get("per_page", 250)
        session_id = arguments.get("session_id", "testing")

        if not imo:
            raise ValueError("IMO number is required")

        # Build filter_by string
        filter_by = f"imo:{imo}"
        if category:
            filter_by += f" && category:={category}"
        if group:
            filter_by += f" && group:={group}"
        if period:
            filter_by += f" && period:={period}"
        if date_from and date_to:
            filter_by += f" && date:>={int(date_from)} && date:<={int(date_to)}"
        elif date_from:
            filter_by += f" && date:>={int(date_from)}"
        elif date_to:
            filter_by += f" && date:<={int(date_to)}"

        # Execute search
        search_parameters = {
            "q": "*",
            "filter_by": filter_by,
            "include_fields": "imo,vesselName,group,category,period,reportPeriod,date,budgetAmount,expenseAmount",
            "per_page": per_page
        }

        client = TypesenseClient()
        search_result = client.collections["budget"].documents.search(search_parameters)

        if not search_result or "hits" not in search_result:
            return [types.TextContent(
                type="text",
                text=f"No budget data found for vessel {imo}.",
                title="No Budget Data Found",
                format="json"
            )]

        # Format results
        hits = search_result.get("hits", [])
        budget_data = []
        for hit in hits:
            document = hit.get("document", {})
            document = convert_unix_dates(document)
            budget_data.append(document)
        
        # Get data link and insert into MongoDB
        data_link = get_data_link(budget_data)
        vessel_name = budget_data[0].get("vesselName", "") if budget_data else ""
        link_header = f"vessel budget data"
        if category: link_header += f" for category {category}"
        if group: link_header += f" for group {group}"
        if period: link_header += f" for period {period}"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)

        formatted_text = json.dumps({
            "count": len(budget_data),
            "documents": budget_data
        }, indent=2, default=str)
        
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title="Vessel Budget Data",
            format="json"
        )
        
        artifact_data = get_artifact("get_vessel_budget_data", data_link)
        
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title="Vessel Budget Data",
            format="json"
        )

        return [content, artifact]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving vessel budget data: {str(e)}",
            title="Error",
            format="json"
        )]
    
#Vendor Tools


async def vendor_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
        """
        Handle Typesense vendor search tool
        
        Args:
            arguments: Tool arguments including collection name
            
        Returns:
            List containing the collection statistics as TextContent
        """
        # collection = arguments.get("collection")
        collection = "vendor4"
        # typesense_client = TypesenseClient()
        session_id = arguments.get("session_id", "testing")
        if not collection:
            raise ValueError("Collection name is required")
        
        try:
            # Make sure all required keys are present (even if None)
            for key in ["vendorName", "service", "locationRegion"]:
                arguments.setdefault(key, None)

            results = query_vendor_search(arguments)
            
            # Get data link
            data_link = get_data_link(results)
            
            # Get imo and vessel_name if available (in this case they might not be)
            imo = None
            vessel_name = None
            
            # Insert the data link to mongodb collection
            link_header = "vendor search results"
            insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
            
            results_text = json.dumps(results, indent=2)
            # Create TextContent with all required fields
            content = types.TextContent(
                type="text",                # Required field
                text=results_text,          # The actual text content
                title=f"Vendor Search Results",
                format="json"
            )
            
            artifact_data = get_artifact("vendor_search", data_link)

            artifact = types.TextContent(
                type="text",
                text=json.dumps(artifact_data, indent=2, default=str),
                title=f"Vendor Search Results",
                format="json"
            )
            
            return [content, artifact]
        except Exception as e:
            logger.error(f"Error retrieving stats for collection {collection}", e)
            raise ValueError(f"Error retrieving collection stats: {str(e)}")
    
async def get_vendor_contact_info(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
        """
        Handle Typesense get contact info tool
        
        """
        typesense_client = TypesenseClient()
        collection = "vendor4"
        session_id = arguments.get("session_id", "testing")

        if not collection:
            raise ValueError("Collection name is required")
        
        try:
            include_fields = "address, contactEmail, contactNumber, vendorName"
            query = {
                "q": arguments['vendorName'],
                "query_by": "vendorName",
                "include_fields": include_fields
            }

            results = typesense_client.collections[collection].documents.search(query)

            logger.info("typesense results: %s", results)

            hits = results.get("hits") or []  # Ensure hits is always a list
            
            # Get documents for data link
            documents = [hit.get("document", {}) for hit in hits]
            
            # Get data link
            data_link = get_data_link(documents)
            
            # Get imo and vessel_name if available (in this case they might not be)
            imo = None
            vessel_name = None
            
            # Insert the data link to mongodb collection
            link_header = "vendor contact info"
            insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)

            formatted_results = {
                "found": results.get("found", 0),
                "out_of": results.get("out_of", 0),
                "page": results.get("page", 1),
                "hits": [hit.get("document") for hit in hits]
            }
            
            # Convert the results to JSON string
            formatted_text = json.dumps(formatted_results, indent=2)
            # Create TextContent with all required fields in correct structure
            content = types.TextContent(
                type="text",                # Required field
                text=formatted_text,        # The actual text content
                title=f"Search results for '{collection}'",
                format="json"
            )
            
            artifact_data = get_artifact("get_vendor_contact_info", data_link)

            artifact = types.TextContent(
                type="text",
                text=json.dumps(artifact_data, indent=2, default=str),
                title=f"Vendor Contact Information Results",
                format="json"
            )
            
            # Log the content for debugging
            logger.info(f"Created search results TextContent: {type(content)}")
            
            return [content, artifact]
        except Exception as e:
            logger.error(f"Error searching collection {collection}", e)
            raise ValueError(f"Error searching collection: {str(e)}")


#Helper functions
from pymongo import MongoClient
import cohere
import itertools
from rapidfuzz import process, fuzz

mongo_client = MongoClient(r'mongodb://etl:rSp6X49ScvkDpHE@db.syia.ai:27017/?authMechanism=DEFAULT&authSource=syia-etl&directConnection=true')['syia-etl']
co = cohere.Client(r"ISYpYOVgh4WBGGfMQ2eeYoLHnMviWCvjSBIH3Cci")
typesense_client = TypesenseClient()

def limit_synonyms(subs, max_synonyms=5):
        limited_subs = {}
        for key, values in subs.items():
            limited_subs[key] = values[:max_synonyms]  # Limit to the first `max_synonyms`
        return limited_subs

def reranking(query, documents, batch_size=200):
        all_results = []  # Using a min-heap to keep only the top 30 results
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            co_results = co.rerank(query=query, documents=batch, rank_fields=['field'], top_n=30, model='rerank-english-v3.0', return_documents=True)

            for result in co_results.results:
                item = {
                    'score': result.relevance_score,
                    'document': batch[result.index]
                }
                all_results.append(item)
        top_results = sorted(all_results, key=lambda x: x['score'], reverse=True)[:30]
        rerank_results = [item['document'] for item in top_results]
        return rerank_results

def chunk_list_by_length(lst, max_length):
        chunks, current_chunk = [], []
        current_length = 0
        for item in lst:
            if current_length + len(item) + 4 < max_length:
                current_chunk.append(item)
                current_length += len(item) + 4
            else:
                chunks.append(current_chunk)
                current_chunk = [item]
                current_length = len(item) + 4
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

def create_bidirectional_synonyms(phrase_synonyms):
        bidirectional = {}
        for key, synonyms in phrase_synonyms.items():
            all_phrases = [key] + synonyms
            unique_phrases = set(all_phrases)
            for phrase in unique_phrases:
                other_phrases = unique_phrases - {phrase}
                bidirectional[phrase.strip()] = list(other_phrases)
        return bidirectional

def generate_query_variants(query, bidirectional_synonyms, threshold=80, max_synonyms=5):
        query = query.strip().lower()
        query_words = query.split()
        max_n = min(5, len(query_words))
        substitutions = {}  # Stores positions and their possible replacements

        # Identify phrases to replace
        for n in range(max_n, 0, -1):
            for i in range(len(query_words) - n + 1):
                ngram = ' '.join(query_words[i:i + n])
                # Fuzzy match the n-gram against the keys in bidirectional_synonyms
                match = process.extractOne(
                    ngram, bidirectional_synonyms.keys(), scorer=fuzz.token_sort_ratio
                )
                if match:  # Check if a match is found
                    best_match, score, _ = match
                    if score >= threshold:
                        # Record the position and possible replacements
                        substitutions[(i, n)] = bidirectional_synonyms[best_match]
        substitutions = limit_synonyms(substitutions, max_synonyms=max_synonyms)

        # Generate all combinations of substitutions
        def replace_phrases(words, subs):
            positions = list(subs.keys())
            variants = []

            # Generate all combinations of substitutions
            if positions:
                replacement_combinations = itertools.product(*[subs[pos] for pos in positions])
                total_combinations = 1                                           
                for pos in positions:
                    total_combinations *= len(subs[pos])

                for replacement_choices in replacement_combinations:
                    words_copy = words.copy()
                    # Sort positions in reverse order to prevent index shifting
                    sorted_replacements = sorted(
                        zip(positions, replacement_choices), key=lambda x: x[0][0], reverse=True
                    )
                    for ((start, length), replacement) in sorted_replacements:
                        words_copy = words_copy[:start] + replacement.split() + words_copy[start+length:]
                    variants.append(' '.join(words_copy))
            else:
                # No substitutions, return original query
                variants.append(' '.join(words))

            # Ensure the original query is included
            original_query = ' '.join(words)
            if original_query not in variants:
                variants.append(original_query)

            # Remove duplicates
            return list(set(variants))

        query_variants = replace_phrases(query_words, substitutions)
        return query_variants

def query_vendor_search(query_dict):
        vendor_services_synonyms_updated = mongo_client['vendor_services_synonyms_updated']

        result = {i:[] for i in query_dict.keys()}
        for field, value in query_dict.items():
            if value is not None:
                value = value.lower()# lower all the user query values
                if field == 'service':
                    service_query = query_dict.get('service', None)
                    phrase_synonyms = {}

                    services_syn = list(vendor_services_synonyms_updated.find())
                    for doc in services_syn:
                        service_name = doc['service'].lower()                   # lower all the service names
                        synonyms = [_.lower() for _ in doc['synonyms']]         # lower all the synonyms
                        match = process.extractOne(service_query, synonyms)

                        if match:  # catching None
                            best_match, score, index = match
                            if score >= 70:
                                if best_match not in phrase_synonyms:
                                    phrase_synonyms[best_match] = synonyms
                                else:
                                    phrase_synonyms[best_match].extend(synonyms)
                                    phrase_synonyms[best_match] = list(set(phrase_synonyms[best_match]))        
                                                
                    bidirectional_synonyms = create_bidirectional_synonyms(phrase_synonyms)
                    query_variants = generate_query_variants(service_query, bidirectional_synonyms)
                    ls = [{"field": variant.lower()} for variant in query_variants]         
                    top_results = reranking(service_query, ls)
                    query_variants = [_['field'] for _ in top_results]


                    chunked_query_variants = chunk_list_by_length(query_variants, 2000)
                    aggregated_hits_embedding = []
                    aggregated_hits_gpt_chunked = []
                    
                    for chunk in chunked_query_variants:
                        combined_query = ' OR '.join(f'({variant})' for variant in chunk)

                        search_parameters_embedding = {
                            'q': combined_query,
                            'query_by': 'embedding',
                            'prefix': 'false',
                            "num_typos": 5,
                            'per_page': 15,
                            'page': 1
                        }

                        search_parameters_gpt_chunked = {
                            'q': combined_query,
                            'query_by': 'gpt_chunked_services, servicesOffered',
                            'prefix': 'false',
                            "num_typos": 5
                        }

                        try:
                            results_embedding = typesense_client.collections['vendor4'].documents.search(search_parameters_embedding)
                            if 'hits' in results_embedding:
                                aggregated_hits_embedding.extend(results_embedding['hits'])

                            results_gpt_chunked = typesense_client.collections['vendor4'].documents.search(search_parameters_gpt_chunked)
                            if 'hits' in results_gpt_chunked:
                                aggregated_hits_gpt_chunked.extend(results_gpt_chunked['hits'])

                        except Exception as e:
                            logger.error(f"Error during search for chunk: {combined_query[:100]}... : {e}")
                            continue

                    aggregated_hits = aggregated_hits_embedding + aggregated_hits_gpt_chunked
                    if aggregated_hits:
                        if 'vector_distance' in aggregated_hits[0]:
                            sorted_data = sorted(aggregated_hits, key=lambda x: x.get('vector_distance', float('inf')))
                        else:
                            sorted_data = sorted(aggregated_hits, key=lambda x: x.get('text_match', 0), reverse=True)

                        unique_vendors = []
                        for entry in sorted_data:
                            document = entry['document']
                            vendor_name = document.get('vendorName')
                            score = entry.get('vector_distance') if 'vector_distance' in entry else entry.get('text_match')

                            vendor_info = {
                                'vendorName': vendor_name,
                                'serviceoffered': document.get('serviceoffered'),
                                'locationRegion': document.get('locationRegion'),
                                'synergyContracted': document.get('synergyContracted'),
                                'score': score
                            }
                            existing_index = next((i for i, v in enumerate(unique_vendors) if v['vendorName'].lower() == vendor_name.lower()), None)
                            if existing_index is not None:
                                existing_score = unique_vendors[existing_index]['score']
                                if ('vector_distance' in entry and score < existing_score) or ('text_match' in entry and score > existing_score):
                                    unique_vendors[existing_index] = vendor_info
                            else:
                                unique_vendors.append(vendor_info)

                        result[field] = unique_vendors
                else:
                    search_parameters = {
                    'q': value.lower(),
                    'query_by': field, # 'embedding, locationRegion, vendorName'
                    "num_typos": 5
                    }

                    try:
                        results = typesense_client.collections['vendor4'].documents.search(search_parameters)
                        # print(results)
                        t = results['hits']
                        if not t:
                            continue

                        if 'vector_distance' in t[0]:
                            sorted_data = sorted(t, key=lambda x: x['vector_distance'])
                        else:
                            sorted_data = sorted(t, key=lambda x: x['text_match'], reverse = True)
                        
                        unique_vendors = []
                        for entry in sorted_data:
                            document = entry['document']
                            vendor_name = document.get('vendorName')
                            score = entry.get('vector_distance') if 'vector_distance' in entry else entry.get('text_match')

                            vendor_info = {
                                'vendorName': vendor_name,
                                'serviceoffered': document.get('serviceoffered'),
                                'locationRegion': document.get('locationRegion'),
                                'synergyContracted': document.get('synergyContracted'),
                                'score': score
                            }
                            
                            existing_index = next((i for i, v in enumerate(unique_vendors) if v['vendorName'].lower() == vendor_name.lower()), None)

                            if existing_index is not None:
                                existing_score = unique_vendors[existing_index]['score']
                                if ('vector_distance' in entry and score < existing_score) or ('text_match' in entry and score > existing_score): 
                                    unique_vendors[existing_index] = vendor_info
                            else:
                                unique_vendors.append(vendor_info)

                        result[field] = unique_vendors
                    except Exception as e:
                        logger.error(f"Error during search (rest fields): {e}")
        
        vendor_name_sets = [set(entry['vendorName'].lower() for entry in vendors) for vendors in result.values()]
        if vendor_name_sets:
            all_three_match = set.intersection(*vendor_name_sets)
        else:
            all_three_match = set()

        result_all_three = [
            vendor for field_vendors in result.values() for vendor in field_vendors
            if vendor['vendorName'].lower() in all_three_match
        ]

        two_field_matches = [
            vendor for field1, field2 in itertools.combinations(result.values(), 2)
            for vendor in field1 if vendor['vendorName'].lower() in {v['vendorName'].lower() for v in field2}
            and vendor['vendorName'].lower() not in all_three_match
        ]

        single_field_matches = [
            vendor for field_vendors in result.values() for vendor in field_vendors
            if vendor['vendorName'].lower() not in all_three_match
            and all(vendor['vendorName'].lower() not in {v['vendorName'].lower() for v in other_field_vendors} for other_field_vendors in result.values() if other_field_vendors is not field_vendors)
        ]

        result_fin = result_all_three + two_field_matches + single_field_matches
        for _ in result_fin:
            _.pop('score', None)
        return result_fin



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
        "followUp":res.get("followUp","")

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
    category = arguments.get("category","purchase")
    role = arguments.get("role",None)
    imo = arguments.get("imo",None)

    if imo:
        vessel_name,vessel_id = await get_vessel_name(imo)
    else:
        vessel_name = None
        vessel_id = None

    client = MongoDBClient()
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
            "followUp": mongoresult.get("followUp","")
            
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
    min_importance = arguments.get("min_importance",0)
    page_size = arguments.get("page_size",10)
    pagination = arguments.get("pagination",1)
 
    filter_by = []
    if imo: # imo is a string
        filter_by.append(f"imo:{imo}")
    if min_importance: # min_importance is a float
        filter_by.append(f"importance_score:>{min_importance}")
    filter_by.append(f"category:purchase")
 
    if filter_by:
        filter_by = "&&".join(filter_by)
 
 
    if query:
        typesense_query = {"q":query,
                       "query_by":"embedding_text",
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
            "casefile_url":doc["link"]
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
 
##### CASEFILE UPDATE ENDS HERE #####

def convert_unix_dates(document: dict) -> dict:
    """Convert Unix timestamps to human readable format for known date fields."""
    date_fields = [
        'purchaseRequisitionDate',
        'purchaseOrderIssuedDate',
        'orderReadinessDate',
        'poDate',
        'date',
        'dateTime',
        'expenseDate'
    ]
    
    for field in date_fields:
        if field in document:
            try:
                document[field] = dt.datetime.fromtimestamp(document[field]).strftime('%Y-%m-%d %H:%M:%S')
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to convert {field}: {e}")
    
    return document

async def smart_purchase_table_search_handler(arguments: dict):
    """
    Handle smart purchase table search tool.

    Args:
        arguments: Tool arguments following the smart_purchase_table_search schema.

    Returns:
        List containing the results and artifacts as TextContent.
    """
    collection = "purchase"
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
                if value is None:
                    continue
                if key.endswith("_range"):
                    # Handle range filters - dates and amounts
                    field_base = key.replace("_range", "")
                    
                    if "date" in field_base.lower():
                        # Handle date ranges
                        start_date = value.get("start_date")
                        end_date = value.get("end_date")
                        
                        if start_date:
                            start_timestamp = int(dt.datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                            filter_parts.append(f"{field_base}:>={start_timestamp}")
                        if end_date:
                            end_timestamp = int(dt.datetime.strptime(end_date, '%Y-%m-%d').timestamp())
                            filter_parts.append(f"{field_base}:<={end_timestamp}")
                    elif "amount" in field_base.lower():
                        # Handle amount ranges
                        min_amount = value.get("min_amount")
                        max_amount = value.get("max_amount")
                        
                        if min_amount is not None:
                            filter_parts.append(f"{field_base}:>={min_amount}")
                        if max_amount is not None:
                            filter_parts.append(f"{field_base}:<={max_amount}")
                    else:
                        raise ValueError(f"Unsupported range filter field: {field_base}")
                    
                elif isinstance(value, bool):
                    filter_parts.append(f"{key}:={str(value).lower()}")
                elif isinstance(value, str):
                    filter_parts.append(f"{key}:={json.dumps(value).strip('"')}")
                else:
                    filter_parts.append(f"{key}:={value}")

        filter_by = " && ".join(filter_parts) if filter_parts else None

        # Set up query fields based on schema
        query_by = (
            "purchaseRequisitionNumber, prDescription, purchaseRequisitionSummary, qtcNo, purchaseOrderNumber"
        )

        include_fields = ("imo,vesselName,purchaseRequisitionDate,purchaseRequisitionDescription,"
                        "purchaseRequisitionStatus,purchaseOrderAmount,purchaseOrderIssuedDate,"
                        "vendorOrsupplierName,invoiceStatus,invoiceValue,orderReadinessDate,"
                        "purchaseRequisitionNumber,purchaseRequisitionLink,purchaseOrderNumber,"
                        "purchaseOrderLink,purchaseRequisitionType,scanID,scanIDLink,"
                        "purchaseOrderStatus,poCreatedBy,orderType,invoiceApproverName,"
                        "forwarderName,forwarderRemarks,warehouseLocation,cargoType,weight,"
                        "purchaseRequisitionSummary,orderPriority,accountCode")

        query = {
            "q": query_text,
            "query_by": query_by,
            "include_fields": include_fields,
            "per_page": max_results,
        }
        if filter_by:
            query["filter_by"] = filter_by
        if sort_by != "relevance":
            query["sort_by"] = f"{sort_by}:{sort_order}"

        logger.debug(f"[Typesense Query] {query}")

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get('document', {})
            document.pop('embedding', None)
            document = convert_unix_dates(document)  # Convert Unix timestamps to readable dates
            filtered_hits.append({
                'id': document.get('id', document.get('_id')),
                'score': hit.get('text_match', 0),
                'document': document
            })

        documents = [hit['document'] for hit in filtered_hits]
        data_link = get_data_link(documents)
        vessel_name = hits[0]['document'].get('vesselName') if hits else None
        link_header = f"Smart purchase search result for query: '{query_text}'"
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

        artifact_data = get_artifact("smart_purchase_table_search", data_link)
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Smart purchase search artifact for query '{query_text}'",
            format="json"
        )

        return [content, artifact]

    except Exception as e:
        logger.error(f"Error executing smart purchase search: {e}")
        raise ValueError(f"Error performing smart purchase search: {str(e)}")

async def smart_budget_search_handler(arguments: dict):
    """
    Handle smart budget search tool.

    Args:
        arguments: Tool arguments following the smart_budget_search schema.

    Returns:
        List containing the results and artifacts as TextContent.
    """
    collection = "budget"
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
                if value is None:
                    continue
                if key.endswith("_range"):
                    # Handle range filters - dates and amounts
                    field_base = key.replace("_range", "")
                    
                    if "date" in field_base.lower():
                        # Handle date ranges
                        start_date = value.get("start_date")
                        end_date = value.get("end_date")
                        
                        if start_date:
                            start_timestamp = int(dt.datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                            filter_parts.append(f"{field_base}:>={start_timestamp}")
                        if end_date:
                            end_timestamp = int(dt.datetime.strptime(end_date, '%Y-%m-%d').timestamp())
                            filter_parts.append(f"{field_base}:<={end_timestamp}")
                    elif "amount" in field_base.lower():
                        # Handle amount ranges
                        min_amount = value.get("min_amount")
                        max_amount = value.get("max_amount")
                        
                        if min_amount is not None:
                            filter_parts.append(f"{field_base}:>={min_amount}")
                        if max_amount is not None:
                            filter_parts.append(f"{field_base}:<={max_amount}")
                    else:
                        raise ValueError(f"Unsupported range filter field: {field_base}")
                    
                elif isinstance(value, bool):
                    filter_parts.append(f"{key}:={str(value).lower()}")
                elif isinstance(value, str):
                    filter_parts.append(f"{key}:={json.dumps(value).strip('"')}")
                else:
                    filter_parts.append(f"{key}:={value}")

        filter_by = " && ".join(filter_parts) if filter_parts else None

        # Set up query fields based on schema
        query_by = "vesselName,category"
        
        exclude_fields = "embedding,_id"

        query = {
            "q": query_text,
            "query_by": query_by,
            "per_page": max_results,
            "exclude_fields": exclude_fields
        }
        if filter_by:
            query["filter_by"] = filter_by
        if sort_by != "relevance":
            query["sort_by"] = f"{sort_by}:{sort_order}"

        logger.debug(f"[Typesense Query] {query}")

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get('document', {})
            document = convert_unix_dates(document)  # Convert Unix timestamps to readable dates
            filtered_hits.append({
                'id': document.get('id', document.get('_id')),
                'score': hit.get('text_match', 0),
                'document': document
            })

        documents = [hit['document'] for hit in filtered_hits]
        data_link = get_data_link(documents)
        vessel_name = hits[0]['document'].get('vesselName') if hits else None
        imo = hits[0]['document'].get('imo') if hits else None
        
        link_header = f"Smart budget search result for query: '{query_text}'"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)

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

        artifact_data = get_artifact("smart_budget_search", data_link)
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Smart budget search artifact for query '{query_text}'",
            format="json"
        )

        return [content, artifact]

    except Exception as e:
        logger.error(f"Error executing smart budget search: {e}")
        raise ValueError(f"Error performing smart budget search: {str(e)}")

async def smart_expense_search_handler(arguments: dict):
    """
    Handle smart expense search tool.

    Args:
        arguments: Tool arguments following the smart_expense_search schema.

    Returns:
        List containing the results and artifacts as TextContent.
    """
    collection = "expense"
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
                if value is None:
                    continue
                if key.endswith("_range"):
                    # Handle range filters - dates and amounts
                    field_base = key.replace("_range", "")
                    
                    if "date" in field_base.lower():
                        # Handle date ranges
                        start_date = value.get("start_date")
                        end_date = value.get("end_date")
                        
                        if start_date:
                            start_timestamp = int(dt.datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                            filter_parts.append(f"{field_base}:>={start_timestamp}")
                        if end_date:
                            end_timestamp = int(dt.datetime.strptime(end_date, '%Y-%m-%d').timestamp())
                            filter_parts.append(f"{field_base}:<={end_timestamp}")
                    elif "amount" in field_base.lower():
                        # Handle amount ranges
                        min_amount = value.get("min_amount")
                        max_amount = value.get("max_amount")
                        
                        if min_amount is not None:
                            filter_parts.append(f"{field_base}:>={min_amount}")
                        if max_amount is not None:
                            filter_parts.append(f"{field_base}:<={max_amount}")
                    else:
                        raise ValueError(f"Unsupported range filter field: {field_base}")
                    
                elif isinstance(value, bool):
                    filter_parts.append(f"{key}:={str(value).lower()}")
                elif isinstance(value, str):
                    filter_parts.append(f"{key}:={json.dumps(value).strip('"')}")
                else:
                    filter_parts.append(f"{key}:={value}")

        filter_by = " && ".join(filter_parts) if filter_parts else None

        # Set up query fields based on schema
        query_by = "vesselName,accountDescription"
        
        # Include fields relevant for expense data
        exclude_fields = "embedding,vesselId,docId,fleetId,fleetManagerId,technicalSuperintendentId,_id"

        query = {
            "q": query_text,
            "query_by": query_by,
            "exclude_fields": exclude_fields,
            "per_page": max_results,
        }
        if filter_by:
            query["filter_by"] = filter_by
        if sort_by != "relevance":
            query["sort_by"] = f"{sort_by}:{sort_order}"

        logger.debug(f"[Typesense Query] {query}")

        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        hits = results.get("hits", [])
        filtered_hits = []

        for hit in hits:
            document = hit.get('document', {})
            document = convert_unix_dates(document)  # Convert Unix timestamps to readable dates
            filtered_hits.append({
                'id': document.get('id', document.get('_id')),
                'score': hit.get('text_match', 0),
                'document': document
            })

        documents = [hit['document'] for hit in filtered_hits]
        data_link = get_data_link(documents)
        vessel_name = hits[0]['document'].get('vesselName') if hits else None
        imo = hits[0]['document'].get('imo') if hits else None
        
        link_header = f"Smart expense search result for query: '{query_text}'"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)

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

        artifact_data = get_artifact("smart_expense_search", data_link)
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Smart expense search artifact for query '{query_text}'",
            format="json"
        )

        return [content, artifact]

    except Exception as e:
        logger.error(f"Error executing smart expense search: {e}")
        raise ValueError(f"Error performing smart expense search: {str(e)}")
    


async def get_all_vessel_purchase_requisitions_handler(arguments: dict):
    """
    Export all purchase requisitions for a vessel using Typesense's export method.

    Args:
        arguments: Tool arguments following the get_all_vessel_purchase_requisitions schema.

    Returns:
        List containing the export result metadata and artifact as TextContent.
    """
    collection = "purchase"
    session_id = arguments.get("session_id", "testing")
    imo = arguments["imo"]
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")

    try:
        # Compose `filter_by` string from inputs
        filter_parts = [f"imo:={imo}"]

        if start_date:
            start_ts = int(dt.datetime.strptime(start_date, '%Y-%m-%d').timestamp())
            filter_parts.append(f"purchaseRequisitionDate:>={start_ts}")
        if end_date:
            end_ts = int(dt.datetime.strptime(end_date, '%Y-%m-%d').timestamp())
            filter_parts.append(f"purchaseRequisitionDate:<={end_ts}")

        filter_by = " && ".join(filter_parts)

        # Build query for export
        query = {
            "filter_by": filter_by
        }

        logger.debug(f"[Typesense Query] {query}")

        client = TypesenseClient()
        export_result = client.collections[collection].documents.export(query)

        if isinstance(export_result, bytes):
            export_result = export_result.decode("utf-8", errors="replace")
        documents = [json.loads(line) for line in export_result.splitlines() if line.strip()]
        vessel_name = documents[0].get('vesselName') if documents else None
        imo_extracted = documents[0].get('imo') if documents else None
        data_link = get_data_link(documents)
        link_header = f"Purchase requisition export for IMO {imo}"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)

        # Refactored output to match the requested format
        formatted_results = {
            "found": len(documents),
            "out_of": len(documents),
            "page": 1,
            "hits": documents
        }
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2, default=str),
            title=f"Exported purchase requisitions for IMO {imo}",
            format="json"
        )
        artifact_data = get_artifact("get_all_vessel_purchase_requisitions", data_link)
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Purchase requisition export artifact for IMO {imo}",
            format="json"
        )
        return [content, artifact]

    except Exception as e:
        logger.error(f"Error executing purchase requisition export: {e}")
        raise ValueError(f"Error exporting purchase requisitions: {str(e)}")

async def get_vessel_expense_data_handler(arguments: dict):
    """
    Export all expense records for a vessel using Typesense's export method.
    """
    collection = "expense"
    session_id = arguments.get("session_id", "testing")
    imo = arguments["imo"]
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    exclude_fields_str = "_id,docId,fleetId,vesselId,fleetManagerId,technicalSuperintendentId"
    try:
        filter_parts = [f"imo:={imo}"]
        if start_date:
            start_ts = int(dt.datetime.strptime(start_date, '%Y-%m-%d').timestamp())
            filter_parts.append(f"expenseDate:>={start_ts}")
        if end_date:
            end_ts = int(dt.datetime.strptime(end_date, '%Y-%m-%d').timestamp())
            filter_parts.append(f"expenseDate:<={end_ts}")
        filter_by = " && ".join(filter_parts)
        query = {"filter_by": filter_by, "exclude_fields": exclude_fields_str}
        client = TypesenseClient()
        export_result = client.collections[collection].documents.export(query)
        if isinstance(export_result, bytes):
            export_result = export_result.decode("utf-8", errors="replace")
        documents = [json.loads(line) for line in export_result.splitlines() if line.strip()]
        vessel_name = documents[0].get('vesselName') if documents else None
        imo_extracted = documents[0].get('imo') if documents else None
        data_link = get_data_link(documents)
        link_header = f"Expense export for IMO {imo}"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
        
        formatted_results = {
            "found": len(documents),
            "out_of": len(documents),
            "page": 1,
            "hits": documents
        }
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2, default=str),
            title=f"Exported expense records for IMO {imo}",
            format="json"
        )
        artifact_data = get_artifact("get_vessel_expense_data", data_link)
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Expense export artifact for IMO {imo}",
            format="json"
        )
        return [content, artifact]
    except Exception as e:
        logger.error(f"Error executing expense export: {e}")
        raise ValueError(f"Error exporting expense records: {str(e)}")

async def get_complete_vessel_budget_data_handler(arguments: dict):
    """
    Export all budget records for a vessel using Typesense's export method.
    """
    collection = "budget"
    session_id = arguments.get("session_id", "testing")
    imo = arguments["imo"]
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    exclude_fields_str = "_id,docId,fleetId,vesselId,fleetManagerId,technicalSuperintendentId"
    try:
        filter_parts = [f"imo:={imo}"]
        if start_date:
            start_ts = int(dt.datetime.strptime(start_date, '%Y-%m-%d').timestamp())
            filter_parts.append(f"date:>={start_ts}")
        if end_date:
            end_ts = int(dt.datetime.strptime(end_date, '%Y-%m-%d').timestamp())
            filter_parts.append(f"date:<={end_ts}")
        filter_by = " && ".join(filter_parts)
        query = {"filter_by": filter_by, "exclude_fields": exclude_fields_str}
        client = TypesenseClient()
        export_result = client.collections[collection].documents.export(query)
        if isinstance(export_result, bytes):
            export_result = export_result.decode("utf-8", errors="replace")
        documents = [json.loads(line) for line in export_result.splitlines() if line.strip()]
        vessel_name = documents[0].get('vesselName') if documents else None
        imo_extracted = documents[0].get('imo') if documents else None
        data_link = get_data_link(documents)
        link_header = f"Budget export for IMO {imo}"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
        # Refactored output to match the requested format
        formatted_results = {
            "found": len(documents),
            "out_of": len(documents),
            "page": 1,
            "hits": documents
        }
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2, default=str),
            title=f"Exported budget records for IMO {imo}",
            format="json"
        )
        artifact_data = get_artifact("get_complete_vessel_budget_data", data_link)
        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Budget export artifact for IMO {imo}",
            format="json"
        )
        return [content, artifact]
    except Exception as e:
        logger.error(f"Error executing budget export: {e}")
        raise ValueError(f"Error exporting budget records: {str(e)}")
