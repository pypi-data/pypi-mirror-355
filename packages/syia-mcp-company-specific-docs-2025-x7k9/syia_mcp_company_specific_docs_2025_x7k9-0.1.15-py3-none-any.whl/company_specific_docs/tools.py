from company_specific_docs.databases import *
import json
from typing import Dict, Any, TypedDict
from enum import Enum
from typing import Union, Sequence, Optional 
from pydantic import BaseModel
import mcp.types as types
from company_specific_docs import mcp, logger
import requests
from company_specific_docs.tool_schema import tool_definitions
import datetime
from typing import Any, Dict, List, Union, Sequence
import cohere
from company_specific_docs.constants import COHERE_API_KEY

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
import importlib.metadata



# def _date_to_unix_timestamp(self, date_str: str) -> int:
#         """Convert a date string in YYYY-MM-DD format to a UNIX timestamp."""
#         try:
#             dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
#             return int(dt.timestamp())
#         except ValueError as e:
#             raise ValueError(f"Invalid date format. Please use YYYY-MM-DD format: {e}")
def _date_to_unix_timestamp(date_str: str) -> int:
    """Convert a date string in YYYY-MM-DD format to a UNIX timestamp."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError as e:
        raise ValueError(f"Invalid date format. Please use YYYY-MM-DD format: {e}")

server_tools = tool_definitions

def register_tools():
    """Register all tools with the MCP server."""
    @mcp.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List all available tools."""
        logger.info("Listing available tools")
        return server_tools

    @mcp.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None 
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        """Call a specific tool by name with the given arguments."""
        logger.info(f"Calling tool: {name} with arguments: {arguments}")
        try:
            if name == "list_company_manuals":
                return await list_company_manuals(arguments) 
            elif name == "smart_company_manual_search":
                return await smart_company_manual_search(arguments)
            elif name == "fetch_company_documents_by_vector_search":
                return await fetch_company_documents_by_vector_search(arguments)
            elif name == "get_company_manual_structure":
                return await get_company_manual_structure(arguments)
            elif name == "get_by_company_document_name_or_num":
                return await get_by_company_document_name_or_num(arguments)
            elif name == "get_company_manual_chapter_overview":
                return await get_company_manual_chapter_overview(arguments)
            elif name == "read_company_manual_section":
                return await read_company_manual_section(arguments)
            elif name == "read_company_manual_by_page_range":
                return await read_company_manual_by_page_range(arguments)
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            elif name == "google_search": 
                return await google_search(arguments)
            elif name == "get_mcp_build_version":
                return await get_mcp_build_version()
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise ValueError(f"Error calling tool {name}: {str(e)}")
        

# Helper functions


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
        "query": "Search results from Company Manuals",
        "searchEngine": "general"
      },
      "visual": {
        "icon": "search",
        "color": "#34A853"
      }
    },
    "content": "Search results for: Search results from Company Manuals",
    "artifacts": [
      {
        "id": "artifact_search_1744192295406_875",
        "type": "search_results",
        "content": {
          "query": "Search results from Company Manuals",
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

# ------------------- Company Manual Tool Handlers -------------------

async def list_company_manuals(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Retrieve a comprehensive list of all available company manuals.
    Args:
        arguments: No arguments required
    Returns:
        List containing the company manuals as TextContent
    """
    client = TypesenseClient()

    # Maximum number of results to return in searches
    MAX_DOCUMENTS = 50

    # Get first MAX_CIRCULARS items
    typesense_query = {
        "q": "*",
        "query_by": "documentName",
        "group_by": "documentName",
        "filter_by": "embType:!=Managers_Instructions && embType:!=CF && embType:!=RA",
        "per_page": MAX_DOCUMENTS
    }
    results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)
    
    # Extract unique document names from results
    documents = []
    if "grouped_hits" in results:
        documents = [group["group_key"][0] for group in results["grouped_hits"]]

    # Comment out original pagination code
    """
    per_page = 100
    page = 1
    all_documents = set()
    total_found = None
    client = TypesenseClient()

    while True:
        typesense_query = {
            "q": "*",
            "query_by": "documentName",
            "group_by": "documentName",
            "filter_by": "embType:!=Managers_Instructions && embType:!=CF && embType:!=RA",
            "per_page": per_page,
            "page": page
        }
        results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)
        if total_found is None:
            total_found = results.get("found", 0)
        if "grouped_hits" in results:
            for group in results["grouped_hits"]:
                all_documents.add(group["group_key"][0])
        # Stop if we've fetched all results
        if page * per_page >= total_found or not results.get("grouped_hits"):
            break
        page += 1

    documents = list(all_documents)
    """

    return [types.TextContent(
        type="text",
        text=json.dumps(documents, indent=2),
        title="List of Company Manuals",
        format="json"
    )]

# async def smart_company_manual_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
#     """Universal search tool for company manuals with intelligent query processing."""
#     try:
#         collection = "company_manual_documentsearch"
#         client = TypesenseClient()

#         # Extract arguments with defaults
#         query = arguments.get("query", "")
#         search_type = arguments.get("search_type", "hybrid" if query else "browse")
#         filters = arguments.get("filters", {})
#         max_results = arguments.get("max_results", 20)

#         # def sanitize_filter_value(value: str) -> str:
#         #     # Define a regex pattern of removable/special characters
#         #     # pattern = r"[()\[\]{}&|\":',=]"
#         #     pattern = r"[()\[\]{}&|:,=]"
#         #     cleaned = re.sub(pattern, " ", value).strip()
#         #     return json.dumps(cleaned)  # safely quoted for Typesense
#         def clean_indexed_field(value):
#             if not isinstance(value, str):
#                 return ''
#             value = value.lower()
#             # Replace any non-alphanumeric character with a space
#             value = re.sub(r'[^a-z0-9]', ' ', value)
#             # Collapse multiple spaces to one
#             value = re.sub(r'\s+', ' ', value).strip()
#             return value

#         # Build filter string from filters dict
#         filter_parts = []
        
#         # Handle document_type filter
#         document_type = filters.get("document_type")
#         if document_type:
#             if document_type == "company manual":
#                 # List of all company manual embTypes
#                 company_manual_embtypes = [
#                     'GAS_text', 'LNG_text', 'CONTINGENCY_MANUAL_VESSEL_AND_OFFICE_text',
#                     'Synergy_Global_Business_Travel_Policy_text', 'ISMS_CRM_text', 'FMP_text',
#                     'navigation_manual_text', 'MSMP_text', 'GTM_text', 'CHEMICAL_TANKER_manual_text',
#                     'CARGO_BULK_CARRIER_manual_text', 'HSM_manual_text', 'OPM_text',
#                     'CARGO_OPERATIONS_(TANKER)_manual_text', 'technical_manual_text', 'smm_text',
#                     'EEMS_text', 'CONTAINER_CARGO_OPERATION_manual_text', 'LMP_text',
#                     'Synergy_India_Business_Travel_Policy__text', 'CONTINGENCY_MANUAL_OFFICE_text']
#                 # Create filter for company manuals
#                 filter_parts.append(f"embType:[{', '.join([f'\"{v}\"' for v in company_manual_embtypes])}]")
#             elif document_type == "risk assessment":
#                 filter_parts.append("embType:=RA")
#             elif document_type == "forms and checklists":
#                 filter_parts.append("embType:=CF")
#             elif document_type == "manager instruction":
#                 filter_parts.append("embType:=Managers_Instructions")
        
#         # Handle other filters
#         for field, value in filters.items():
#             if value and field != "document_type":
#                 if field == "page_range" and isinstance(value, list) and len(value) == 2:
#                     filter_parts.append(f"pageNumber:>={value[0]} && pageNumber:<={value[1]}")
#                 elif field == "year":
#                     filter_parts.append(f"Year:={clean_indexed_field(value)}")
#                 elif field == "document_name":
#                     # For document name, we'll use it in the query instead of filter
#                     continue
#                 else:
#                     filter_parts.append(f"{field}: {clean_indexed_field(value)}")
        
#         filter_string = " && ".join(filter_parts) if filter_parts else None

#         # Enhance query based on document_name filter if present
#         enhanced_query = query
#         if filters.get("document_name") and query:
#             enhanced_query = f"{query} {filters['document_name']}"
#         elif filters.get("document_name") and not query:
#             enhanced_query = filters["document_name"]

#         # Build the search query
#         if search_type == "browse":
#             search_query = {
#                 "q": "*",
#                 "query_by": "documentName,chapter,section",
#                 "per_page": max_results,
#                 "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
#             }
#         elif search_type == "semantic":
#             search_query = { 
#                 "q": enhanced_query,
#                 "query_by": "embedding",
#                 "prefix": False,
#                 "per_page": max_results,
#                 "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
#             }
#         elif search_type == "keyword":
#             search_query = {
#                 "q": enhanced_query,
#                 "query_by": "documentName,chapter,section",
#                 "per_page": max_results,
#                 "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
#             }
#         else:  # hybrid
#             search_query = {
#                 "q": enhanced_query,
#                 "query_by": "embedding,documentName,chapter,section",
#                 "prefix": False,
#                 "per_page": max_results,
#                 "include_fields": "documentHeader,chapter,documentName,section,revNo,originalText,documentLink"}

#         # Add filters if any
#         if filter_string:
#             search_query["filter_by"] = filter_string

#         # Add sorting
#         if search_type == "browse" and not query:
#             search_query["sort_by"] = "Year:desc,documentName:asc"
#         else:
#             search_query["sort_by"] = "Year:desc"

#         # Execute search
#         results = client.collections[collection].documents.search(search_query)
#         hits = results.get("hits", [])
#         total_found = results.get("found", 0)

#         # Process results
#         processed_results = []
#         for hit in hits:
#             document = hit.get("document", {})
#             document.pop('embedding', None)  # Remove embedding field
#             processed_results.append({
#                 "document": document,
#                 "text_match_score": hit.get("text_match_score", 0)
#             })
        
#         # Format results
#         formatted_results = {
#             "search_metadata": {
#                 "query": query,
#                 "search_type": search_type, 
#                 "filters_applied": filters,
#                 "total_found": total_found,
#                 "returned": len(processed_results)
#             },
#             "results": processed_results
#         }
        
#         title = f"Smart Search Results: {query[:50]}..." if query else "Browse Results"
        
#         content = types.TextContent(
#             type="text",
#             text=json.dumps(formatted_results, indent=2),
#             title=title,
#             format="json"
#         )
    
#         link_data = []
#         for document in results["hits"]:
#             link_data.append({
#                 "title": document['document'].get("documentName"),
#                 "url": document['document'].get("documentLink")
#             })
#         artifact_data = get_list_of_artifacts("smart_company_manual_search",link_data)

#         # artifact = types.TextContent(
#         #     type="text",
#         #     text=json.dumps(artifact_data, indent=2),
#         #     title="IMO Publication Search Results",
#         #     format="json"
#         # )

#         return [content]+ artifact_data
    
#     except Exception as e:
#         return [types.TextContent(
#             type="text",
#             text=f"Error retrieving search results: {str(e)}",
#             title="Error",
#             format="json"
#         )]



async def smart_company_manual_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """Universal search tool for company manuals with intelligent query processing."""
    try:
        collection = "company_manual_documentsearch"
        client = TypesenseClient()

        # Extract arguments with defaults
        query = arguments.get("query", "")
        search_type = arguments.get("search_type", "hybrid" if query else "browse")
        filters = arguments.get("filters", {})
        max_results = arguments.get("max_results", 7)

        # def sanitize_filter_value(value: str) -> str:
        #     # Define a regex pattern of removable/special characters
        #     # pattern = r"[()\[\]{}&|\":',=]"
        #     pattern = r"[()\[\]{}&|:,=]"
        #     cleaned = re.sub(pattern, " ", value).strip()
        #     return json.dumps(cleaned)  # safely quoted for Typesense
        def clean_indexed_field(value):
            if not isinstance(value, str):
                return ''
            value = value.lower()
            # Replace any non-alphanumeric character with a space
            value = re.sub(r'[^a-z0-9]', ' ', value)
            # Collapse multiple spaces to one
            value = re.sub(r'\s+', ' ', value).strip()
            return value

        # Build filter string from filters dict
        filter_parts = []
        
        # Handle document_type filter
        document_type = filters.get("document_type")
        if document_type:
            if document_type == "company manual":
                # List of all company manual embTypes
                company_manual_embtypes = [
                    'GAS_text', 'LNG_text', 'CONTINGENCY_MANUAL_VESSEL_AND_OFFICE_text',
                    'Synergy_Global_Business_Travel_Policy_text', 'ISMS_CRM_text', 'FMP_text',
                    'navigation_manual_text', 'MSMP_text', 'GTM_text', 'CHEMICAL_TANKER_manual_text',
                    'CARGO_BULK_CARRIER_manual_text', 'HSM_manual_text', 'OPM_text',
                    'CARGO_OPERATIONS_(TANKER)_manual_text', 'technical_manual_text', 'smm_text',
                    'EEMS_text', 'CONTAINER_CARGO_OPERATION_manual_text', 'LMP_text',
                    'Synergy_India_Business_Travel_Policy__text', 'CONTINGENCY_MANUAL_OFFICE_text']
                # Create filter for company manuals
                filter_parts.append(f"embType:[{', '.join([f'\"{v}\"' for v in company_manual_embtypes])}]")
            elif document_type == "risk assessment":
                filter_parts.append("embType:=RA")
            elif document_type == "forms and checklists":
                filter_parts.append("embType:=CF")
            elif document_type == "manager instruction":
                filter_parts.append("embType:=Managers_Instructions")
        
        # Handle other filters
        for field, value in filters.items():
            if value and field != "document_type":
                if field == "page_range" and isinstance(value, list) and len(value) == 2:
                    filter_parts.append(f"pageNumber:>={value[0]} && pageNumber:<={value[1]}")
                elif field == "year":
                    filter_parts.append(f"Year:={clean_indexed_field(value)}")
                elif field == "document_name":
                    # For document name, we'll use it in the query instead of filter
                    continue
                else:
                    filter_parts.append(f"{field}: {clean_indexed_field(value)}")
        
        filter_string = " && ".join(filter_parts) if filter_parts else None

        # Enhance query based on document_name filter if present
        enhanced_query = query
        if filters.get("document_name") and query:
            enhanced_query = f"{query} {filters['document_name']}"
        elif filters.get("document_name") and not query:
            enhanced_query = filters["document_name"]

        #Semantic search query
        search_query = { 
            "q": enhanced_query,
            "query_by": "embedding",
            "prefix": False,
            "per_page": max_results,
            "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
        }

        # Add filters if any
        if filter_string:
            search_query["filter_by"] = filter_string

        search_query["sort_by"] = "Year:desc"

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
                artifact_data = get_list_of_artifacts("smart_company_manual_search",link_data)
                content = types.TextContent(
                    type="text",
                    text=json.dumps(top_results, indent=2),
                    title="Reranked Company Manual Search Results",
                    format="json"
                )
                return [content]+ artifact_data
            except Exception as e:
                logger.error(f"Error in Cohere reranking: {e}")

                
        # Process results
        processed_results = []
        for hit in hits:
            document = hit.get("document", {})
            document.pop('embedding', None)  # Remove embedding field
            processed_results.append({
                "document": document,
                "text_match_score": hit.get("text_match_score", 0)
            })
        
        # Format results
        formatted_results = {
            "search_metadata": {
                "query": query,
                "search_type": search_type, 
                "filters_applied": filters,
                "total_found": total_found,
                "returned": len(processed_results)
            },
            "results": processed_results
        }
        
        title = f"Smart Search Results: {query[:50]}..." if query else "Browse Results"
        
        content = types.TextContent(
            type="text",
            text=json.dumps(formatted_results, indent=2),
            title=title,
            format="json"
        )
    
        link_data = []
        for document in results["hits"]:
            link_data.append({
                "title": document['document'].get("documentName"),
                "url": document['document'].get("documentLink")
            })
        artifact_data = get_list_of_artifacts("smart_company_manual_search",link_data)

        return [content]+ artifact_data
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving search results: {str(e)}",
            title="Error",
            format="json" 
        )]
    

async def fetch_company_documents_by_vector_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Performs a targeted search across company policy manuals, risk assessments, and management directives.
    Uses the 'query' argument for Typesense search and applies Cohere reranking if <= 50 results.
    """
    query = arguments.get("query", "*")
    client = TypesenseClient()
    # Maximum number of results to return in searches
    MAX_DOCUMENTS = 50

    # Get first MAX_CIRCULARS items
    typesense_query = {
        "q": query,
        "query_by": "embedding",
        "sort_by": "Year:desc",
        "include_fields": "documentName,chapter,revDate,revNo,section,summary,documentLink,originalText",
        "prefix": False,
        "per_page": MAX_DOCUMENTS
    }
    results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)
    hits = results.get("hits", [])
    total_found = results.get("found", 0)
    all_hits = hits

    # Comment out original pagination code
    """
    per_page = 20
    page = 1
    all_hits = []
    total_found = None
    client = TypesenseClient()

    while True:
        typesense_query = {
            "q": query,
            "query_by": "embedding",
            "sort_by": "Year:desc",
            "include_fields": "documentName,chapter,revDate,revNo,section,summary,documentLink,originalText",
            "prefix": False,
            "per_page": per_page,
            "page": page
        }
        results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)
        hits = results.get("hits", [])
        if total_found is None:
            total_found = results.get("found", 0)
        all_hits.extend(hits)
        if page * per_page >= total_found or not hits:
            break
        page += 1
    """

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
            if docs:
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
                artifact_data = get_list_of_artifacts("fetch_company_documents_by_vector_search", link_data)

                # artifact = types.TextContent(
                #     type="text",
                #     text=json.dumps(artifact_data, indent=2, default=str),
                #     title="Reranked Company Manual Search Results",
                #     format="json"
                # )
                content = types.TextContent(
                    type="text",
                    text=json.dumps(top_results, indent=2),
                    title="Reranked Company Manual Search Results",
                    format="json"
                )
                return [content]+ artifact_data
        except Exception as e:
            logger.error(f"Error in Cohere reranking: {e}")
            # Fall back to original results if reranking fails

    # Return all results if no reranking was done
    filtered_hits = []
    for hit in all_hits:
        document = hit.get('document', {})
        document.pop('embedding', None)
        filtered_hits.append(document)

    documents = filtered_hits
    link_data = []
    for document in documents:
        link_data.append({
            "title": document.get("documentName"),
            "url": document.get("documentLink")
        })
    artifact_data = get_list_of_artifacts("fetch_company_documents_by_vector_search",link_data)

    content = types.TextContent(   
        type="text",
        text=json.dumps(filtered_hits, indent=2),
        title="Company Manual Search Results",
        format="json"
    )
    # artifact = types.TextContent(
    #     type="text",
    #     text=json.dumps(artifact_data, indent=2),
    #     title="Company Manual Search Results",
    #     format="json"
    # )
    return [content]+artifact


async def get_company_manual_structure(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Search by document name or number. Returns up to 10 matched documents directly without Cohere reranking.
    """
    document_name = arguments.get("document_name", "*")
    per_page = 10  # Only fetch up to 10 results in a single query
    client = TypesenseClient()

    typesense_query = {
        "q": document_name,
        "query_by": "documentName",
        # "sort_by": "Year:desc",
        "include_fields": "documentName,chapter,shortSummary,chapterSectionInfo, documentLink",
        "per_page": per_page,
        "page": 1
    }
    results = client.collections["full_company_manual_documentsearches"].documents.search(typesense_query)
    hits = results.get("hits", [])

    # Return up to 10 results directly, no Cohere reranking
    filtered_hits = []
    for hit in hits:
        document = hit.get('document', {})
        document.pop('embedding', None)
        filtered_hits.append(document)
    return [types.TextContent(
        type="text",
        text=json.dumps(filtered_hits, indent=2),
        title="Document Name/Number Search Results (Top 10)",
        format="json"
    )]


async def get_by_company_document_name_or_num(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Search by document name or number. Applies Cohere reranking if <= 50 results.
    """
    document_name = arguments.get("document_name", "*")
    document_type = arguments.get("document_type", "*")
    client = TypesenseClient()

    docname_map = {}

    MAX_DOCUMENTS = 50
    company_manual_filter_values = ['GAS_text',
                                    'LNG_text',
                                    'CONTINGENCY_MANUAL_VESSEL_AND_OFFICE_text',
                                    'Synergy_Global_Business_Travel_Policy_text',
                                    'ISMS_CRM_text',
                                    'FMP_text',
                                    'navigation_manual_text',
                                    'MSMP_text',
                                    'GTM_text',
                                    'CHEMICAL_TANKER_manual_text',
                                    'CARGO_BULK_CARRIER_manual_text',
                                    'HSM_manual_text',
                                    'OPM_text',
                                    'CARGO_OPERATIONS_(TANKER)_manual_text',
                                    'technical_manual_text',
                                    'smm_text',
                                    'EEMS_text',
                                    'CONTAINER_CARGO_OPERATION_manual_text',
                                    'LMP_text',
                                    'Synergy_India_Business_Travel_Policy__text',
                                    'CONTINGENCY_MANUAL_OFFICE_text',
                                    'importantQuestion']
    
    risk_assesment_filter_values = ["RA"]
    forms_and_checklists_filter_values = ["CF"]
    manager_instruction_filter_values = ["Managers_Instructions"]
    
    if document_type == "company manual":
        # filter_str = f"embType:[{', '.join([f'\"{v}\"' for v in company_manual_filter_values])}]"
        return await get_company_manual_structure(arguments)
    elif document_type == "risk assessment":
        filter_str = f"embType:[{', '.join([f'\"{v}\"' for v in risk_assesment_filter_values])}]"
    elif document_type == "forms and checklists":
        filter_str = f"embType:[{', '.join([f'\"{v}\"' for v in forms_and_checklists_filter_values])}]"
    elif document_type == "manager instruction":
        filter_str = f"embType:[{', '.join([f'\"{v}\"' for v in manager_instruction_filter_values])}]"

    # Get first MAX_CIRCULARS items
    typesense_query = {
        "q": document_name,
        "query_by": "documentName",
        "filter_by": filter_str,
        "sort_by": "Year:desc",
        "include_fields": "documentName,revDate,revNo,summary,documentLink,originalText",
        "per_page": MAX_DOCUMENTS
    }
    results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)
    hits = results.get("hits", []) 
    total_found = results.get("found", 0)
    all_hits = hits

    # Comment out original pagination code
    """
    per_page = 20
    page = 1
    all_hits = []
    total_found = None
    client = TypesenseClient()

    while True:
        typesense_query = {
            "q": document_name,
            "query_by": "documentName",
            "sort_by": "Year:desc",
            "include_fields": "documentName,chapter,revDate,revNo,section,summary,documentLink,originalText",
            "per_page": per_page,
            "page": page
        }
        results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)
        hits = results.get("hits", [])
        if total_found is None:
            total_found = results.get("found", 0)
        all_hits.extend(hits)
        if page * per_page >= total_found or not hits:
            break
        page += 1
    """

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
                query=document_name,
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
            artifact_data = get_list_of_artifacts("get_by_company_document_name_or_num",link_data)
            # artifact = types.TextContent(
            #     type="text",
            #     text=json.dumps(artifact_data, indent=2, default=str),
            #     title="Reranked Company Manual Search Results",
            #     format="json"
            # )
            content = types.TextContent(
                type="text",
                text=json.dumps(top_results, indent=2),
                title="Reranked Company Manual Search Results",
                format="json"
            )
            return [content]+ artifact_data
        except Exception as e:
            logger.error(f"Error in Cohere reranking: {e}")
            # Fall back to original results if reranking fails

    # Return all results if no reranking was done
    filtered_hits = []
    for hit in all_hits:
        document = hit.get('document', {})
        document.pop('embedding', None)
        filtered_hits.append(document)

    documents = filtered_hits
    link_data = []
    for document in documents:
        if document.get("documentLink"):
            link_data.append({
                "title": document.get("documentName"),
                "url": document.get("documentLink")
            })
    artifact_data = get_list_of_artifacts("get_by_company_document_name_or_num",link_data)
    # artifact = types.TextContent(
    #     type="text",
    #     text=json.dumps(artifact_data, indent=2),
    #     title="Company Manual Search Results",
    #     format="json"
    # )
    content = types.TextContent(
        type="text",
        text=json.dumps(filtered_hits, indent=2),
        title="Company Manual Search Results",
        format="json"
    )
    return [content]+ artifact_data

async def get_company_manual_chapter_overview(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Given a chapter and its corresponding document name, this tool returns the chapter content overview.
    """
    chapter = arguments.get("chapter", "*")
    document_name = arguments.get("document_name", "*")
    if chapter is None:
        raise ValueError("Chapter must be provided.")
    if document_name is None:
        raise ValueError("document_name must be provided.")
    per_page = 10  # Only fetch up to 10 results in a single query
    client = TypesenseClient()

    # def sanitize_filter_value(value: str) -> str:
    #     # Define a regex pattern of removable/special characters
    #     # pattern = r"[()\[\]{}&|\":',=]"
    #     pattern = r"[()\[\]{}&|:,=]"
    #     cleaned = re.sub(pattern, " ", value).strip()
    #     return json.dumps(cleaned)  # safely quoted for Typesense
    def clean_indexed_field(value):
        if not isinstance(value, str):
            return ''
        value = value.lower()
        # Replace any non-alphanumeric character with a space
        value = re.sub(r'[^a-z0-9]', ' ', value)
        # Collapse multiple spaces to one
        value = re.sub(r'\s+', ' ', value).strip()
        return value

    typesense_query = {
        "q": "*",
        "query_by": "chapter,documentName",
        "filter_by": f'chapter_indexed: {clean_indexed_field(chapter)} && doc_name_indexed: {clean_indexed_field(document_name)}',
        "include_fields": "chapter,documentHeader,documentName,documentSummary,originalText,pageNumber,section,shortSummary",
        "per_page": per_page,
        "page": 1
    }

    results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)

    # document_query = {
    #     "q": document_name,
    #     # "q": "*",
    #     "query_by": "documentName",
    #     # "filter_by": f'chapter: {chapter} && documentName: {document_name}',
    #     "include_fields": "chapter,documentHeader,documentName,documentSummary,originalText,pageNumber,section,shortSummary",
    #     "per_page": per_page,
    #     "page": 1
    # }
    # document_result = client.collections["company_manual_documentsearch"].documents.search(document_query)

    # results = []
    # for document in document_result['hits']:
    #     document_name = document['document']['documentName']
        
    #     chapter_query = {
    #         "q": chapter,
    #         "query_by": "chapter",
    #         "filter_by": f'documentName:={document_name}',
    #         "include_fields": "chapter,documentHeader,documentName,documentSummary,originalText,pageNumber,section,shortSummary",
    #         "per_page": per_page,
    #         "page": 1
    #     }
    #     results = client.collections["company_manual_documentsearch"].documents.search(chapter_query)
        
    #     if results['hits']:
    #         results=results+results['hits']

    # results = document_result.documents.search(chapter_query)

    hits = results.get("hits", [])

    # Return up to 10 results directly, no Cohere reranking
    filtered_hits = []
    for hit in hits:
        document = hit.get('document', {})
        document.pop('embedding', None)
        filtered_hits.append(document)
    content = types.TextContent(
        type="text",
        text=json.dumps(filtered_hits, indent=2),
        title="Document Name/Number Search Results (Top 10)",
        format="json"
    )

    link_data = []
    for document in results["hits"]:
        link_data.append({
            "title": document['document'].get("documentName"),
            "url": document['document'].get("documentLink")
        })
    artifact_data = get_list_of_artifacts("get_company_manual_chapter_overview",link_data)

    artifact = types.TextContent(
        type="text",
        text=json.dumps(artifact_data, indent=2),
        title="IMO Publication Search Results",
        format="json"
    )

    return [content]+ artifact_data

async def read_company_manual_section(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Given a section and its corresponding chapter and document name, this tool returns the section overview.
    """
    section = arguments.get("section", "*")
    chapter = arguments.get("chapter", "*")
    documentName = arguments.get("document_name", "*")
    if section is None:
        raise ValueError("Section must be provided.")
    if chapter is None:
        raise ValueError("Chapter must be provided.")
    if documentName is None:
        raise ValueError("documentName must be provided.")
    per_page = 10  # Only fetch up to 10 results in a single query
    client = TypesenseClient()

    # def sanitize_filter_value(value: str) -> str:
    #     # Define a regex pattern of removable/special characters
    #     # pattern = r"[()\[\]{}&|\":',=]"
    #     pattern = r"[()\[\]{}&|\:',=]"
    #     cleaned = re.sub(pattern, " ", value).strip()
    #     return json.dumps(cleaned)  # safely quoted for Typesense
    def clean_indexed_field(value):
        if not isinstance(value, str):
            return ''
        value = value.lower()
        # Replace any non-alphanumeric character with a space
        value = re.sub(r'[^a-z0-9]', ' ', value)
        # Collapse multiple spaces to one
        value = re.sub(r'\s+', ' ', value).strip()
        return value

    typesense_query = {
        "q": "*",
        "query_by": "section,chapter,documentName",
        "filter_by": f"section_indexed: {clean_indexed_field(section)} && chapter_indexed: {clean_indexed_field(chapter)} && doc_name_indexed: {clean_indexed_field(documentName)}",
        "include_fields": "chapter,documentHeader,documentName,documentSummary,originalText,pageNumber,section,shortSummary",
        "per_page": per_page,
        "page": 1
    }
    results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)
    hits = results.get("hits", [])

    # Return up to 10 results directly, no Cohere reranking
    filtered_hits = []
    for hit in hits:
        document = hit.get('document', {})
        document.pop('embedding', None)
        filtered_hits.append(document)
    content = types.TextContent(
        type="text",
        text=json.dumps(filtered_hits, indent=2),
        title="Document Name/Number Search Results (Top 10)",
        format="json"
    )

    link_data = []
    for document in results["hits"]:
        link_data.append({
            "title": document['document'].get("documentName"),
            "url": document['document'].get("documentLink")
        })
    artifact_data = get_list_of_artifacts("read_company_manual_section",link_data)

    # artifact = types.TextContent(
    #     type="text",
    #     text=json.dumps(artifact_data, indent=2),
    #     title="IMO Publication Search Results",
    #     format="json"
    # )

    return [content]+ artifact_data

async def read_company_manual_by_page_range(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Extracts content from a document given a start and end page number.
    Args:
        arguments: Should contain 'document_name', 'start_page', and 'end_page'.
    Returns:
        List containing the extracted content as TextContent.
    """
    document_name = arguments.get("document_name", "*")
    start_page = arguments.get("start_page")
    end_page = arguments.get("end_page")
    if start_page is None or end_page is None:
        raise ValueError("Both start_page and end_page must be provided.")
    client = TypesenseClient()

    # def sanitize_filter_value(value: str) -> str:
    #     # Define a regex pattern of removable/special characters
    #     # pattern = r"[()\[\]{}&|\":',=]"
    #     pattern = r"[()\[\]{}&|:,=]"
    #     cleaned = re.sub(pattern, "", value).strip()
    #     return json.dumps(cleaned)  # safely quoted for Typesense
    def clean_indexed_field(value):
        if not isinstance(value, str):
            return ''
        value = value.lower()
        # Replace any non-alphanumeric character with a space
        value = re.sub(r'[^a-z0-9]', ' ', value)
        # Collapse multiple spaces to one
        value = re.sub(r'\s+', ' ', value).strip()
        return value

    max_pages = 10
    results = []
    batching = False
    current_start = start_page
    while current_start <= end_page:
        current_end = min(current_start + max_pages - 1, end_page)
        typesense_query = {
            "q": "*",
            "filter_by": f"doc_name_indexed: {clean_indexed_field(document_name)} && pageNumber:>={current_start} && pageNumber:<={current_end}",
            "per_page": 100,  # Adjust as needed
            "page": 1
        }
        query_results = client.collections["company_manual_documentsearch"].documents.search(typesense_query)
        hits = query_results.get("hits", [])
        filtered_hits = []
        for hit in hits:
            document = hit.get('document', {})
            document.pop('embedding', None)
            filtered_hits.append(document)
        results.extend(filtered_hits)
        if current_end - current_start + 1 >= max_pages:
            batching = True
        current_start = current_end + 1

        link_data = []
        for document in results:
            link_data.append({
                "title": document.get("documentName"),
                "url": document.get("documentLink")
            })
        artifact_data = get_list_of_artifacts("read_company_manual_by_page_range",link_data)

        # artifact = types.TextContent(
        #     type="text",
        #     text=json.dumps(artifact_data, indent=2),
        #     title="IMO Publication Search Results",
        #     format="json"
        # )

    message = None
    if batching:
        message = types.TextContent(
            type="text",
            text=f"Note: Requested page range exceeded {max_pages} pages. Results are aggregated from multiple batches.",
            title="Batching Notice",
            format="plain"
        )
    content = types.TextContent(
        type="text",
        text=json.dumps(results, indent=2),
        title=f"Extracted Content from Pages {start_page}-{end_page}",
        format="json"
    )
    if message:
        return [message, content]+ artifact_data
    else:
        return [content]+ artifact_data


# async def fetch_manager_instruction_specific_details_by_vector_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
#     filters = ["embType:Managers_Instructions"]
#     query_parts = []
#     if "document_name" in arguments and arguments["document_name"]:
#         query_parts.append(arguments["document_name"])
#     typesense_query = {
#         "q": " ".join(query_parts) if query_parts else "*",
#         "query_by": "embedding,documentName",
#         "filter_by": " && ".join(filters),
#         "sort_by": "Year:desc",
#         "include_fields": "documentName,chapter,revDate,revNo,section,summary,documentLink,originalText"
#     }
#     try:
#         client = TypesenseClient()
#         result = await typesense_with_optional_cohere_rerank(
#             client=client,
#             collection="company_manual_documentsearch",
#             typesense_query=typesense_query,
#             cohere_query=arguments.get("document_name", ""),
#             cohere_key=COHERE_API_KEY
#         )
#         return [types.TextContent(
#             type="text",
#             text=json.dumps(result, indent=2),
#             title="Manager's Instructions Search Results (with optional Cohere rerank)",
#             format="json"
#         )]
#     except Exception as e:
#         logger.error("Error in manager instruction search", e)
#         raise

# async def fetch_forms_and_checklists_specific_details_by_vector_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
#     filters = ["embType:CF"]
#     query_parts = []
#     if "document_name" in arguments and arguments["document_name"]:
#         query_parts.append(arguments["document_name"])
#     typesense_query = {
#         "q": " ".join(query_parts) if query_parts else "*",
#         "query_by": "embedding,documentName",
#         "filter_by": " && ".join(filters),
#         "sort_by": "Year:desc",
#         "include_fields": "documentName,chapter,revDate,revNo,section,summary,documentLink,originalText",
#         "prefix": False
#     }
#     try:
#         client = TypesenseClient()
#         result = await typesense_with_optional_cohere_rerank(
#             client=client,
#             collection="company_manual_documentsearch",
#             typesense_query=typesense_query,
#             cohere_query=arguments.get("document_name", ""),
#             cohere_key=COHERE_API_KEY
#         )
#         return [types.TextContent(
#             type="text",
#             text=json.dumps(result, indent=2),
#             title="Forms and Checklists Search Results (with optional Cohere rerank)",
#             format="json"
#         )]
#     except Exception as e:
#         logger.error("Error in forms and checklists search", e)
#         raise

# def format_results(results: Dict[str, Any], title: str) -> types.TextContent:
#     """Helper method to format search results consistently."""
#     return types.TextContent(
#         type="text",
#         text=json.dumps(results, indent=2),
#         title=title,
#         format="json"
#     )


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


async def get_mcp_build_version() -> List[types.TextContent]:
    build_info = {}
    errors = []
    package_name = None

    # Attempt to get local version from pyproject.toml
    try:
        with open("./pyproject.toml", "r", encoding="utf-8") as file:
            content = file.read()

        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)

        if version_match:
            build_info["local_build_version"] = version_match.group(1)
        else:
            errors.append("Local build version not found in pyproject.toml.")

        if name_match:
            package_name = name_match.group(1)
        else:
            errors.append("Package name not found in pyproject.toml.")
            package_name = "syia-internal-tools-mcp-2024-x7k9"

    except Exception as e:
        # Hardcode your package name here for fallback
        package_name = "syia-internal-tools-mcp-2024-x7k9"

    # If local version not found, try to get installed version
    if not build_info.get("local_build_version") and package_name:
        try:
            installed_version = importlib.metadata.version(package_name)
            build_info["installed_package_version"] = installed_version
        except Exception as e:
            errors.append(f"Failed to get installed package version: {e}")
    elif not build_info.get("local_build_version"):
        # Try to get any installed package version if package_name is not available
        try:
            # If you want to hardcode the package name, set it here
            # package_name = "your-package-name"
            pass
        except Exception as e:
            errors.append(f"Failed to get installed package version: {e}")

    # Attempt to get production version from TestPyPI
    if package_name:
        try:
            url = f"https://test.pypi.org/pypi/{package_name}/json"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                production_version = data.get("info", {}).get("version")
                if production_version:
                    build_info["production_build_version"] = production_version
                else:
                    errors.append("Production version not found in PyPI response.")
            else:
                errors.append(f"Failed to fetch from PyPI. Status code: {response.status_code}")

        except Exception as e:
            errors.append(f"Failed to fetch production version: {e}")
    else:
        errors.append("Package name was not available, skipping PyPI lookup.")

    # Combine results
    result_text = json.dumps(build_info, indent=2)
    if errors:
        result_text += "\n\nErrors:\n" + "\n".join(f"- {err}" for err in errors)

    return [
        types.TextContent(
            type="text",
            title="Build Version",
            text=result_text,
            format="json"
        )
    ]
