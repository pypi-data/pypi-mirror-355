from vendor_search.databases import *
import json
from typing import Dict, Any, TypedDict, List
from enum import Enum
from typing import Union, Sequence, Optional
from pydantic import BaseModel
import mcp.types as types
from datetime import datetime, timezone
from vendor_search import mcp, logger
from vendor_search.tool_schema import tool_definitions
from rapidfuzz import process, fuzz
import itertools
import asyncio
from .constants import LLAMA_API_KEY, VENDOR_MODEL, PERPLEXITY_API_KEY
from document_parse.main_file_s3_to_llamaparse import parse_to_document_link
import time

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
            elif name == "typesense_query":
                return await typesense_query(arguments)
            elif name == "find_relevant_vendors":
                return await vendor_search(arguments)
            elif name == "get_vendor_contact_details":
                return await get_vendor_contact_info(arguments)

            # Document Parsing Tool Handlers
            elif name == "parse_document_link":
                return await parse_document_link(arguments)

            elif name == "create_update_casefile":
                return await create_update_casefile(arguments)
            elif name == "google_search":
                return await google_search(arguments)

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise ValueError(f"Error calling tool {name}: {str(e)}")


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
        Handle Typesense query tool
        
        Args:
            arguments: Tool arguments including collection and query parameters
            
        Returns:
            List containing the search results as TextContent
        """
    collection = arguments.get("collection")
    query = arguments.get("query", {})
    if not collection:
            raise ValueError("Collection name is required")
        
    try:
        typesense_client = TypesenseClient()
        results = typesense_client.collections[collection].documents.search(query)
        # Format the results
        formatted_results = {
            "found": results.get("found", 0),
            "out_of": results.get("out_of", 0),
            "page": results.get("page", 1),
            "hits": [hit.get("document") for hit in results.get("hits", [])]
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
        
            
        return [content]
    except Exception as e:
        logger.error(f"Error searching collection {collection}: {e}")
        raise ValueError(f"Error searching collection: {str(e)}")



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
        if not collection:
            raise ValueError("Collection name is required")
        
        try:
            # Make sure all required keys are present (even if None)
            for key in ["vendorName", "service", "locationRegion"]:
                arguments.setdefault(key, None)

            results = query_vendor_search(arguments)
            results_text = json.dumps(results, indent=2)
            # Create TextContent with all required fields
            content = types.TextContent(
                type="text",                # Required field
                text=results_text,            # The actual text content
                title=f"Vendor Search Results",
                format="json"
            )
            
            return [content]
        except Exception as e:
            logger.error(f"Error retrieving stats for collection {collection}", e)
            raise ValueError(f"Error retrieving collection stats: {str(e)}") 
    
async def get_vendor_contact_info(arguments: Dict[str, Any]) -> List[Union[types.TextContent, types.ImageContent]]:
        """
        Handle Typesense get contact info tool
        
        """
        typesense_client = TypesenseClient()
        collection = "vendor4"

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
            
            

            # Log the content for debugging
            logger.info(f"Created search results TextContent: {type(content)}")
            
            return [content]
        except Exception as e:
            logger.error(f"Error searching collection {collection}", e)
            raise ValueError(f"Error searching collection: {str(e)}")
        
#Helper functions
from pymongo import MongoClient
import cohere

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