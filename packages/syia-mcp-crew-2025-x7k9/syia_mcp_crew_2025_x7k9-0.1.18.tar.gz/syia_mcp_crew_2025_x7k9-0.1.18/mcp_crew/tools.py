from mcp_crew.databases import *
import json
from typing import Dict, Any, TypedDict
from enum import Enum
from typing import Union, Sequence, Optional
from pydantic import BaseModel
import mcp.types as types
from mcp_crew import mcp, logger
import requests
from mcp_crew.tool_schema import tool_definitions
import datetime as dt
from .constants import LLAMA_API_KEY, VENDOR_MODEL
from document_parse.main_file_s3_to_llamaparse import parse_to_document_link
import time

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
from dotenv import load_dotenv
load_dotenv()
import snowflake.connector

server_tools = tool_definitions


async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        try:
            # MongoDB tool handlers
            if name == "mongodb_find":
                return await mongodb_find(arguments)
            elif name == "vessel_info_search":
                return await vessel_info_search(arguments)
            elif name == "get_crew_table_schema":
                return await get_typesense_schema(arguments)

            # Typesense tool handlers
            elif name == "get_vessel_details":
                return await get_vessel_details(arguments)
            elif name == "crew_table_query":
                return await typesense_query(arguments)
            elif name == "get_crew_emails":
                return await get_crew_emails(arguments)
            elif name == "get_crew_casefiles":
                return await get_crew_casefiles(arguments)
            elif name == "list_crew_contracts_ending_within":
                return await list_crew_contracts_ending_within(arguments)
            elif name == "get_seafarer_id":
                return await get_seafarer_id(arguments)
            elif name == "get_vessel_crew_details":
                return await get_vessel_crew_details(arguments)

            # Snowflake tool handlers
            
            elif name == "get_seafarer_details":
                return await get_seafarer_details(arguments)
            
            # Document Parsing Tool Handlers
            elif name == "parse_document_link":
                return await parse_document_link(arguments)
            elif name == "list_crew_members":
                return await list_crew_members(arguments)
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            elif name == "google_search":
                return await google_search(arguments)
            
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

async def get_crew_emails(arguments: Dict[str, Any]):
        """
        Handle get crew emails tool
        
        Args:
            arguments: Tool arguments including IMO number and lookback hours
            
        Returns:
            List containing the crew-related emails as TextContent
        """
        imo = arguments.get("imo")
        lookbackHours = arguments.get("lookbackHours")
        per_page = arguments.get("per_page", 10) 
        include_fields = "vesselName,dateTime,subject,importance,casefile,narrative,senderEmailAddress,toRecipientsEmailAddresses,imo,tags"
        tag = arguments.get("tag", "crew")

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
                title=f"Crew-related emails for vessel {imo} in the last {lookbackHours} hours",
                format="json"
            )
            
            return [content]
        except Exception as e:
            logger.error(f"Error retrieving crew-related emails for {imo} in the last {lookbackHours} hours", e)
            raise ValueError(f"Error retrieving crew-related emails: {str(e)}")
        
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

async def get_crew_casefiles(arguments: Dict[str, Any]):
        """
        Handle get crew casefiles tool
        
        Args:
            arguments: Tool arguments including IMO number and lookback hours
            
        Returns:
            List containing the crew-related casefiles as TextContent
        """
        imo = arguments.get("imo")
        lookbackHours = arguments.get("lookbackHours")
        per_page = arguments.get("per_page", 10)
        include_fields = "vesselName,lastCasefileUpdateDate,subject,importance,casefile,narrative,senderEmailAddress,toRecipientsEmailAddresses,imo,link"

        if not imo or not lookbackHours:
            raise ValueError("IMO number and lookback hours are required")
        
        try:
            client = TypesenseClient()
            start_utc  = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=lookbackHours)
            start_ts = int(start_utc.timestamp())  
            collection = "caseFiles"
            
            query = {
                "q": "crew",  # Search for "crew" keyword
                "query_by": "embedding",
                "filter_by": f"imo:{imo} && lastCasefileUpdateDate:>{start_ts}",
                "per_page": per_page,
                "include_fields": include_fields,
                "sort_by": "lastCasefileUpdateDate:desc",
                "prefix": False
            }
            
            # Execute the search
            results = client.collections[collection].documents.search(query)

            hits = results.get("hits", [])
            filtered_hits = []
            link_data = []
            
            for hit in hits:
                document = hit.get('document', {})
                # Remove embedding field to reduce response size
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
                title=f"Crew-related casefiles for vessel {imo} in the last {lookbackHours} hours",
                format="json"   
            )

            artifacts = get_list_of_artifacts("get_crew_casefiles", link_data)
            
            return [content] + artifacts
        except Exception as e:
            logger.error(f"Error retrieving crew-related casefiles for {imo} in the last {lookbackHours} hours", e)
            raise ValueError(f"Error retrieving crew-related casefiles: {str(e)}")



async def list_crew_contracts_ending_within(arguments: Dict[str, Any]):
        """
        Handle list crew contracts ending within a specified time period tool
        
        Args:
            arguments: Tool arguments including IMO number and days
            
        Returns:
            List containing the crew contracts ending within the specified time period as TextContent
        """
        imo = arguments.get("imo")
        days = arguments.get("days")
        per_page = arguments.get("per_page", 250)
        session_id = arguments.get("session_id", "testing")

        if not imo or not days:
            raise ValueError("IMO number and days are required")
        
        try:
            client = TypesenseClient()
            # Calculate cutoff date based on days
            cutoff_date = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)
            cutoff_ts = int(cutoff_date.timestamp())
            
            collection = "crew"
            
            # Update include_fields to match the base URL exactly
            include_fields = "imo,VESSEL_NAME,Name,SIGN_ON_DATE,POSITION_NAME,CREW_CODE,CONTRACT_END_DATE,SIGN_OFF_DATE"
            
            query = {
                "q": "*",                                         # wildcard token
                "query_by": "VESSEL_NAME",                        # Updated to match expected schema
                "filter_by": (
                    f"imo:{imo} && "                             # Removed := to match base URL format
                    f"CONTRACT_END_DATE:<{cutoff_ts}"             # Changed <= to < to match base URL
                ),
                "per_page": per_page,
                "sort_by": "CONTRACT_END_DATE:asc",               # Earliest expiring contracts first
                "include_fields": include_fields
            }
            
            # Execute the search
            logger.info(f"Searching for crew contracts ending within {days} days for vessel {imo}")
            results = client.collections[collection].documents.search(query)

            hits = results.get("hits", [])
            filtered_hits = []
            
            for hit in hits:
                document = hit.get('document', {})
                # Remove embedding field to reduce response size if it exists
                document.pop('embedding', None)
                # Convert date fields to human readable format
                document = convert_crew_dates(document)
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
                vessel_name = hits[0]['document'].get('VESSEL_NAME', None)
            except:
                vessel_name = None
                
            # Insert the data link to mongodb collection
            link_header = f"crew contracts ending within {days} days"
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
            
            # Create TextContent with all required fields in correct structure
            content = types.TextContent(
                type="text",                # Required field
                text=formatted_text,        # The actual text content
                title=f"Crew contracts ending within {days} days for vessel {imo}",
                format="json"
            )
            
            artifact_data = get_artifact("list_crew_contracts_ending_within", data_link)

            artifact = types.TextContent(
                type="text",
                text=json.dumps(artifact_data, indent=2, default=str),
                title=f"Crew contracts ending within {days} days for vessel {imo}",
                format="json"
            )
            return [content, artifact]    
        except Exception as e:
            logger.error(f"Error retrieving crew contracts ending within {days} days for vessel {imo}", e)
            return [types.TextContent(
                type="text",
                text=f"Error retrieving crew contracts: {str(e)}"
            )]        
        
async def list_crew_members(arguments: dict):
    """
    Return the current crew roster for a vessel.
    
    Args:
        arguments: Tool arguments including IMO number and optional per_page
        
    Returns:
        List containing crew member information as TextContent
    """
    imo = arguments.get("imo")
    per_page = 50
    session_id = arguments.get("session_id", "testing")
    
    if not imo:
        raise ValueError("IMO number is required")
    
    try:
        # Set up search parameters for the crew collection
        search_parameters = {
            'q': '*',
            'filter_by': f'imo:{imo}',
            'include_fields': 'imo,VESSEL_NAME,Name,SIGN_ON_DATE,POSITION_NAME,CREW_CODE,CONTRACT_END_DATE,SIGN_OFF_DATE',
            'per_page': per_page
        }
        
        # Execute search
        client = TypesenseClient()
        raw = client.collections['crew'].documents.search(search_parameters)
        hits = raw.get('hits', [])
        
        if not hits:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"No crew members found for vessel with IMO {imo}"
                }, indent=2),
                title=f"Crew roster for IMO {imo}",
                format="json"
            )]
        
        # Process and format results
        crew_members = []
        for hit in hits:
            doc = hit.get('document', {})
            # Convert date fields to human readable format
            doc = convert_crew_dates(doc)
            crew_members.append({
                'imo': doc.get('imo'),
                'vessel_name': doc.get('VESSEL_NAME'),
                'name': doc.get('Name'),
                'position': doc.get('POSITION_NAME'),
                'crew_code': doc.get('CREW_CODE'),
                'sign_on_date': doc.get('SIGN_ON_DATE'),
                'contract_end_date': doc.get('CONTRACT_END_DATE'),
                'sign_off_date': doc.get('SIGN_OFF_DATE')
            })
        
        # Get documents for data link
        documents = [hit['document'] for hit in hits]
        
        # Get data link
        data_link = get_data_link(documents)
        
        # Get vessel name from hits
        vessel_name = hits[0].get('document', {}).get('VESSEL_NAME')
        
        # Insert the data link to mongodb collection
        link_header = "crew members roster"
        insert_data_link_to_mongodb(data_link, link_header, session_id, imo, vessel_name)
        
        response = {
            'vessel_imo': imo,
            'vessel_name': vessel_name,
            'total_crew': len(crew_members),
            'crew_members': crew_members
        }
        
        # Return formatted response
        content = types.TextContent(
            type="text",
            text=json.dumps(response, indent=2),
            title=f"Crew roster for IMO {imo}",
            format="json"
        )
        
        artifact_data = get_artifact("list_crew_members", data_link)

        artifact = types.TextContent(
            type="text",
            text=json.dumps(artifact_data, indent=2, default=str),
            title=f"Crew roster for IMO {imo}",
            format="json"
        )
        return [content, artifact]
    except Exception as e:
        logger.error(f"Error retrieving crew roster for IMO {imo}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": f"Error retrieving crew roster: {str(e)}"
            }, indent=2),
            title=f"Error for IMO {imo}",
            format="json"
        )]
        
async def get_seafarer_id(arguments: Dict[str, Any]):
    """
    Handle get seafarer id tool
    
    Args:
        arguments: Tool arguments including seafarer name
        
    Returns:
        List containing the seafarer id as TextContent
    """
    search_query = arguments.get("query")
    query_by = arguments.get("query_by")
    filter_by = arguments.get("filter_by")

    if filter_by != "":
        filter_by = filter_by.split(" && ")
        filter_by_list = []
        for f in filter_by:
            if f[-10:].count('-') == 2:  # crude check for YYYY-MM-DD at end
                prefix = f[:-10]
                date_str = f[-10:]
                try:
                    timestamp = int(dt.datetime.strptime(date_str, "%Y-%m-%d").timestamp())
                    filter_by_list.append(f"{prefix}{timestamp}")
                except ValueError:
                    filter_by_list.append(f)  # fallback if date parsing fails
            else:
                filter_by_list.append(f)
        final_filter_by = " && ".join(filter_by_list)

    if search_query == "":
        search_query = "*"
    try:
        client = TypesenseClient()
        collection = "crew_details"
        if filter_by != "" and (search_query != "*" or search_query != ""):
            query = {
                "q": search_query,
                "query_by": query_by,
                "filter_by": final_filter_by,
                "include_fields": "CREW_CODE",
                "per_page": 250
                }
        elif filter_by != "" and (search_query == "*" or search_query == ""):
            query = {
                "q": "*",
                "filter_by": final_filter_by,
                "include_fields": "CREW_CODE",
                "per_page": 250
            }
        else:
            query = {
                "q": search_query,
                "query_by": query_by,
                "include_fields": "CREW_CODE",
                "per_page": 250
            }
        results = client.collections[collection].documents.search(query)
        hits = results.get("hits", [])
        filtered_hits = []
        for hit in hits:
            document = hit.get('document', {})
            filtered_hits.append(document.get('CREW_CODE'))
        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": filtered_hits
        }   
        formatted_text = json.dumps(formatted_results, indent=2, default=str)
        if not hits:
            return [types.TextContent(
                type="text",
                text=f"No seafarers found"
            )]
        else:
            content = types.TextContent(
                type="text",
                text=formatted_text,
                title=f"Crew IDs for {query}",
                format="json"
                )
            return [content]
    except Exception as e:
        logger.error(f"Error retrieving seafarer id: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving seafarer id: {str(e)}"
        )]

async def get_vessel_crew_details(arguments: Dict[str, Any]):
    """
    Handle get vessel crew details tool
    
    Args:
        arguments: Tool arguments including vessel imo number
        
    Returns:
        List containing the vessel crew details as TextContent
    """
    imo = arguments.get("imo")
    if not imo:
        raise ValueError("IMO number is required")
    try:
        client = TypesenseClient()
        collection = "crew"
        query = {
                "q": "*",
                "filter_by": f"imo:={imo}",
                "include_fields": "imo,VESSEL_NAME,Name,SIGN_ON_DATE,POSITION_NAME,CREW_CODE,CONTRACT_END_DATE",
                "per_page": 100
            }
        results = client.collections[collection].documents.search(query)
        hits = results.get("hits", [])
        filtered_hits = []
        
        if not hits:
            return [types.TextContent(
                type="text",
                text=f"Error retrieving vessel crew details: {str(e)}"
            )]
        for hit in hits:
            document = hit.get('document', {})
            filtered_hits.append({
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
        formatted_text = json.dumps(formatted_results, indent=2, default=str)
        
        # Create TextContent with all required fields in correct structure
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Crew details for vessel {imo}",
            format="json"   
        )

        return [content]
    except Exception as e:
        logger.error(f"Error retrieving vessel crew details: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving vessel crew details: {str(e)}"
        )]
        
# ------------------- Snowflake Tool Handlers -------------------

async def get_seafarer_details(arguments: Dict[str, Any]):
    """
    Handle get seafarer details tool
    
    Args:
        arguments: Tool arguments including crew_id
        
    Returns:
        List containing the seafarer details as TextContent
    """
    crew_id = arguments.get("crew_id")
    required_fields = arguments.get("required_fields")
    if "CREW_CODE" not in required_fields:
        required_fields = f"CREW_CODE, {required_fields}"
    if "SIGN_ON_DATE" not in required_fields:
        required_fields = f"SIGN_ON_DATE, {required_fields}"

    if not crew_id:
        raise ValueError("Crew id is required")
    try:
        if isinstance(crew_id, list):
            all_results = []
            for id in crew_id:
                try:
                    conn = snowflake.connector.connect(
                        user=os.getenv("SNOWFLAKE_USER"),
                        password=os.getenv("SNOWFLAKE_PASSWORD"),
                        account=os.getenv("SNOWFLAKE_ACCOUNT"),
                        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
                        role=os.getenv("SNOWFLAKE_ROLE"),
                        database=os.getenv("SNOWFLAKE_DATABASE_REPORT"),
                        schema=os.getenv("SNOWFLAKE_SCHEMA_SEARFEARER")
                    )
                    query = f"""
                    WITH base AS (
                            SELECT 
                                {required_fields},
                            FROM revised_base_view
                            WHERE CREW_CODE = '{id}'
                        )
                        SELECT *
                        FROM base
                        ORDER BY SIGN_ON_DATE DESC
                        LIMIT 1;
                    """
                    cur = conn.cursor()
                    cur.execute(query)
                    columns = [desc[0] for desc in cur.description]
                    results = [dict(zip(columns, row)) for row in cur.fetchall()]
                    cur.close()
                    conn.close()
                    formatted_result = {
                        "crew_id": id,
                        "results": results
                    }
                    all_results.append(formatted_result)
                except Exception as e:
                    logger.error(f"Error retrieving seafarer details: {e}")
                    continue
            formatted_results = {
                "all_results": all_results
            }
            return [types.TextContent(
                type="text",
                text=json.dumps(formatted_results, indent=2, default=str),
                title=f"Seafarer details for {crew_id}",
                format="json"
                )]
    except Exception as e:
        logger.error(f"Error retrieving seafarer details: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving seafarer details: {str(e)}"
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
                # error_text = response.text
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
        "pages":str(res.get("pages",[])),
        "index":str(res.get("index",[]))

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
    category = arguments.get("category","crew")
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
    min_importance = arguments.get("min_importance",0)
    page_size = arguments.get("page_size",10)
    pagination = arguments.get("pagination",1)
    category = arguments.get("category","crew")
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
 
