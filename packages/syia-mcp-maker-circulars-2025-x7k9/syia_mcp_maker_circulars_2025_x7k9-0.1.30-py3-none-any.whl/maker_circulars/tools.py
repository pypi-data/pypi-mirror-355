# Standard Library
import os
import re
import time
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Third-Party Libraries
import requests
import httpx
import cohere
from pymongo import MongoClient, errors
from dateutil import parser
from typing import Any, Dict, List, Sequence, Union
from playwright.async_api import async_playwright

# Internal Modules
from maker_circulars import mcp, logger
from maker_circulars.constants import (
    COHERE_API_KEY,
    MONGODB_URI,
    MONGODB_DB_NAME,
    OPENAI_API_KEY,
    PERPLEXITY_API_KEY,
)
from maker_circulars.databases import *
from maker_circulars.tool_schema import tool_definitions
from maker_circulars.utils import timestamped_filename_pdf
from utils.llm import LLMClient
import mcp.types as types
from difflib import SequenceMatcher


# Maximum number of circulars to return in search results
MAX_CIRCULARS = 10

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
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError as e:
        raise ValueError(f"Invalid date format. Please use YYYY-MM-DD format: {e}")
    
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
        "query": "Search results from Maker Circulars",
        "searchEngine": "general"
      },
      "visual": {
        "icon": "search",
        "color": "#34A853"
      }
    },
    "content": "Search results for: Search results from Maker Circulars",
    "artifacts": [
      {
        "id": "artifact_search_1744192295406_875",
        "type": "search_results",
        "content": {
          "query": "Search results from Maker Circulars",
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



def get_artifact(function_name: str, url_list: list):
    """
    Handle get artifact tool using updated artifact format
    """

    artifacts = []
    for url in url_list:
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
            if name == "list_maker_specific_circulars":
                return await list_maker_specific_circulars(arguments)
            elif name == "smart_circular_search":
                return await smart_circular_search(arguments)
            elif name == "get_circular_by_doc_name_or_num":
                return await get_circular_by_doc_name_or_num(arguments)
            elif name == "get_circular_by_maker_and_date_range":
                return await get_circular_by_maker_and_date_range(arguments)
            elif name == "fetch_circular_details_by_vector_search":
                return await fetch_circular_details_by_vector_search(arguments)
            elif name == "list_all_circular_makers":
                return await list_all_circular_makers(arguments)
            # Maker Circulars - MAN BW Downloads
            elif name == "latest_circulars_manbw_downloads":
                 return await latest_circulars_manbw_downloads()   
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            # MongoDB Tools
            elif name == "get_maker_model_for_particular_imo":
                return await get_maker_model_for_particular_imo(arguments["imo"])  
            elif name == "google_search":
                return await google_search(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise ValueError(f"Error calling tool {name}: {str(e)}")

# ------------------- Circular Tool Handlers -------------------


def format_circular_hit(hit: Dict, doc: Dict) -> Dict:
    return {
        "relevance_score": round(hit.get("text_match", 0), 3) if hit.get("text_match") else None,
        "document": {
            "name": doc.get("documentName", "Unknown"),
            "link": doc.get("documentLink", ""),
            "timestamp": doc.get("unix_timestamp", "Unknown")
        },
        "equipment_info": {
            "maker": doc.get("maker", "Unknown"),
            "model": doc.get("model", "Unknown")
        },
        "content_excerpt": doc.get("textToEmbed", ""),
        "highlights": hit.get("highlights", None)
    }

def parse_date_to_unix(date_str: str) -> int:
    """
    Parses a date string into a Unix timestamp.
    Args:
        date_str (str): Human-friendly date string.

    Returns:
        int: UTC-based Unix timestamp.
    """
    try:
        dt = parser.parse(date_str, fuzzy=True, dayfirst=True)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)

        dt_utc = dt.astimezone(timezone.utc)
        return int(dt_utc.timestamp())
    except Exception as e:
        raise ValueError(f"Could not interpret date '{date_str}'. Please use a full or partial date like 'March 2024', '2025-01-01', or '15 May 2023'. Error: {e}")



async def smart_circular_search(arguments: Dict[str, Any]):
    try:
        query = arguments.get("query", "")
        search_type = arguments.get("search_type", "hybrid" if query else "browse")
        filters = arguments.get("filters", {})
        max_results = arguments.get("max_results", 7)

        collection = "full_circulars"
        client = TypesenseClient()

        if "from_date" in filters:
            try:
                filters["from_timestamp"] = parse_date_to_unix(filters.pop("from_date"))
            except ValueError as e:
                return [types.TextContent(
                    type="text",
                    text=str(e),
                    title="Invalid 'from_date'",
                    format="json"
                )]

        if "to_date" in filters:
            try:
                filters["to_timestamp"] = parse_date_to_unix(filters.pop("to_date"))
            except ValueError as e:
                return [types.TextContent(
                    type="text",
                    text=str(e),
                    title="Invalid 'to_date'",
                    format="json"
                )]
        
        def sanitize_filter_value(value: str) -> str:
            # Define a regex pattern of removable/special characters
            # pattern = r"[()\[\]{}&|\":',=]"
            pattern = r"[()\[\]{}&|:,=]"
            cleaned = re.sub(pattern, " ", value).strip()
            return json.dumps(cleaned)  # safely quoted for Typesense
 
        filter_parts = []
        if filters.get("maker"):
            filter_parts.append(f'maker_indexed:{sanitize_filter_value(filters["maker"]).lower()}')
        if filters.get("document_name"):
            filter_parts.append(f'doc_name_indexed:{sanitize_filter_value(filters["document_name"]).lower()}')
        if filters.get("from_timestamp"):
            filter_parts.append(f'unix_timestamp:>={sanitize_filter_value(filters["from_timestamp"])}')
        if filters.get("to_timestamp"):
            filter_parts.append(f'unix_timestamp:<={sanitize_filter_value(filters["to_timestamp"])}')

        filter_string = " && ".join(filter_parts) if filter_parts else None

        # if search_type == "browse":
        #     search_query = {
        #         "q": "*",
        #         "query_by": "textToEmbed",
        #         "sort_by": "unix_timestamp:desc",
        #         "per_page": max_results,
        #         "include_fields": "documentHeader,documentName,maker,model,originalText,documentLink"
        #     }
        # elif search_type == "semantic":
        search_query = {
            "q": query,
            "query_by": "embedding",
            "per_page": max_results,
            "prefix": False,
            "include_fields": "documentHeader,documentName,maker,model,originalText,documentLink"
        }
        # elif search_type == "keyword":
        #     search_query = {
        #         "q": query,
        #         "query_by": "textToEmbed,doc_name_indexed,maker_indexed",
        #         "per_page": max_results,
        #         "include_fields": "documentHeader,documentName,maker,model,originalText,documentLink"
        #     }
        # else:  # hybrid
        #     search_query = {
        #         "q": query,
        #         "query_by": "textToEmbed,embedding",
        #         "per_page": max_results,
        #         "prefix": False,
        #         "include_fields": "documentHeader,documentName,maker,model,originalText,documentLink"
        #     }

        # if filter_string:
        search_query["filter_by"] = filter_string

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
                artifact_data = get_list_of_artifacts("smart_circular_search",link_data)
                content = types.TextContent(
                    type="text",
                    text=json.dumps(top_results, indent=2),
                    title="Reranked Company Manual Search Results",
                    format="json"
                )
                return [content]+ artifact_data
            except Exception as e:
                logger.error(f"Error in Cohere reranking: {e}")

        formatted_results = {
            "search_metadata": {
                "query": query,
                "search_type": search_type,
                "filters_applied": filters,
                "total_found": results.get("found", 0),
                "returned": min(results.get("found", 0), max_results)
            },
            "results": [format_circular_hit(hit, hit["document"]) for hit in results.get("hits", [])]
        }

        title = f"Circular Search: {query[:50]}..." if query else "Recent Circulars"
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
        artifact_data = get_list_of_artifacts("smart_circular_search", link_data)

        # artifact = types.TextContent(
        #     type="text",
        #     text=json.dumps(artifact_data, indent=2),
        #     title="IMO Publication Search Results",
        #     format="json"
        # )

        return [content]+ artifact_data

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error during circular search: {str(e)}",
            title="Error",
            format="json"
        )]



async def list_maker_specific_circulars(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Retrieve a table of contents (ToC) listing all circulars related to a specific equipment maker.
    Fetches all pages dynamically and aggregates results.
    Args:
        arguments: Tool arguments including maker name
    Returns:
        List containing the circulars as TextContent
    """
    maker = arguments.get("maker")
    if not maker:
        raise ValueError("Maker name is required")

    per_page = 20
    page = 1
    all_hits = []
    total_found = None
    client = TypesenseClient()

    # # Limit to MAX_CIRCULARS items
    # typesense_query = {
    #     "q": maker,
    #     "query_by": "maker_indexed",
    #     "sort_by": "unix_timestamp:desc",
    #     "per_page": 250,
    #     "include_fields": "documentName,maker,issue_date,equipment,model,documentLink"
    # }
    # results = client.collections["full_circulars"].documents.search(typesense_query)
    # hits = results.get("hits", [])
    # total_found = results.get("found", 0)
    # all_hits = hits  # Just use the first MAX_CIRCULARS items


    while True:
        typesense_query = { 
            "q": maker,
            "query_by": "maker_indexed",
            "sort_by": "unix_timestamp:desc",
            "per_page": per_page,
            "page": page,
            "include_fields": "documentName,maker,issue_date,equipment,model,documentLink"
        }
        results = client.collections["full_circulars"].documents.search(typesense_query)
        hits = results.get("hits", [])
        if total_found is None:
            total_found = results.get("found", 0)
        all_hits.extend(hits)
        # Stop if we've fetched all results
        if page * per_page >= total_found or not hits:
            break
        page += 1

    link_data = []
    filtered_hits = [] #removed documentLink
    for hit in all_hits:
        doc = hit.get("document", {})
        if doc.get("documentLink"):
            link_data.append({
                "title": doc.get("documentName"),
                "url": doc.get("documentLink")
            })
        if "embedding" in doc:
            doc.pop('embedding', None)
        if "documentLink" in doc:
            doc.pop('documentLink', None)
        filtered_hits.append(doc)

    artifact_data = get_list_of_artifacts("list_maker_specific_circulars", link_data)
    # artifact = types.TextContent(
    #     type="text",
    #     text=json.dumps(artifact_data, indent=2, default=str),
    #     title=f"Circulars by {maker}",
    #     format="json"
    # )

    content = types.TextContent(
        type="text",
        text=json.dumps(filtered_hits, indent=2),
        title=f"Circulars by {maker}",
        format="json"
    )

    return [content]+ artifact_data

async def get_circular_by_doc_name_or_num(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Search and retrieve circulars using any part of the document name or number.
    
    Args:
        arguments: Tool arguments including document name or number
        
    Returns:
        List containing the circulars as TextContent
    """
    document_name_or_num = arguments.get("document_name_or_num")
    if not document_name_or_num:
        raise ValueError("Document name or number is required")

    per_page = 20
    page = 1
    all_hits = []
    total_found = None
    client = TypesenseClient()

    # Limit to MAX_CIRCULARS items
    typesense_query = {
        "q": document_name_or_num,
        "query_by": "documentName",
        "sort_by": "unix_timestamp:desc",
        "per_page": MAX_CIRCULARS,  # Get only MAX_CIRCULARS items at once
        "include_fields": "documentName,maker,equipment,model,summary,documentLink,originalText",
        "prefix": False
    }
    results = client.collections["full_circulars"].documents.search(typesense_query)
    hits = results.get("hits", [])
    total_found = results.get("found", 0)
    all_hits = hits  # Just use the first MAX_CIRCULARS items

    # Comment out the original pagination code
    """
    while True:
        typesense_query = {
            "q": document_name_or_num,
            "query_by": "documentName",
            "sort_by": "unix_timestamp:desc",
            "per_page": per_page,
            "page": page,
            "include_fields": "documentName,maker,equipment,model,summary,documentLink,originalText",
            "prefix": False
        }
        results = client.collections["full_circulars"].documents.search(typesense_query)
        hits = results.get("hits", [])
        if total_found is None:
            total_found = results.get("found", 0)
        all_hits.extend(hits)
        # Stop if we've fetched all results
        if page * per_page >= total_found or not hits:
            break
        page += 1
    """

    # If we have results and a document name, apply Cohere reranking only if results are not too many
    if all_hits and COHERE_API_KEY and len(all_hits) <= 50:
        try:
            # Collect documents with their original text for reranking
            docs_with_originals = []
            for hit in all_hits:
                document = hit.get("document", {})
                if "originalText" in document:
                    docs_with_originals.append({
                        "text": document["originalText"],
                        "original": document
                    })
            # Extract just the text for reranking
            docs = [doc["text"] for doc in docs_with_originals]
            # Initialize Cohere client
            co = cohere.ClientV2(COHERE_API_KEY)
            # Perform reranking
            reranked = co.rerank(
                model="rerank-v3.5",
                query=document_name_or_num,
                documents=docs,
                top_n=min(5, len(docs))
            )
            # Get the top results based on reranking
            top_results = [docs_with_originals[result.index]["original"] for result in reranked.results]

            link_data = [{
                "title": doc.get("documentName"),
                "url": doc.get("documentLink")} for doc in top_results if doc.get("documentLink")]
            artifact_data = get_list_of_artifacts("get_circular_by_doc_name_or_num", link_data)

            # artifact = types.TextContent(
            #     type="text",
            #     text=json.dumps(artifact_data, indent=2, default=str),
            #     title="Reranked Circular Search Results",
            #     format="json"
            # )

            content = types.TextContent(    
                type="text",
                text=json.dumps(top_results, indent=2),
                title=f"Reranked Circulars matching '{document_name_or_num}'",
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
        filtered_hits.append({
            'id': document.get('id'),
            'score': hit.get('text_match', 0),
            'document': document
        })

    documents = [hit['document'] for hit in filtered_hits]
    link_data = []
    for document in documents:

        if document.get("documentLink"):
            link_data.append({
                "title": document.get("documentName"),
                "url": document.get("documentLink")
            })
    artifact = get_list_of_artifacts("get_circular_by_doc_name_or_num",link_data)
    # Format the results
    formatted_results = {
        "found": total_found,
        "out_of": total_found,
        "page": 1,
        "hits": filtered_hits
    }
    content = types.TextContent(
        type="text",
        text=json.dumps(formatted_results, indent=2),
        title=f"Circulars matching '{document_name_or_num}'",
        format="json"
    )

    return [content]+ artifact

async def get_circular_by_maker_and_date_range(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Retrieve circulars for a specific maker issued within a date range.
    If the date range exceeds 1 year, only returns data for the latest 1 year within the range.
    
    Args:
        arguments: Tool arguments including maker name, start date, and end date
        
    Returns:
        List containing the circulars as TextContent and messages about date range handling
    """
    maker = arguments.get("maker")
    start_date_str = arguments.get("start_date", (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
    end_date_str = arguments.get("end_date", datetime.now().strftime('%Y-%m-%d'))
    
    if not maker or not start_date_str or not end_date_str:
        raise ValueError("Maker name, start_date, and end_date are required")
    
    # Convert date strings to datetime objects for comparison
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    # Calculate date range
    date_range = end_date - start_date
    max_range = timedelta(days=365)  # 1 year
    
    # If range exceeds 1 year, adjust start_date to limit to latest 1 year
    message = None
    remaining_range = None
    if date_range > max_range:
        original_start = start_date
        start_date = end_date - max_range
        start_date_str = start_date.strftime('%Y-%m-%d')
        message = f"Note: Date range exceeds 1 year. Returning data from {start_date_str} to {end_date_str}."
        remaining_range = {
            "start_date": original_start.strftime('%Y-%m-%d'),
            "end_date": (start_date - timedelta(days=1)).strftime('%Y-%m-%d')
        }
        
    # Convert dates to UNIX timestamps
    start_timestamp = _date_to_unix_timestamp(start_date_str)
    end_timestamp = _date_to_unix_timestamp(end_date_str)
    date_filter = f"unix_timestamp:>={start_timestamp} && unix_timestamp:<={end_timestamp}"
    
    client = TypesenseClient()

    # Limit to MAX_CIRCULARS items
    typesense_query = {
        "q": maker,
        "query_by": "maker_indexed",
        "filter_by": date_filter,
        "sort_by": "unix_timestamp:desc",
        "include_fields": "documentName,maker,issue_date,equipment,model,summary,documentLink,originalText"
    }
    results = client.collections["full_circulars"].documents.search(typesense_query)
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
                query=maker,
                documents=docs,
                top_n=min(5, len(docs))
            )
            top_results = [docs_with_originals[result.index]["original"] for result in reranked.results]
            
            # Add message about date range if applicable
            if message:
                top_results.insert(0, {"message": message})
                if remaining_range:
                    top_results.insert(1, {"remaining_range": remaining_range})
            
            # Collect link data for artifact
            link_data = []
            for doc in top_results:
                if isinstance(doc, dict) and doc.get("documentLink"):
                    link_data.append({
                        "title": doc.get("documentName"),
                        "url": doc.get("documentLink")
                    })
            artifact_data = get_list_of_artifacts("get_circular_by_maker_and_date_range", link_data)
            # artifact = types.TextContent(
            #     type="text",
            #     text=json.dumps(artifact_data, indent=2, default=str),
            #     title="Reranked Circular Search Results",
            #     format="json"
            # )
            content = types.TextContent(
                type="text",
                text=json.dumps(top_results, indent=2),
                title=f"Reranked Circulars by {maker} between {start_date_str} and {end_date_str}",
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
        filtered_hits.append({
            'id': document.get('id'),
            'score': hit.get('text_match', 0),
            'document': document
        })
    
    # Add message about date range if applicable
    if message:
        filtered_hits.insert(0, {"message": message})
        if remaining_range:
            filtered_hits.insert(1, {"remaining_range": remaining_range})
    
    documents = [f["document"] for f in filtered_hits if "document" in f]
    link_data = []
    for document in documents:
        if document.get("documentLink"):
            link_data.append({
                "title": document.get("documentName"),
                "url": document.get("documentLink")
            })
    artifact_data = get_list_of_artifacts("get_circular_by_maker_and_date_range", link_data)
    # artifact = types.TextContent(
    #     type="text",
    #     text=json.dumps(artifact_data, indent=2, default=str),
    #     title="Circular Search Results",
    #     format="json"
    # )
    formatted_results = {
        "found": total_found,
        "out_of": total_found,
        "page": 1,
        "hits": filtered_hits
    }
    content = types.TextContent(   
        type="text",
        text=json.dumps(formatted_results, indent=2),
        title=f"Circulars by {maker} between {start_date_str} and {end_date_str}",
        format="json"
    )
    return [content]+ artifact_data

async def fetch_circular_details_by_vector_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    This tool provides a flexible way to search circulars based on multiple parameters.
    
    Args:
        arguments: Tool arguments including optional maker, document name, and date range
        
    Returns:
        List containing the circulars as TextContent
    """

    per_page = 20
    page = 1
    all_hits = []
    total_found = None
    client = TypesenseClient()

    # Limit to MAX_CIRCULARS items
    typesense_query = {
        "q": arguments["query"],
        "query_by": "embedding",
        "sort_by": "unix_timestamp:desc",
        "per_page": MAX_CIRCULARS,  # Get only MAX_CIRCULARS items at once
        "include_fields": "documentName,maker,issue_date,equipment,model,summary,documentLink,originalText",
        "prefix": False
    }
    results = client.collections["full_circulars"].documents.search(typesense_query)
    hits = results.get("hits", [])
    total_found = results.get("found", 0)
    all_hits = hits  # Just use the first MAX_CIRCULARS items

    # Comment out the original pagination code
    """
    # Paginate and collect all hits
    while True:
        typesense_query = {
            "q": arguments["query"],
            "query_by": "embedding",
            "sort_by": "unix_timestamp:desc",
            "per_page": per_page,
            "page": page,
            "include_fields": "documentName,maker,issue_date,equipment,model,summary,documentLink,originalText",
            "prefix": False
        }
        results = client.collections["full_circulars"].documents.search(typesense_query)
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
                    query=arguments.get("document_name", arguments["query"]),
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
                artifact_data = get_list_of_artifacts("fetch_circular_details_by_vector_search", link_data)

                # artifact = types.TextContent(
                #     type="text",
                #     text=json.dumps(artifact_data, indent=2, default=str),
                #     title="Reranked Circular Search Results",
                #     format="json"
                # )
                content = types.TextContent(
                    type="text",
                    text=json.dumps(top_results, indent=2),
                    title="Reranked Circular Search Results",
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
        filtered_hits.append({
            'id': document.get('id'),
            'score': hit.get('text_match', 0),
            'document': document
        })
    formatted_results = {
        "found": total_found,
        "out_of": total_found,
        "page": 1,
        "hits": filtered_hits
    }
    content = types.TextContent(
        type="text",
        text=json.dumps(formatted_results, indent=2),
        title=f"Circular Search Results",
        format="json"
    )
    documents = [f["document"] for f in filtered_hits]
    link_data = []
    for document in documents:
        if document.get("documentLink"):
            link_data.append({
                "title": document.get("documentName"),
                "url": document.get("documentLink")
            })
    artifact_data = get_list_of_artifacts("fetch_circular_details_by_vector_search", link_data)
    # artifact = types.TextContent(
    #     type="text",
    #     text=json.dumps(artifact_data, indent=2, default=str),
    #     title="Circular Search Results",
    #     format="json"
    # )
    return [content]+ artifact_data

async def list_all_circular_makers(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Retrieves a list of all manufacturers for circulars in the database.
    Args:
        arguments: No arguments required
    Returns:
        List containing the manufacturers as TextContent
    """
    try:
        client = TypesenseClient()
        per_page = 100
        page = 1
        all_makers = set()
        total_found = None
        while True:
            query = {
                "q": "*",
                "query_by": "maker",
                "group_by": "maker",
                "per_page": per_page,
                "page": page
            }
            results = client.collections["full_circulars"].documents.search(query)
            if total_found is None:
                total_found = results.get("found", 0)
            grouped_hits = results.get("grouped_hits", [])
            for group in grouped_hits:
                if group["group_key"]:
                    all_makers.add(group["group_key"][0])
            if page * per_page >= total_found or not grouped_hits:
                break
            page += 1
        makers = sorted(list(all_makers))
        return [types.TextContent(
            type="text", 
            text=json.dumps(makers, indent=2), 
            title="List of Circular Manufacturers", 
            format="json"
        )]
    except Exception as e:
        logger.error(f"Error fetching list of makers: {str(e)}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Maker Circulars - MAN BW Downloads
# ─────────────────────────────────────────────────────────────────────────────

async def _latest_circulars_manbw_downloads_automation(outfile: Path) -> dict:
    # Initialize result dictionary
    result = {
        "table_data": [],
        "error": None,
        "downloads": []  # List to store download paths
    }

    async with async_playwright() as p:
        logger.info("launch browser (headless)")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to MAN B&W service letters page
            logger.info("Navigating to MAN B&W service letters page")
            await page.goto("https://www.man-es.com/services/industries/marine/service-letters/")
            
            # Accept cookies if present
            try:
                await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=5000)
                await page.click('#onetrust-accept-btn-handler')
                logger.info("Accepted cookies")
            except Exception as e:
                logger.warning(f"No cookie banner found or error accepting cookies: {str(e)}")
            
            # Close any additional dialogs if present
            try:
                await page.wait_for_selector('//a[@class="button-close"]//*[name()="svg"]', timeout=5000)
                await page.click('//a[@class="button-close"]//*[name()="svg"]')
                logger.info("Closed additional dialog")
            except Exception as e:
                logger.warning(f"No dialog to close or error closing dialog: {str(e)}")

            # Setup download path in current directory
            download_path = outfile.parent
            logger.info(f"Download path set to: {download_path}")

            try:
                logger.info("Processing service letter download")
                
                # Get the file details from the specified selector
                details_selector = '#MainContent_C006_Col00 > ul.component.list.list--download > li:nth-child(1) > div > div > div.listItem__dataDetails > span'
                await page.wait_for_selector(details_selector, timeout=30000)
                file_details = await page.inner_html(details_selector)
                logger.info(f"File details: {file_details}")
                
                # Wait for and click the download link using the specific CSS selector
                download_selector = '#MainContent_C006_Col00 > ul.component.list.list--download > li:nth-child(1) > div > div > div.listItem__download > a > span.listItem__downloadFileFormat.listItem__downloadIcon'
                await page.wait_for_selector(download_selector, timeout=30000)
                
                # Get new page when clicking link
                async with page.context.expect_page() as new_page_info:
                    await page.click(download_selector)
                    new_page = await new_page_info.value
                    await new_page.wait_for_load_state("load", timeout=60000)
                
                # Get PDF URL and download
                pdf_url = await new_page.evaluate("window.location.href")
                logger.info(f"Downloading PDF from {pdf_url}")
                
                # Download using page.request
                response = await page.request.get(pdf_url)
                pdf_bytes = await response.body()
                
                # Save the file
                filename = download_path / f"{file_details}.pdf"
                with open(filename, "wb") as f:
                    f.write(pdf_bytes)
                
                logger.info(f"Saved to {filename}")
                result["downloads"].append(str(filename))
                
                # Close the new page
                await new_page.close()
                
                # Update result with downloaded file and file details
                result["table_data"] = [{
                    "text_content": f"Download completed successfully. File details: {file_details}",
                    "file_details": file_details,
                    "download_path": str(filename)
                }]

            except Exception as e:
                error_msg = f"Error downloading service letter: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg

        except Exception as e:
            error_msg = f"Failed to download MAN B&W document: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            # Take screenshot of error state
            try:
                error_screenshot = outfile.parent / "error_screenshot.png"
                await page.screenshot(path=str(error_screenshot))
                logger.info(f"Error screenshot saved to: {error_screenshot}")
            except Exception as screenshot_error:
                logger.error(f"Failed to save error screenshot: {str(screenshot_error)}")
        finally:
            await context.close()
            await browser.close()

    return result

async def latest_circulars_manbw_downloads() -> list[dict]:
    """Download service letters from MAN B&W website.
    
    Returns:
        List of content blocks containing download information and paths
    """
    out = timestamped_filename_pdf(prefix="manbw_download")
    result = await _latest_circulars_manbw_downloads_automation(out)

    # Format the response as a list of content blocks
    content_blocks = []

    # Add download path if available
    if result.get("downloads"):
        content_blocks.append({
            "type": "text",
            "text": f"Downloaded file path: {result['downloads'][0]}"
        })

    # Add table data with file details if available
    if result.get("table_data"):
        content_blocks.append({
            "type": "text",
            "text": f"File details: {result['table_data'][0].get('file_details', '')}"
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
            "text": "No data could be retrieved from MAN B&W website"
        })

    return content_blocks






# ─────────────────────────────────────────────────────────────────────────────
# MongoDB - Get Maker and Model for Particular IMO and Equipment
# ─────────────────────────────────────────────────────────────────────────────


MONGODB_ETL_DATA_URI= os.getenv("MONGODB_ETL_DATA_URI")
MONGODB_ETL_DATA_DB= os.getenv("MONGODB_ETL_DATA_DB")
MONGODB_ETL_DATA_COLLECTION= os.getenv("MONGODB_ETL_DATA_COLLECTION")



async def get_maker_model_for_particular_imo(imo: str) -> list[dict]:
    """
    Query MongoDB for documents matching the given vessel name and return
    maker and model information in the correct format.

    Args:
        vessel_name (str): The name of the vessel to query.

    Returns:
        list[dict]: A list of content blocks containing the query results
    """
    try:
        # Create MongoDB client
        client = MongoClient(MONGODB_ETL_DATA_URI)
        db = client[MONGODB_ETL_DATA_DB]
        coll = db[MONGODB_ETL_DATA_COLLECTION]

        # Regex to match exactly "Diesel Generator" or "Main Engine"
        # component_pattern = re.compile(r'^(Diesel Generator|Main Engine)$', re.IGNORECASE)
        
        component_pattern = re.compile(r'^(AE|ME)$', re.IGNORECASE)

        # Build filter and projection
        filter_query = {
            "imo": int(imo),
             "code": {"$regex": component_pattern}
            # "component": {"$regex": component_pattern}
        }
        projection = {"_id": 0, "vesselName": 1, "makerName": 1, "model": 1, "component": 1}

        # Execute the query
        results = list(coll.find(filter_query, projection))

        # Close the client connection
        client.close()

        # Format results into content blocks
        content_blocks = []
        
        if results:
            # Add a text block with the formatted results
            formatted_text = f"imo: {imo}\n\n"
            for item in results:
                formatted_text += f"Vessel Name: {item.get('vesselName', 'N/A')}\n"
                formatted_text += f"Component: {item.get('component', 'N/A')}\n"
                formatted_text += f"Maker: {item.get('makerName', 'N/A')}\n"
                formatted_text += f"Model: {item.get('model', 'N/A')}\n\n"
            
            content_blocks.append({
                "type": "text",
                "text": formatted_text
            })
        else:
            content_blocks.append({
                "type": "text",
                "text": f"No machinery details found for imo: {imo}"
            })

        return content_blocks

    except errors.PyMongoError as e:
        # Return error message in correct format
        return [{
            "type": "text",
            "text": f"Error querying database: {str(e)}"
        }]


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
            score = SequenceMatcher(None, doc_casefile, casefile.lower()).ratio()
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
