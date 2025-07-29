from imo_publications.databases import *
import json
from typing import Dict, Any, TypedDict
from enum import Enum
from typing import Union, Sequence, Optional
from pydantic import BaseModel
import mcp.types as types
from imo_publications import mcp, logger
import requests
from imo_publications.tool_schema import tool_definitions
import datetime
from typing import Any, Dict, List, Union, Sequence
import cohere
from .constants import COHERE_API_KEY, LLAMA_API_KEY, VENDOR_MODEL, PERPLEXITY_API_KEY
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
    """Register all tools with the MCP server."""
    @mcp.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List all available tools."""
        return server_tools

    @mcp.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> Sequence[Union[types.TextContent, types.ImageContent, types.EmbeddedResource]]:
        """Call a specific tool by name with the given arguments."""
        try:
            if name == "list_imo_publications":
                return await fetch_list_of_imo_publication(arguments)
            elif name == "fetch_imo_publication_by_vector_search":
                return await fetch_imo_publication_by_vector_search(arguments)
            elif name == "get_by_imo_publication_name":
                return await get_by_imo_publication_name(arguments)
            elif name == "parse_document_link":
                return await parse_document_link(arguments)
            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            elif name == "google_search":
                return await google_search(arguments)
            elif name == "smart_imo_publication_search":
                return await smart_imo_publication_search(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise ValueError(f"Error calling tool {name}: {str(e)}")
        
# Helper functions


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



# ------------------- IMO Publication Tool Handlers -------------------

async def fetch_list_of_imo_publication(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Retrieve a comprehensive list of all available IMO publications.
    
    Args:
        arguments: No arguments required
        
    Returns:
        List containing the IMO publications as TextContent
    """
    typesense_query = {
        "q": "*",
        "query_by": "documentName",
        "group_by": "documentName",
        "per_page": 20
    }
    
    try:
        client = TypesenseClient()
        results = client.collections["imo_publication"].documents.search(typesense_query)
        
        # Extract unique document names from results
        documents = []
        if "grouped_hits" in results:
            documents = [group["group_key"][0] for group in results["grouped_hits"]]
        
        return [types.TextContent(
            type="text",
            text=json.dumps(documents, indent=2),
            title="List of IMO Publications",
            format="json"
        )]
    except Exception as e:
        logger.error("Error fetching list of IMO publications", e)
        raise

async def fetch_imo_publication_by_vector_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Performs a targeted search across IMO publications using Typesense and applies Cohere reranking if results are not too many.
    Uses the 'query' argument for Typesense search (default is '*').
    """
    query = arguments.get("query", "*")
    client = TypesenseClient()

    typesense_query = {
        "q": query,
        "query_by": "embedding",
        "include_fields": "documentName,chapter,revDate,revNo,summary,documentLink,originalText",
        "prefix": False,
        "per_page": 20   
    }
    results = client.collections["imo_publication"].documents.search(typesense_query)
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
                artifacts = get_list_of_artifacts("fetch_imo_publication_by_vector_search", link_data)

                content = types.TextContent(
                    type="text",
                    text=json.dumps(top_results, indent=2),
                    title="Reranked IMO Publication Search Results",
                    format="json"
                )
                return [content] + artifacts
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
    artifacts = get_list_of_artifacts("fetch_imo_publication_by_vector_search", link_data)

    content = types.TextContent(   
        type="text",
        text=json.dumps(filtered_hits, indent=2),
        title="IMO Publication Search Results",
        format="json"
    )
    return [content] + artifacts

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

async def get_by_imo_publication_name(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """
    Locates specific IMO publications using any part of the document name or reference number, with optional Cohere reranking.
    """
    document_name = arguments.get("document_name", "")
    if not document_name:
        raise ValueError("document_name is required")
    client = TypesenseClient()
    MAX_DOCUMENTS = 20
    # Use wildcards for partial match
    typesense_query = {
        "q": f"*{document_name}*",
        "query_by": "documentName",
        "include_fields": "documentName,chapter,revDate,revNo,summary,documentLink,originalText",
        "per_page": MAX_DOCUMENTS,
        "prefix": True
    }
    results = client.collections["imo_publication"].documents.search(typesense_query)
    hits = results.get("hits", [])
    all_hits = hits

    # If we have results and <= 50, apply Cohere reranking
    if all_hits and COHERE_API_KEY and len(all_hits) <= MAX_DOCUMENTS:
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
                artifacts = get_list_of_artifacts("get_by_imo_publication_name", link_data)

                content = types.TextContent(
                    type="text",
                    text=json.dumps(top_results, indent=2),
                    title="Reranked IMO Publication Name Search Results",
                    format="json"
                )
                return [content] + artifacts
        except Exception as e:
            logger.error(f"Error in Cohere reranking: {e}")
            # Fall back to original results if reranking fails

    # Return all results if no reranking was done
    filtered_hits = []
    for hit in all_hits:
        document = hit.get('document', {})
        document.pop('embedding', None)
        filtered_hits.append(document)

    link_data = []
    for document in filtered_hits:
        link_data.append({
            "title": document.get("documentName"),
            "url": document.get("documentLink")
        })
    artifacts = get_list_of_artifacts("get_by_imo_publication_name", link_data)

    content = types.TextContent(
        type="text",
        text=json.dumps(filtered_hits, indent=2),
        title="IMO Publication Name Search Results",
        format="json"
    )
    return [content] + artifacts

async def smart_imo_publication_search(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
    """Universal search tool for IMO publications with intelligent query processing."""
    try:
        collection = "imo_publication"
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
                elif field == "document_name":
                    # For document name, we'll use it in the query instead of filter
                    continue
                else:
                    filter_parts.append(f"{field}:{sanitize_filter_value(value)}")
        filter_string = " && ".join(filter_parts) if filter_parts else None

        # Enhance query based on document_name filter if present
        enhanced_query = query
        if filters.get("document_name") and query:
            enhanced_query = f"{query} {filters['document_name']}"
        elif filters.get("document_name") and not query:
            enhanced_query = filters["document_name"]

        # # Build the search query
        # if search_type == "browse":
        #     search_query = {
        #         "q": "*",
        #         "query_by": "documentName,chapter,section",
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
        #         "query_by": "documentName,chapter,section",
        #         "per_page": max_results,
        #         "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
        #     }
        # else:  # hybrid
        #     search_query = {
        #         "q": enhanced_query,
        #         "query_by": "embedding,documentName,chapter,section",
        #         "prefix": False,
        #         "per_page": max_results,
        #         "include_fields": "documentHeader,documentName,chapter,section,revNo,originalText,documentLink"
        #     }

        # # Add filters if any
        if filter_string:
            search_query["filter_by"] = filter_string

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
                artifact_data = get_list_of_artifacts("smart_imo_publication_search",link_data)
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
        artifacts = get_list_of_artifacts("smart_imo_publication_search", link_data)

        return [content] + artifacts
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error retrieving search results: {str(e)}",
            title="Error",
            format="json"
        )]
