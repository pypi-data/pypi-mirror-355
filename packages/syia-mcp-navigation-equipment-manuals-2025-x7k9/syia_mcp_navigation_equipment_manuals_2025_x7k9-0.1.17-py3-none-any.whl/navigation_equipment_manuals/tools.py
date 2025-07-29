from navigation_equipment_manuals.databases import *
import json
from typing import Dict, Any, TypedDict
from enum import Enum
from typing import Union, Sequence, Optional
from pydantic import BaseModel
import mcp.types as types
from datetime import datetime, timezone
from navigation_equipment_manuals import mcp, logger
import requests
from navigation_equipment_manuals.tool_schema import tool_definitions
import cohere
from navigation_equipment_manuals.constants import COHERE_API_KEY
from .constants import OPENAI_API_KEY, PERPLEXITY_API_KEY


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
            if name == "get_table_schema":
                return await get_typesense_schema(arguments)

            # Typesense tool handlers
            # elif name == "typesense_query":
            #     return await typesense_query(arguments)
            elif name == "smart_navigation_manual_search":
                return await smart_navigation_manual_search(arguments)
            elif name == "list_equipment_manufacturers":
                return await fetch_list_of_makers(arguments)
            elif name == "list_navigation_equipment_types":
                return await fetch_list_of_equipments(arguments)
            elif name == "list_navigation_equipment_models":
                return await fetch_list_of_models(arguments)
            elif name == "find_equipment_manuals":
                return await fetch_list_of_manuals(arguments)
            elif name == "search_manual_content":
                return await semantic_query_search(arguments)
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            elif name == "google_search":
                return await google_search(arguments)
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise ValueError(f"Error calling tool {name}: {str(e)}")


# Helpful functions


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
        "query": "Search results from Navigational Equipment Manuals",
        "searchEngine": "general"
      },
      "visual": {
        "icon": "search",
        "color": "#34A853"
      }
    },
    "content": "Search results for: Search results from Navigational Equipment Manuals",
    "artifacts": [
      {
        "id": "artifact_search_1744192295406_875",
        "type": "search_results",
        "content": {
          "query": "Search results from Navigational Equipment Manuals",
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


def get_list_of_artifacts(function_name: str, results: list):
    """
    Handle get artifact tool using updated artifact format
    """
    artifacts = []
    for i, result in enumerate(results):
        url = result.get("url")
        title = result.get("title")
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
                        "url": title,
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
                title=title,
                format="json"
            )
            artifacts.append(artifact)
    return artifacts


def format_hit(hit: Dict, doc: Dict) -> Dict:
    """Format a single search hit based on intent"""
    hit_data = {
        "relevance_score": round(hit.get("text_match", 0), 3) if hit.get("text_match") else None,
        "document_info": {
            "name": doc.get("documentName", "Unknown"),
            "type": doc.get("documentType", "Unknown"),
            "page": doc.get("pageNumber", "Unknown")
        },
        "equipment_info": {
            "maker": doc.get("maker", "Unknown"),
            "model": doc.get("model", "Unknown"),
            "type": doc.get("equipment", "Unknown")
        },
        "location": {
            "chapter": doc.get("chapter", ""),
            "section": doc.get("section", ""),
            "page": doc.get("pageNumber", "")
        }
    }

    content = doc.get("originalText", doc.get("embText", ""))
    hit_data["content"] = content

    if "highlights" in hit:
        hit_data["highlights"] = hit["highlights"]

    return hit_data

# ------------------- MongoDB Tool Handlers -------------------


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
#         # Format the results
#         formatted_results = {
#             "found": results.get("found", 0),
#             "out_of": results.get("out_of", 0),
#             "page": results.get("page", 1),
#             "hits": [hit.get("document") for hit in results.get("hits", [])]
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

async def smart_navigation_manual_search(arguments: Dict[str, Any]):
    """Universal search tool for navigation manuals with intelligent query processing."""
    try:
        collection = "navigation_manuals"
        client = TypesenseClient()

        # Extract arguments with defaults
        query = arguments.get("query", "")
        search_type = arguments.get("search_type", "hybrid" if query else "browse")
        filters = arguments.get("filters", {})
        max_results = arguments.get("max_results", 7)

        def sanitize_filter_value(value: str) -> str:
            # Define a regex pattern of removable/special characters
            # pattern = r"[()\[\]{}&|\":',=]"
            pattern = r"[()\[\]{}&|:,=]"
            cleaned = re.sub(pattern, " ", value).strip()
            return json.dumps(cleaned)  # safely quoted for Typesense

        # Build filter string from filters dict
        filter_parts = []
        for field, value in filters.items():
            if value:
                if field == "page_range" and isinstance(value, list) and len(value) == 2:
                    filter_parts.append(f"pageNumber:>={value[0]} && pageNumber:<={value[1]}")
                else:
                    filter_parts.append(f"{field}:{sanitize_filter_value(value)}")
        filter_string = " && ".join(filter_parts) if filter_parts else None

        # Enhance query based on intent
        enhanced_query = query

        # # Build the search query
        # if search_type == "browse":
        #     search_query = {
        #         "q": "*",
        #         "query_by": "embText",
        #         "per_page": max_results,
        #         "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
        #     }
        # elif search_type == "semantic":
        search_query = {
            "q": enhanced_query,
            "query_by": "embedding",
            "prefix": False,
            "per_page": max_results,
            "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
        }
        # elif search_type == "keyword":
        #     search_query = {
        #         "q": enhanced_query,
        #         "query_by": "embText,section,chapter",
        #         "per_page": max_results,
        #         "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
        #     }
        # else:
        #     search_query = {
        #         "q": enhanced_query,
        #         "query_by": "embText,embedding",
        #         "prefix": False,
        #         "per_page": max_results,
        #         "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
        #     }

        # # Add filters if any
        if filter_string:
            search_query["filter_by"] = filter_string

        # Add sorting for browse mode
        # if search_type == "browse" and not query:
        # search_query["sort_by"] = "pageNumber:asc"

        # Execute search
        results = client.collections[collection].documents.search(search_query)
        hits = results.get("hits", [])
        total_found = results.get("found", 0)
        all_hits = hits


        # If we have results and <= 50, apply Cohere reranking
        if all_hits and COHERE_API_KEY and len(all_hits) <= 50:
            try:
                docs_with_originals = []
                for hit in all_hits:
                    document = hit.get("document", {})
                    if "originalText" in document:
                        docs_with_originals.append({
                            "text": document["originalText"],
                            "original": document
                        })
                docs = [doc["text"] for doc in docs_with_originals]
                co = cohere.ClientV2(COHERE_API_KEY)
                reranked = co.rerank(
                    model="rerank-v3.5",
                    query=query,
                    documents=docs,
                    top_n=min(5, len(docs))
                )
                top_results = [docs_with_originals[result.index]["original"] for result in reranked.results]
                # Collect link data for artifact
                link_data = []
                for doc in top_results:
                    if doc.get("documentLink"):
                        link_data.append({
                            "title": doc.get("documentName"),
                            "url": doc.get("documentLink")
                        })
                artifact_data = get_list_of_artifacts("smart_navigation_manual_search",link_data)
                content = types.TextContent(
                    type="text",
                    text=json.dumps(top_results, indent=2),
                    title="Reranked Company Manual Search Results",
                    format="json"
                )
                return [content]+ artifact_data
            except Exception as e:
                logger.error(f"Error in Cohere reranking: {e}")

        # Format results
        formatted_results = {
            "search_metadata": {
                "query": query,
                "search_type": search_type,
                "filters_applied": filters,
                "total_found": results.get("found", 0),
                "returned": min(results.get("found", 0), max_results)
            },
            "results": []
        }

        for hit in results.get("hits", []):
            doc = hit["document"]
            hit_data = format_hit(hit, doc)
            formatted_results["results"].append(hit_data)

        title = f"Search Results: {query[:50]}..." if query else "Browse Results"

        content =types.TextContent(
            type = "text",
            text = json.dumps(formatted_results, indent=2),
            title = title,
            format = "json"
        )

        link_data = []
        for document in results["hits"]:
            link_data.append({
                "title": document['document'].get("documentName"),
                "url": document['document'].get("documentLink")
            })
        artifacts = get_list_of_artifacts("smart_navigation_manual_search", link_data)

        return [content] + artifacts
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving search results: {str(e)}",
            title="Error",
            format="json"
        )]











    
async def fetch_list_of_makers(arguments: Dict[str, Any]):
        # Query to get unique makers from the navigation_manuals collection

        collection = "navigation_manuals"
        client = TypesenseClient()
        query = {
            "q": "*",
            "query_by": "maker",
            "group_by": "maker",
            "per_page": 100
        }
        results = client.collections[collection].documents.search(query)
        
        # Extract unique makers from results
        makers = []
        if "grouped_hits" in results:
            makers = [group["group_key"][0] for group in results["grouped_hits"]]
        
        return [types.TextContent(
            type="text", 
            text=json.dumps(makers, indent=2), 
            title="List of Navigation Equipment Manufacturers", 
            format="json"
        )]

async def fetch_list_of_equipments(arguments: Dict[str, Any]):
        
        collection = "navigation_manuals"
        filters = []
        
        if "maker" in arguments and arguments["maker"]:
            filters.append(f"maker:={arguments['maker']}")
            
        # Create search parameters with proper handling for None values
        query = {
            "q": "*", 
            "query_by": "equipment", 
            "group_by": "equipment", 
            "per_page": 100,
            "include_fields": "equipment"
        }
        
        # Only add filter_by if we have filters
        if filters:
            query["filter_by"] = " && ".join(filters)
            
        # Query to get unique equipment types
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        # Extract equipment values from grouped_hits
        equipments = [group["group_key"][0] for group in results.get("grouped_hits", [])]
        
        return [types.TextContent(
            type="text", 
            text=json.dumps(equipments, indent=2), 
            title="List of Navigation Equipment Types", 
            format="json"
        )]

async def fetch_list_of_models(arguments: Dict[str, Any]):
        collection = "navigation_manuals"
        filters = []
        
        if "maker" in arguments and arguments["maker"]:
            filters.append(f"maker:={arguments['maker']}")
        if "equipment" in arguments and arguments["equipment"]:
            filters.append(f"equipment:={arguments['equipment']}")
            
        # Create search parameters with proper handling for None values
        query = {
            "q": "*", 
            "query_by": "model",
            "group_by": "model",
            "per_page": 100,
            "include_fields": "model,maker,equipment,documentType"
        }
        
        # Only add filter_by if we have filters
        if filters:
            query["filter_by"] = " && ".join(filters)
            
        # Query to get unique models with additional fields
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)
        
        # Extract relevant data from results
        model_data = []
        seen_models = set()
        
        if "grouped_hits" in results:
            for group in results["grouped_hits"]:
                # Get the model name from the group key
                model = group["group_key"][0]
                
                # Get the first document in the group to extract other fields
                if group["hits"] and "document" in group["hits"][0]:
                    doc = group["hits"][0]["document"]
                    
                    # Only include fields not used as filters
                    entry = {"model": model}
                    
                    if not arguments.get("maker"):
                        entry["maker"] = doc.get("maker", "")
                    if not arguments.get("equipment"):
                        entry["equipment"] = doc.get("equipment", "")
                    
                    # Always include document type
                    entry["available_manuals"] = doc.get("documentType", "")
                    
                    model_data.append(entry)
                    seen_models.add(model)
        
        return [types.TextContent(
            type="text", 
            text=json.dumps(model_data, indent=2), 
            title="List of Navigation Equipment Models", 
            format="json"
        )]

async def fetch_list_of_manuals(arguments: Dict[str, Any]):
        collection = "navigation_manuals"

        maker = arguments.get("maker")
        model = arguments.get("model")
        equipment = arguments.get("equipment")
        max_results = 100

        filters = []
        if maker:
            filters.append(f"maker:{maker}")
        if model:
            filters.append(f"model:{model}")
        if equipment:
            filters.append(f"equipment:{equipment}")
        
        if not filters:
            return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": "At least one filter (maker, model, or equipment) must be provided to avoid fetching all documents",
                "suggestion": "Please specify at least one of: maker, model, or equipment type",
                "available_actions": "try using other tools to get the maker / model / equipment type",
                "parameters_received": {
                    "maker": maker,
                    "model": model,
                    "equipment": equipment,
                    "max_results": max_results
                }
            }, indent=2),
            title="Error: No Filters Provided",
            format="json"
        )]


        
        # Create search parameters
        query = {
            "q": "*",
            "group_by": "documentName",
            "per_page": max_results,
            "include_fields": "documentName,documentType,documentLink",
            "filter_by": " && ".join(filters)
        }
        
        # Execute search
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)

        # Extract results from grouped hits
        manuals = [
            {
                "documentName": group["group_key"][0],
                "documentType": group["hits"][0]["document"].get("documentType", ""),
                "documentLink": group["hits"][0]["document"].get("documentLink", "")
            }
            for group in results.get("grouped_hits", [])
        ]

        link_data = []
        for document in manuals:
            link_data.append({
                "title": document.get("documentName"),
                "url": document.get("documentLink")
            })
        artifacts = get_list_of_artifacts("find_equipment_manuals", link_data)
        
        content = types.TextContent(
            type="text",
            text=json.dumps(manuals, indent=2),
            title="List of Navigation Equipment Manuals",
            format="json"
        )

        return [content] + artifacts

async def semantic_query_search(arguments: Dict[str, Any]):
        collection = "navigation_manuals"
        filters = []
        user_query = arguments.get("user_query", "")
        cohere_limit = 5
        
        if "maker" in arguments and arguments["maker"]:
            filters.append(f"maker:={arguments['maker']}")
        if "model" in arguments and arguments["model"]:
            filters.append(f"model:={arguments['model']}")
        if "equipment" in arguments and arguments["equipment"]:
            filters.append(f"equipment:={arguments['equipment']}")
        if "manual_type" in arguments and arguments["manual_type"]:
            if arguments["manual_type"] == "installation":
                filters.append(f"documentType:=Installation Manual")
            elif arguments["manual_type"] == "operation":
                filters.append(f"documentType:=Operation Manual OR documentType:=Instruction Manual")
            elif arguments["manual_type"] == "service":
                filters.append(f"documentType:=Service Manual")
            else:
                raise ValueError(f"Invalid manual type: {arguments['manual_type']}")
        
        # Create search parameters with proper handling for None values
        query = {
            "q": user_query if user_query else "*", 
            "query_by": "embedding,embText",
            "per_page": 10,  # Increased to have more candidates for reranking
            "include_fields": "documentName,documentType,documentLink,equipment,maker,model,originalText",
            "prefix": False
        }
        
        # Only add filter_by if we have filters
        if filters:
            query["filter_by"] = " && ".join(filters)
            
        client = TypesenseClient()
        results = client.collections[collection].documents.search(query)
        
        # If we have results and a user query, apply Cohere reranking
        if results["hits"] and user_query and COHERE_API_KEY:
            try:
                # Collect documents with their original text for reranking
                docs_with_originals = []
                for hit in results["hits"]:
                    if "originalText" in hit["document"]:
                        docs_with_originals.append({
                            "text": hit["document"]["originalText"],
                            "original": hit["document"]
                        })
                
                # Extract just the text for reranking
                docs = [doc["text"] for doc in docs_with_originals]
                
                # Initialize Cohere client
                co = cohere.ClientV2(COHERE_API_KEY)
                
                # Perform reranking
                reranked = co.rerank(
                    model="rerank-v3.5",
                    query=user_query,
                    documents=docs,
                    top_n=cohere_limit
                )
                
                # Get the top results based on reranking
                top_results = [docs_with_originals[result.index]["original"] for result in reranked.results]

                link_data = []
                for document in top_results:
                    link_data.append({
                        "title": document.get("documentName"),
                        "url": document.get("documentLink")
                    })
                artifacts = get_list_of_artifacts("search_manual_content", link_data)
                content = types.TextContent(
                    type="text",
                    text=json.dumps(top_results, indent=2),
                    title="Reranked Navigation Manual Search Results",
                    format="json"
                )

                return [content] + artifacts
            except Exception as e:
                logger.error(f"Error in Cohere reranking: {e}")
                # Fall back to original results if reranking fails
        hits = results["hits"]
        # Return original results if no reranking was done  

        link_data = []
        for hit in hits:
            doc = hit.get("document", {})
            if doc.get("documentLink"):
                link_data.append({
                    "title": doc.get("documentName"),
                    "url": doc.get("documentLink")
                })
        artifacts = get_list_of_artifacts("search_manual_content", link_data)
        content = types.TextContent(
            type="text", 
            text=json.dumps([hit["document"] for hit in results["hits"]], indent=2), 
            title="Navigation Manual Search Results", 
            format="json"
        )
        return [content] + artifacts



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
        
        

   
