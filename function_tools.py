import json
from openai import OpenAI
import requests
from urllib.parse import quote_plus, urlencode
from rag import generate_rag_runnable_chain
# import streamlit as st
import os
from dotenv import load_dotenv

if os.getenv("DEPLOYMENT_ENVIRONMENT", "development") != "production":
    load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
gpt_model = os.getenv("GPT_MODEL")
fosrc_server_link = os.getenv("FOSRC_SERVER_LINK")

system_message = """
You are a helpful assistant for the Federal Open Science Repository of Canada (FOSRC). Always be accurate. If you don't know the answer, say so. Do not add any of the following search filters unless specified by the user: size filter, search query filter, the authors filter, the subjects filter, the min date filter, the max date filter, the communities filter, and the item types filter.

Search results should be presented as a numbered list of items in the following format:

*Title*
*Link*

where *Title* is only the result title, and *Link* is only the result link. If the title is missing, still present the item with the link.
"""

def custom_title_capitalization(text_string, no_caps_list=None):
    if no_caps_list is None:
        no_caps_list = ["a", "an", "the", "and", "but", "or", "for", "nor", "on", "in", "at", "to", "with", "of"]

    words = []
    for word in text_string.split():
        if word.lower() not in no_caps_list:
            words.append(word.capitalize())
        else:
            words.append(word.lower())  # Keep excluded words in lowercase
    return " ".join(words)

def get_search_results_count(search_query, authors, subjects, min_date, max_date, item_types, communities):
    print(f"get_search_results_count() called for search term: {search_query}")
    
    url = fosrc_server_link + "/server/api/discover/search/objects"

    params = {
        "sort": "score,DESC",
        "page": 0,
        "size": 0,
        "query": search_query if search_query else ""
    }

    encoded_query_params_string = urlencode(params)

    additional_query_parameters = []

    if authors:
        for author in authors:
            if author:
                additional_query_parameters.append("f.author=" + quote_plus(custom_title_capitalization(author)) + ",equals")

    if subjects:
        for subject in subjects:
            if subject:
                additional_query_parameters.append("f.subjectEn=" + quote_plus(subject.capitalize()) + ",equals")

    date_range_string = ""

    if min_date and max_date:
        date_range_string = f"[{min_date} TO {max_date}]"
    elif min_date and not max_date:
        date_range_string = f"[{min_date} TO *]"
    elif max_date and not min_date:
        date_range_string = f"[* TO {max_date}]"

    if date_range_string:
        additional_query_parameters.append("f.dateIssued=" + quote_plus(date_range_string) + ",equals")

    if item_types:
        for item_type in item_types:
            if item_type:
                additional_query_parameters.append("f.itemtype_en=" + quote_plus(item_type.capitalize()) + ",equals")

    if communities:
        for community in communities:
            if community:
                additional_query_parameters.append("f.community_en=" + quote_plus(custom_title_capitalization(community)) + ",equals")
    
    additional_query_parameters_string = "&".join(additional_query_parameters)

    modified_url = url + "?" + encoded_query_params_string + "&" + additional_query_parameters_string
    
    print(modified_url)

    response = requests.get(modified_url)

    # Check the status code
    if response.status_code == 200:
        print("Request successful!")

        response_json = response.json()

        extracted_results_count = response_json.get("_embedded").get("searchResult").get("page").get("totalElements")
        print(extracted_results_count)

        return str(extracted_results_count)
    
    else:
        print(f"Request failed with status code: {response.status_code}")
        return ""
    
get_search_results_count_function = {
    "name": "get_search_results_count",
    "description": "In FOSRC, get the number of search results based on the following filters: search query filter, the authors filter, the subjects filter, the min date filter, the max date filter, the communities filter, and the item types filter.",
    "parameters": {
        "type": "object",
        "properties": {
            "search_query": {
                "type": ["string", "null"],
                "description": "The search query filter.",
            },
            "authors": {
                "type": "array",
                "description": "A list of authors for filtering the query.",
                "items": {
                    "type": ["string", "null"],
                    "description": "An author."
                }
            },
            "subjects": {
                "type": "array",
                "description": "A list of subjects for filtering the query.",
                "items": {
                    "type": ["string", "null"],
                    "description": "A subject."
                }
            },
            "min_date": {
                "type": ["string", "null"],
                "description": "The min date filter. Only the year.",
            },
            "max_date": {
                "type": ["string", "null"],
                "description": "The max date filter. Only the year.",
            },
            "item_types": {
                "type": "array",
                "description": "A list of item types for filtering the query. Only include if specified by the user.",
                "items": {
                    "type": ["string", "null"],
                    "enum": [
                        "",
                        "Article",
                        "Report",
                        "Accepted manuscript",
                        "Internal report",
                        "Departmental report",
                        "Submitted manuscript",
                        "Consultant report",
                        "Other",
                        "Book",
                        "Book chapter",
                        "Conference proceeding or paper",
                        "Whitepaper",

                        # "Article",
                        # "Rapport",
                        # "Manuscrit accepté",
                        # "Rapport interne",
                        # "Rapport ministériel",
                        # "Manuscrit soumis",
                        # "Rapport de consultant",
                        # "Autre",
                        # "Livre",
                        # "Chapitre du livre",
                        # "Actes ou article de conférence",
                        # "Livre blanc"
                        ],
                    "description": "An item type."
                }
            },
            "communities": {
                "type": "array",
                "description": "A list of communities for filtering the query. Only include if specified by the user.",
                "items": {
                    "type": ["string", "null"],
                    "description": "A community."
                }
            },
        },
        "required": ["search_query", "authors", "subjects", "min_date", "max_date", "item_types", "communities"],
        "additionalProperties": False
    }
}

def get_search_results(size, search_query, authors, subjects, min_date, max_date, item_types, communities):
    print(f"get_search_results_count() called for search term: {search_query}")
    
    url = fosrc_server_link + "/server/api/discover/search/objects"

    params = {
        "sort": "score,DESC",
        "page": 0,
        "size": size if size else "10",
        "query": search_query if search_query else ""
    }

    encoded_query_params_string = urlencode(params)

    additional_query_parameters = []

    if authors:
        for author in authors:
            if author:
                additional_query_parameters.append("f.author=" + quote_plus(custom_title_capitalization(author)) + ",equals")

    if subjects:
        for subject in subjects:
            if subject:
                additional_query_parameters.append("f.subjectEn=" + quote_plus(subject.capitalize()) + ",equals")

    date_range_string = ""

    if min_date and max_date:
        date_range_string = f"[{min_date} TO {max_date}]"
    elif min_date and not max_date:
        date_range_string = f"[{min_date} TO *]"
    elif max_date and not min_date:
        date_range_string = f"[* TO {max_date}]"

    if date_range_string:
        additional_query_parameters.append("f.dateIssued=" + quote_plus(date_range_string) + ",equals")

    if item_types:
        for item_type in item_types:
            if item_type:
                additional_query_parameters.append("f.itemtype_en=" + quote_plus(item_type.capitalize()) + ",equals")

    if communities:
        for community in communities:
            if community:
                additional_query_parameters.append("f.community_en=" + quote_plus(custom_title_capitalization(community)) + ",equals")
    
    additional_query_parameters_string = "&".join(additional_query_parameters)

    modified_url = url + "?" + encoded_query_params_string + "&" + additional_query_parameters_string
    
    print(modified_url)

    response = requests.get(modified_url)

    # Check the status code
    if response.status_code == 200:
        print("Request successful!")

        response_json = response.json()

        extracted_results = response_json.get("_embedded").get("searchResult").get("_embedded").get("objects") or []

        modified_results_list = []

        for result in extracted_results:
            modified_result = {
                "title": result.get("_embedded").get("indexableObject").get("name"),
                # "abstract": result.get("_embedded").get("indexableObject").get("metadata").get("dc.description.abstract", [])[0].get("value"),
                "link": (fosrc_server_link + "/items/" + result.get("_embedded").get("indexableObject").get("id")) if result.get("_embedded").get("indexableObject").get("id", "") else "",
            }
            modified_results_list.append(str(modified_result))

        return ", ".join(modified_results_list)
    
    else:
        print(f"Request failed with status code: {response.status_code}")
        return ""
    
get_search_results_function = {
    "name": "get_search_results",
    "description": "In FOSRC, fetch the search results based on the following filters: size filter, search query filter, the authors filter, the subjects filter, the min date filter, the max date filter, the communities filter, and the item types filter.",
    "parameters": {
        "type": "object",
        "properties": {
            "size": {
                "type": ["string", "null"],
                "description": "The size filter which indicates the number of results to return. Only include if specified by the user.",
            },
            "search_query": {
                "type": ["string", "null"],
                "description": "The search query filter.",
            },
            "authors": {
                "type": "array",
                "description": "A list of authors for filtering the query.",
                "items": {
                    "type": ["string", "null"],
                    "description": "An author."
                }
            },
            "subjects": {
                "type": "array",
                "description": "A list of subjects for filtering the query.",
                "items": {
                    "type": ["string", "null"],
                    "description": "A subject."
                }
            },
            "min_date": {
                "type": ["string", "null"],
                "description": "The min date filter. Only the year.",
            },
            "max_date": {
                "type": ["string", "null"],
                "description": "The max date filter. Only the year.",
            },
            "item_types": {
                "type": "array",
                "description": "A list of item types for filtering the query. Only include if specified by the user.",
                "items": {
                    "type": ["string", "null"],
                    "enum": [
                        "",
                        "Article",
                        "Report",
                        "Accepted manuscript",
                        "Internal report",
                        "Departmental report",
                        "Submitted manuscript",
                        "Consultant report",
                        "Other",
                        "Book",
                        "Book chapter",
                        "Conference proceeding or paper",
                        "Whitepaper",

                        # "Article",
                        # "Rapport",
                        # "Manuscrit accepté",
                        # "Rapport interne",
                        # "Rapport ministériel",
                        # "Manuscrit soumis",
                        # "Rapport de consultant",
                        # "Autre",
                        # "Livre",
                        # "Chapitre du livre",
                        # "Actes ou article de conférence",
                        # "Livre blanc"
                        ],
                    "description": "An item type."
                }
            },
            "communities": {
                "type": "array",
                "description": "A list of communities for filtering the query. Only include if specified by the user.",
                "items": {
                    "type": ["string", "null"],
                    "description": "A community."
                }
            },
        },
        "required": ["size", "search_query", "authors", "subjects", "min_date", "max_date", "item_types", "communities"],
        "additionalProperties": False
    }
}



def get_rag_response(user_question):
    chain = generate_rag_runnable_chain()

    generated_prompt = chain.invoke(user_question)

    messages = [{"role": "system", "content": generated_prompt.to_string()}]

    response = get_open_ai_response(messages=messages, use_tools=False)

    return response


get_rag_response_function = {
    "name": "get_rag_response",
    "description": "Fetch the answer to a question based on resources in FOSRC.",
    "parameters": {
        "type": "object",
        "properties": {
            "user_question": {
                "type": ["string", "null"],
                "description": "The user's question.",
            }
        },
        "required": ["user_question"],
        "additionalProperties": False
    }
}


def get_open_ai_response(messages = [], use_tools = True):
    openai = OpenAI(api_key=openai_api_key)
    if use_tools:
        return openai.chat.completions.create(
            model=gpt_model,
            # Optional setting for maximum tokens allowed for the response
            max_tokens=1000,

            # Optional setting for temperature; default is 1; temperature
            # can be set up to 2 for more answer randomness/creativity
            temperature=1,

            messages=messages,
            tools=[
                {"type": "function", "function": get_search_results_count_function},
                {"type": "function", "function": get_search_results_function},
                {"type": "function", "function": get_rag_response_function},
            ]
        )
    else:
        return openai.chat.completions.create(
            model=gpt_model,
            max_tokens=1000,
            temperature=1,
            messages=messages
        )

def handle_tool_calls(message):
    responses = []
    for tool_call in message.tool_calls:
        if tool_call.function.name == "get_search_results_count":
            arguments = json.loads(tool_call.function.arguments)
            search_query = arguments.get('search_query')
            authors = arguments.get('authors')
            subjects = arguments.get('subjects')
            min_date = arguments.get('min_date')
            max_date = arguments.get('max_date')
            item_types = arguments.get('item_types')
            communities = arguments.get('communities')
            
            search_results_count = get_search_results_count(
                search_query = search_query, 
                authors = authors, 
                subjects = subjects, 
                min_date = min_date, 
                max_date = max_date, 
                item_types = item_types,
                communities = communities
            )
            responses.append({
                "role": "tool",
                "content": search_results_count,
                "tool_call_id": tool_call.id
            })
        if tool_call.function.name == "get_search_results":
            arguments = json.loads(tool_call.function.arguments)
            size = arguments.get('size')
            search_query = arguments.get('search_query')
            authors = arguments.get('authors')
            subjects = arguments.get('subjects')
            min_date = arguments.get('min_date')
            max_date = arguments.get('max_date')
            item_types = arguments.get('item_types')
            communities = arguments.get('communities')
            
            search_results = get_search_results(
                size = size,
                search_query = search_query, 
                authors = authors, 
                subjects = subjects, 
                min_date = min_date, 
                max_date = max_date, 
                item_types = item_types,
                communities = communities
            )

            # print(search_results)
            responses.append({
                "role": "tool",
                "content": search_results,
                "tool_call_id": tool_call.id
            })
        if tool_call.function.name == "get_rag_response":
            arguments = json.loads(tool_call.function.arguments)
            user_question = arguments.get('user_question')
            
            response = get_rag_response(
                user_question = user_question,
            )

            print(response)

            responses.append({
                "role": "tool",
                "content": "Repeat the following text EXACTLY:\n" + response.choices[0].message.content if response.choices[0].message.content else "Repeat the following text EXACTLY:\nThe information is not available in FOSRC",
                "tool_call_id": tool_call.id
            })
    return responses

def get_fosrc_answer(user_question):
    messages = [{"role": "system", "content": system_message}] + [{"role": "user", "content": user_question}]
    response = get_open_ai_response(messages=messages)

    print(response)

    while response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message
        responses = handle_tool_calls(message)
        messages.append(message)
        messages.extend(responses)
        response = get_open_ai_response(messages=messages)
    
    return response.choices[0].message.content