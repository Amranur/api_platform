import json
import re
import aiohttp
import requests
from datetime import datetime

def clean_whitespace(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_current_date_and_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def call_llm_api(messages):
    url = "http://36.50.40.36:11434/api/chat"
    data = {
        "model": "llama3.2:latest",
        "messages": messages,
        "stream": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                async for line in response.content:
                    if line:
                        try:
                            json_line = json.loads(line.decode('utf-8'))
                            if 'message' in json_line and 'content' in json_line['message']:
                                yield json_line['message']['content']
                        except json.JSONDecodeError:
                            print("Failed to decode JSON:", line)
            else:
                print("Error:", response.status, await response.text())
                yield f"Error: {response.status}"

async def call_embedding_api(texts):
    url = "http://36.50.40.36:11434/api/embeddings"
    embeddings = []
    print("come and embedding....")
    async with aiohttp.ClientSession() as session:
        for text in texts:
            data = {
                "model": "all-minilm:33m",
                "prompt": text
            }
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    embedding_response = await response.json()
                    if 'embedding' in embedding_response and embedding_response['embedding']:
                        embeddings.append(embedding_response['embedding'])
                    else:
                        print(f"No embedding generated for '{text}':", embedding_response)
                        embeddings.append([])  # Append an empty list if no embedding is generated
                else:
                    print("Error:", response.status, await response.text())
                    embeddings.append([])  # Append an empty list on error
                    
    return embeddings

async def stream_chat_ollama(query: str, model: str):
    try:
        # Construct messages in the required format
        messages = [
            {
                "role": "system",
                "content": f"Please note that the current date and time is: {get_current_date_and_time}. I will provide the best answer as an expert."
            },
            {
                "role": "user",
                "content": f"Please give the best answer for the chat query: {query}."
            }
        ]
        
        # Call LLM API with the constructed messages
        async for response in call_llm_api(messages):
            yield response
    except Exception as e:
        print(f"An error occurred: {e}")
        yield f"Error: {e}"



async def stream_summarize_embed(content_list, embeddings, query):
    try:
        # Combine content and embeddings
        embedded_content = "\n\n".join(
            f"Content section {i+1} with embedding {embeddings[i]}:\n{content}"
            for i, content in enumerate(content_list)
        )
        print("come")

        # Construct messages for summarization
        messages = [
            {
                "role": "system",
                "content": (
                    f"Please note that the current date and time is: {get_current_date_and_time}. "
                    "I will provide a summary and analysis of the main points as an expert. "
                    "The content below includes embedded representations for enhanced relevance."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Please summarize and analyze the main points of the following content, with "
                    f"embeddings for context. The query was: {query}. The  content is: {content_list}"
                )
            }
        ]

        # Stream responses from LLM API
        async for response in call_llm_api(messages):
            yield response

    except Exception as e:
        print(f"An error occurred: {e}")
        yield f"Error: {e}"

    except Exception as e:
        print(f"An error occurred: {e}")
        yield f"Error: {e}"


async def stream_summarize(content: str, query: str):
    try:
        # Construct messages in the required format
        messages = [
    {
        "role": "system",
        "content": "You are an expert AI model tasked with summarizing, analyzing, and answering queries based on provided content and if need use your own expert knowledge. Use the latest available information for your responses."
    },
    {
        "role": "user",
        "content": (f"The current task is to process the following information retrieved for the query: '{query}'. "
                    "First, provide a concise summary of the content. "
                    "Next, analyze the main points and implications of the information. "
                    "Finally, based on this analysis, answer the query provided. "
                    "If the content does not fully address the query, use your own expert knowledge to provide a complete answer. "
                    f"The content is: {content}.")
    }
]
        
        # Call LLM API with the constructed messages and stream responses
        async for response in call_llm_api(messages):
            yield response

    except Exception as e:
        yield f"Error: {e}"











# async def summarize_without_embed(content: str, query: str):
#     try:
#         messages = [
#             {
#                 "role": "system",
#                 "content": "Please note that the current date and time is: {get_current_date_and_time}. I will provide a summary and analysis of the main points as an expert."
#             },
#             {
#                 "role": "user",
#                 "content": f"Please summarize and analyze the main points of the following content retrieved from various URLs and search engines for the query: {query}. The content is: {content}"
#             }
#         ]

#         # Collect responses from the async generator
#         responses = []
#         async for response in call_llm_api(messages):
#             responses.append(response)

#         return responses  # Return collected responses as a list

#     except Exception as e:
#         return [f"Error: {e}"]  # Return error message as a list



