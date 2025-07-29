from asyncio import sleep
from mcp_casefile.databases import *
import json
from typing import Dict, Any, TypedDict
from enum import Enum
from typing import Union, Sequence, Optional
import mcp.types as types
import datetime as dt
from mcp_casefile import mcp, logger
import requests
from mcp_casefile.tool_schema import tool_definitions
from pathlib import Path   
from playwright.async_api import async_playwright
from mcp_casefile.utils import timestamped_filename
from dotenv import load_dotenv
import os   
import re
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

import os
import time
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Union
from pymongo import MongoClient
from . import logger
from typing import Dict, Any, List, Union, Optional
import mcp.types as types # Assumes types.TextContent is defined or imported elsewhere

from typing import Dict, Any
import json

from .constants import OPENAI_API_KEY, LLAMA_API_KEY, VENDOR_MODEL, PERPLEXITY_API_KEY
from document_parse.main_file_s3_to_llamaparse import parse_to_document_link

from utils.llm import LLMClient

from pymongo import MongoClient
from datetime import datetime, timezone
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
from .constants import MONGODB_URI, MONGODB_DB_NAME, OPENAI_API_KEY

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

server_tools = tool_definitions

def register_tools():
    @mcp.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return server_tools

    @mcp.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        try:
            # MongoDB tool handlers
            if name == "get_casefile_index":
                return await get_casefile_index(arguments)
            elif name == "get_casefile_pages":
                return await get_casefile_pages(arguments)
            elif name == "get_latest_plan":
                return await get_latest_plan(arguments)
            # Typesense tool handlers
            elif name == "search_casefile":
                return await search_casefile(arguments)
            elif name == "write_plan":
                return await write_plan(arguments)
            elif name == "get_vessel_details":
                return await get_vessel_details(arguments)

            # Document parser tool handler
            elif name == "parse_document_link":
                return await parse_document_link(arguments)

            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
              
            elif name == "google_search":
                return await google_search(arguments)
            else: 
                raise ValueError(f"Unknown tool: {name}")
            
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise

# ------------------- MongoDB Tool Handlers -------------------

async def get_casefile_index(arguments: dict) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """
    Get the casefile index
    
    Args:
        arguments (dict): Contains casefile_id
        
    Returns:
        Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]: The casefile index
    """
    casefile_id = arguments.get("casefile_id")
    if not casefile_id:
        raise ValueError("casefile_id is required")
    
    limit = int(arguments.get("limit", 10))
    next_iter = int(arguments.get("next_iter", 0))
    
    try:
        logger.info(f"Getting casefile index for: {casefile_id}, limit: {limit}, next_iter: {next_iter}")
        
        mongo_client = MongoDBClient()
        db = mongo_client.db
        # Example query - customize based on your schema
        collection = "casefiles"

        pipeline_length = [
            {"$match": {"_id": ObjectId(casefile_id)}},
            {"$project": {"index": {"$size": "$index"}}}
        ]
        
        # Execute the query
        result = await db[collection].aggregate(pipeline_length).to_list(length=1)
        
        if not result:
            return [types.TextContent(
                type="text",
                text=f"No casefile found with ID: {casefile_id}"
            )]
        
        total_entries = result[0]['index']

        if next_iter == 0:
            skip = max(0, total_entries - limit)
        else:
            skip = max(0, total_entries - (limit * (next_iter + 1)))
            if skip < 0:
                skip = 0
        
        entries_to_take = min(limit, total_entries - skip)
        if entries_to_take <= 0:
            return [types.TextContent(
                type="text",
                text=f"No more index entries to retrieve for casefile ID: {casefile_id}"
            )]
        
        pipeline_fetch = [
            {"$match": {"_id": ObjectId(casefile_id)}},
            {"$project": {
                "index": {"$slice": ["$index", skip, entries_to_take]}, 
                "category": 1,
                "imo": 1,
                "_id": 1
                }}
        ]

        result = await db[collection].aggregate(pipeline_fetch).to_list(length=1)
        if not result:
            return [types.TextContent(
                type="text",
                text=f"Failed to retrieve index entries for casefile ID: {casefile_id}"
            )]
        document = result[0]
        response = {
            "casefile_id": str(document["_id"]),
            "index": document.get("index", []),
            "category": document.get("category"),
            "imo": document.get("imo"),
            "total_entries": total_entries,
            "current_batch": next_iter,
            "total_batches": max(1, (total_entries + limit - 1) // limit),
            "has_more": skip > 0
        }
        
        formatted_text = json.dumps(response, indent=2, default=str)
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Casefile Index for {casefile_id}",
            format="json"
        )
        return [content]
    except Exception as e:
        logger.error(f"Error getting casefile index: {e}")
        raise ValueError(f"Error getting casefile index: {str(e)}")






async def get_casefile_pages(arguments: dict) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """
    Get the casefile pages
    
    Args:
        arguments (dict): Contains casefile_id
        
    Returns:
        Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]: The casefile pages
    """
    casefile_id = arguments.get("casefile_id")
    page_list = arguments.get("pages", [])
    if not isinstance(page_list, list) or not page_list:
        raise ValueError("pages must be a non-empty list")

    try:
        page_list = sorted(set(int(p) for p in page_list))
    except (ValueError, TypeError):
        raise ValueError("All entries in 'pages' must be integers or castable to integers")


    
    if not casefile_id:
        raise ValueError("casefile_id is required")
    
    try:
        logger.info(f"Getting casefile pages for: {casefile_id}, pages: {page_list}")
        
        mongo_client = MongoDBClient()
        db = mongo_client.db
        # Example query - customize based on your schema
        collection = "casefiles"

        doc = await db[collection].find_one({"_id": ObjectId(casefile_id)}, {"pages": {"$slice": 1}})
        if not doc:
            return [types.TextContent(type = "text", text = f"No casefile found with ID: {casefile_id}")]
        if "pages" not in doc or not isinstance(doc["pages"], list):
            return [types.TextContent(type = "text", text = "The 'pages' field is missing or not an array.")]
        
        min_index = min(page_list)
        max_index = max(page_list)

        logger.info(f"Page range requested: {min_index} to {max_index}")

        pipeline = [
            {"$match": {"_id": ObjectId(casefile_id)}},
            {"$project": {
                "pages": {"$slice": ["$pages", min_index, max_index - min_index + 1]},
                "_id": 0
            }}
        ]

        cursor = db[collection].aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if not result:
            return [types.TextContent(type="text", text="No pages found for the given casefile ID.")]
        
        sliced_pages = result[0].get("pages", [])
        offset = min_index

        requested_pages = []
        for page_num in page_list:
            i = page_num - offset
            if 0 <= i < len(sliced_pages):
                requested_pages.append(sliced_pages[i])

        if not requested_pages:
            return [types.TextContent(type="text", text="No pages matched the requested indices")]
        
        response = {
            "casefile_id": casefile_id,
            "pages_requested": page_list,
            "pages_returned": requested_pages
        }
        
        formatted_text = json.dumps(response, indent=2, default=str)

        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Casefile Pages for {casefile_id}",
            format="json"
        )
        return [content]
    except Exception as e:
        logger.error(f"Error getting casefile pages: {e}")
        raise ValueError(f"Error getting casefile pages: {str(e)}")

async def get_latest_plan(arguments: dict) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """
    Get the latest plan
    
    Args:
        arguments (dict): Contains casefile_id
        
    Returns:
        Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]: The latest plan
    """
    casefile_id = arguments.get("casefile_id")
    if not casefile_id:
        raise ValueError("casefile_id is required")
    
    try:
        logger.info(f"Getting latest plan for casefile: {casefile_id}")
        
        mongo_client = MongoDBClient()
        db = mongo_client.db
        # Example query - customize based on your schema
        collection = "casefiles"

        document = await db[collection].find_one({"_id": ObjectId(casefile_id)}, {"casefilePlans": 1})

        if not document:
            return [types.TextContent(type="text", text=f"No casefile found with ID: {casefile_id}")]
        
        plans = document.get("casefilePlans", [])
        if not plans or not isinstance(plans, list):
            return [types.TextContent(type="text", text="No plans found for the casefile")]
        
        sorted_plans = sorted(plans, key = lambda p: p.get("dateTime", ""), reverse=True)
        latest_plan = sorted_plans[0] 

        result = {
            "casefile_id": casefile_id,
            "latest_plan": {
                "dateTime": latest_plan.get("dateTime"),
                "flag": latest_plan.get("flag"),
                "plan": latest_plan.get("plan")
            }
        }

        formatted_text = json.dumps(result, indent=2, default=str)
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Latest Plan for {casefile_id}",
            format="json"
        )
        
        return [content]
    except Exception as e:
        logger.error(f"Error getting latest plan: {e}")
        raise ValueError(f"Error getting latest plan: {str(e)}")
    

async def write_plan(arguments: dict) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """
    Appends a new plan entry to the `casefilePlans` array of a given casefile.

    Args:
        arguments (dict): Must contain:
          - 'casefile_id': str (Mongo ObjectId as hex string)
          - 'plan': str (markdown content to append)
    
    Returns:
        TextContent confirming the update.
    """
    casefile_id = arguments.get("casefile_id")
    plan_text = arguments.get("plan")

    if not casefile_id or not plan_text:
        raise ValueError("both casefile_id and plan are required")
    
    try:
        logger.info(f"Appending a new plan for casefile: {casefile_id}")
        
        mongo_client = MongoDBClient()
        db = mongo_client.db
        # Example query - customize based on your schema
        collection = "casefiles"

        casefile = await db[collection].find_one({"_id": ObjectId(casefile_id)})

        if not casefile:
            return [types.TextContent(type="text", text=f"No casefile found with ID: {casefile_id}")]
        
        now = datetime.now(timezone.utc)
        new_plan = {
            "dateTime": now,
            "flag": "updated plan for something",
            "plan": plan_text
        }

        await db[collection].update_one(
            {"_id": ObjectId(casefile_id)},
            {"$push": {"casefilePlans": new_plan}}
        )

        result = {
            "status": "success",
            "casefile_id": casefile_id,
            "appended_plan": new_plan
        }
        formatted_text = json.dumps(result, indent=2, default=str)

        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Plan written to casefile {casefile_id}",
            format="json"
        )
        
        return [content]
    except Exception as e:
        logger.error(f"Error getting latest plan: {e}")
        raise ValueError(f"Error getting latest plan: {str(e)}")
    
#Helper functions

def get_reference_artifact(results: list):
    """
    Get the reference artifact
    """

    totalResults = len(results)

    artifact = {
    "type": "agent_acting",
    "id": "msg_search_1744192295407_389",
    "parentTaskId": "1311e759-917a-472f-9d14-e0dcf005773b",
    "timestamp": 1744192295407,
    "agent": {
      "id": "agent_browser_researcher",
      "name": "BROWSER",
      "type": "researcher"
    },
    "messageType": "action",
    "action": {
      "tool": "search",
      "operation": "searching",
      "params": {
        "query": "Search results from Email Casefiles",
        "searchEngine": "general"
      },
      "visual": {
        "icon": "search",
        "color": "#34A853"
      }
    },
    "content": "Search results for: Search results from Email Casefiles",
    "artifacts": [
      {
        "id": "artifact_search_1744192295406_875",
        "type": "search_results",
        "content": {
          "query": "Search results from Email Casefiles",
          "totalResults": totalResults,
          "results": results
        },
        "metadata": {
          "searchEngine": "general",
          "searchTimestamp": 1744192295407,
          "responseTime": "0.70"
        }
      }
    ],
    "status": "completed",
    "originalEvent": "tool_result",
    "sessionId": "1311e759-917a-472f-9d14-e0dcf005773b",
    "agent_type": "browser",
    "state": "running"
  }
    return artifact

import time

def get_artifact(function_name: str, results: list):
    """
    Handle get artifact tool using updated artifact format
    """
    url_list = [i['url'] for i in results]
    artifacts = []
    for url in url_list:
        if url:
            a = {
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
            artifacts.append(a)

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
        "artifacts": artifacts,
        "status": "completed"
    }
    return artifact

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

# ------------------- Typesense Tool Handlers -------------------

# async def search_casefile(arguments: dict) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
#     """
#     Search for the required casefile
    
#     Args:
#         arguments (dict): Contains vessel_name
        
#     Returns:
#         Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]: The search results
#     """
#     query = arguments.get("query")
#     imo = arguments.get("imo", None)
#     per_page = arguments.get("per_page", 10)
#     page = arguments.get("page", 1)

#     if not query:
#         raise ValueError("query is required")
    
#     try:
#         logger.info(f"Searching for casefiles related to query: {query}, per_page: {per_page}, page: {page}")
        
#         # Example query parameters
#         collection = "emailCasefile"
#         include_fields = 'casefileInitiationDate,vesselName,_id,lastCasefileUpdateDate,casefile,summary,link'
#         payload = {
#             "q": query,
#             "query_by": "embedding_text, embedding, vesselName",
#             "include_fields": include_fields,
#             "exclude_fields": "embedding",
#             "per_page": per_page,
#             "page": page,
#             'prefix': False
#         }

#         if imo:
#             payload["filter_by"] = f"imo:={int(imo)}"
#         # Execute the search
#         client = TypesenseClient()
#         results = client.collections[collection].documents.search(payload)
        
#         hits = results.get("hits", [])
#         filtered_hits = []
        
#         for hit in hits:
#             document = hit.get('document', {})
#             # Remove embedding field to reduce response size if it exists
#             document.pop('embedding', None)
#             # Convert date fields to human readable format
#             document = convert_casefile_dates(document)
#             filtered_hits.append({
#                'id': document.get('id'),
#                'score': hit.get('text_match', 0),
#                'document': document
#             })
        
#         total_found = results.get("found", 0)
#         has_more = (page * per_page) < total_found
      
#         # Format the results
#         formatted_results = {
#                 "found": total_found,
#                 "out_of": results.get("out_of", 0),
#                 "page": page,
#                 "per_page": per_page,
#                 "has_more": has_more,
#                 "hits": filtered_hits
#             }
#         documents = [i['document'] for i in hits]
#         link_data = []

#         for document in documents:
#             link_data.append({
#                 "title": document.get("casefile"),
#                 "url": document.get("link",None)
#             })

#         artifact_data = get_reference_artifact(link_data)

#         formatted_text = json.dumps(formatted_results, indent=2, default=str)
#         content = types.TextContent(
#             type="text",
#             text=formatted_text,
#             title=f"Casefile Search Results for {query} (Page {page})",
#             format="json"
#         )

#         artifact = types.TextContent(
#             type="text",
#             text=json.dumps(artifact_data, indent=2, default=str),
#             title=f"Casefile Search Results for {query} (Page {page})",
#             format="json"
#         )   

        
#         return [content, artifact]
#     except Exception as e:
#         logger.error(f"Error searching for casefiles: {e}")
#         raise ValueError(f"Error searching for casefiles: {str(e)}")

async def search_casefile(arguments: dict) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
    """
    Search for the required casefile
    
    Args:
        arguments (dict): Contains vessel_name
        
    Returns:
        Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]: The search results
    """
    query = arguments.get("query")
    imo = arguments.get("imo", None)
    per_page = arguments.get("per_page", 10)
    page = arguments.get("page", 1)

    if not query:
        raise ValueError("query is required")
    
    try:
        logger.info(f"Searching for casefiles related to query: {query}, per_page: {per_page}, page: {page}")
        
        # Example query parameters
        collection = "emailCasefile"
        include_fields = 'casefileInitiationDate,vesselName,_id,lastCasefileUpdateDate,casefile,summary,link'
        payload = {
            "q": query,
            "query_by": "embedding_text, embedding, vesselName",
            "include_fields": include_fields,
            "exclude_fields": "embedding",
            "per_page": per_page,
            "page": page,
            'prefix': False
        }

        if imo:
            payload["filter_by"] = f"imo:={int(imo)}"
        # Execute the search
        client = TypesenseClient()
        results = client.collections[collection].documents.search(payload)
        
        hits = results.get("hits", [])
        filtered_hits = []
        
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
        
        total_found = results.get("found", 0)
        has_more = (page * per_page) < total_found
      
        # Format the results
        formatted_results = {
                "found": total_found,
                "out_of": results.get("out_of", 0),
                "page": page,
                "per_page": per_page,
                "has_more": has_more,
                "hits": filtered_hits
            }
        documents = [i['document'] for i in hits]
        link_data = []

        for document in documents:
            link_data.append({
                "title": document.get("casefile"),
                "url": document.get("link",None)
            })

        artifacts = get_list_of_artifacts(query, link_data)

        formatted_text = json.dumps(formatted_results, indent=2, default=str)
        content = types.TextContent(
            type="text",
            text=formatted_text,
            title=f"Casefile Search Results for {query} (Page {page})",
            format="json"
        )
        
        return [content] + artifacts
    except Exception as e:
        logger.error(f"Error searching for casefiles: {e}")
        raise ValueError(f"Error searching for casefiles: {str(e)}")


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
