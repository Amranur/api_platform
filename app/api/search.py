from groq import Groq
import httpx
import logging
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, WebSocket, Depends, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from pydantic import BaseModel
from typing import List, Dict
import re
import requests
from requests.exceptions import SSLError
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, Session, relationship
from langchain_community.utilities import SearxSearchWrapper
from langchain_community.document_loaders import WebBaseLoader

from app.database import get_db
from app.models import APIKey, RequestLog, User, UserPlan

router = APIRouter()

# Clean whitespace function

# Initialize Groq client with direct API key
api_key = "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"
client = Groq(api_key=api_key)
#SEARXNG_API_URL = "https://searsobjanta-gkd0dyewhyaug0as.eastus-01.azurewebsites.net/search"
SEARXNG_API_URL = "http://36.50.40.36:8888/search"

@router.websocket("/playground")
async def websocket_search(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()

    try:
        # Receive the input from WebSocket
        data = await websocket.receive_json()
        query = data.get("query")
        api_key = data.get("api_key")
        model = data.get("model", "llama-3.1-70b-versatile")

        # API Key Validation Logic
        # db_key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.status == True).first()
        # if not db_key:
        #     await websocket.send_json({"error": "Invalid or disabled API key"})
        #     await websocket.close()
        #     return

        # # User and Role Check
        # user = db.query(User).filter(User.id == db_key.user_id).first()
        # if user.role == "customer":
        #     query_count = db.query(func.count(RequestLog.id)).filter(RequestLog.api_key == api_key).scalar()
        #     if query_count >= 5:
        #         await websocket.send_json({"message": "Your free quota is over. Please make a payment."})
        #         await websocket.close()
        #         return

        # Log the Request
        # log = RequestLog(api_key=api_key, query=query, model_id=model)
        # db.add(log)
        # db.commit()

        # Perform the search or summarization
        # This example assumes you want to stream content from a summarization model
        summary_generator = summarize_content_model(query, model)

        async for partial_summary in summary_generator:
            await websocket.send_json({"partial_summary": partial_summary})

        await websocket.send_json({"message": "Summary complete"})
        await websocket.close()

    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()

@router.get("/playground")
def search_old(query: str, api_key: str, model: str = "llama-3.1-70b-versatile", db: Session = Depends(get_db)):
    # Check if API key exists and is active
    db_key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.status == True).first()
    if not db_key:
        raise HTTPException(status_code=403, detail="Invalid or disabled API key")

    # Retrieve the user associated with the API key
    user = db.query(User).filter(User.id == db_key.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User associated with the API key not found")

    # Check if the user has the role 'customer'
    if user.role == "customer":
        # Count the number of queries made with this API key
        query_count = db.query(func.count(RequestLog.id)).filter(RequestLog.api_key == api_key).scalar()

        # Check if the number of queries exceeds the free quota
        if query_count >= 10:
            return {"message": "Your free quota is over. Please make a payment to continue using the service."}

    # Log the request
    log = RequestLog(api_key=api_key, query=query,model_id=model)
    db.add(log)
    db.commit()

    # # Perform the search using SearxNG
    # search = SearxSearchWrapper(searx_host="https://searxng-n113.onrender.com/search?format=json")
    # results = search.results(query, num_results=10, engines=[])

    # all_cleaned_content = []
    # for result in results[:5]:
    #     url = result['link']
    #     print(f"Fetching {url}:")
        
    #     loader = WebBaseLoader(url)
    #     try:
    #         docs = loader.load()
    #         page_content = docs[0].page_content
    #         cleaned_content = clean_whitespace(page_content)
    #         all_cleaned_content.append(cleaned_content)
    #     except requests.exceptions.SSLError as e:
    #         print(f"SSL Error while fetching {url}: {e}")
    #     except Exception as e:
    #         print(f"Error while processing {url}: {e}")

    # combined_content = "\n\n---\n\n".join(all_cleaned_content)
    summary = summarize_content_model("combined_content", query, model)
    # summary = summarize_content(combined_content,query)
    
    return {"summary": summary}

def summarize_content_model(content: str, query: str, model: str = "llama-3.1-70b-versatile") -> str:
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"Please note that the current date and time is: {get_current_date_and_time}. I will provide a summary and analysis of the main points as an expert."
                },
                {
                    "role": "user",
                    "content": f"Please do answer as professional way for this question : {query}"
                }
            ],
            model=model,  # Use the input model here
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return ''

def get_current_date_and_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def summarize_content(content: str,query: str,) -> str:
    try:
        chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"Please note that the current date and time is: {get_current_date_and_time}. I will provide a summary and analysis of the main points as an expert."
            },
            {
                "role": "user",
                "content": f"Please summarize and analyze the main points of the following content retrieved from various URLs and search engines for the query: {query}. The content is: {content}"
            }
        ],
        model="llama-3.1-70b-versatile",
)
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return ''



# Search function using the API key
@router.get("/searchsummary")
async def searchsummary( q: str = Query(..., description="The search query"),
    categories: str = Query("general", description="The categories to filter by"),
    engines: str = Query("all", description="The engines to use"),
    format: str = Query("json", description="The response format")):
    try:
        # Increase timeout to 10 seconds
        timeout = httpx.Timeout(100.0, read=100.0)
        params = {
            "q": q,
            "categories": categories if categories else "general",  # Default to "general" if None
            "engines": engines if engines else "all",  # Default to "all" if None
            "format": format if format else "json",  # Use provided format, default to "json"
        }
        # Making an asynchronous GET request to SearxNG API with the search query and increased timeout
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(SEARXNG_API_URL, params=params)

        # Log response status and content
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response Content: {response.text}")

        # Check if the SearxNG API request was successful
        if response.status_code == 200:
            search_results = response.json().get("results", [])  # Extract the results from the response

            # Initialize list to store cleaned content
            all_cleaned_content = []

            # Process only the top 7 search results
            for result in search_results[:10]:
                url = result.get('url')  # Adjust key based on your actual response structure
                #logging.debug(f"Fetching {url}:")
                
                loader = WebBaseLoader(url)
                try:
                    # Load and clean the content from the URL
                    docs = loader.load()
                    page_content = docs[0].page_content
                    #print(page_content)
                    cleaned_content = clean_whitespace(page_content)
                    #print(cleaned_content)
                    all_cleaned_content.append(cleaned_content)
                except httpx.RequestError as e:
                    logging.error(f"Request Error while fetching {url}: {e}")
                    continue
                except Exception as e:
                    logging.error(f"Error while processing {url}: {e}")
                    continue 

            # Combine all cleaned content and summarize it
            combined_content = "\n\n---\n\n".join(all_cleaned_content)
            summary = summarize_content(combined_content,q)
            return {"summary": summary}  # Return the summarized content

        else:
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching data from SearxNG API: {response.text}")

    except httpx.RequestError as exc:
        # Handle any request errors, such as connection issues
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting SearxNG API: {exc}")

@router.get("/searchsummarymultiple")
async def searchsummary2(
    q: str = Query(..., description="The search query"),
    categories: str = Query("general", description="The categories to filter by"),
    engines: str = Query("all", description="The engines to use"),
    format: str = Query("json", description="The response format")
):
    try:
        # Increase timeout to 100 seconds
        timeout = httpx.Timeout(100.0, read=100.0)
        params = {
            "q": q,
            "categories": categories if categories else "general",  # Default to "general" if None
            "engines": engines if engines else "all",  # Default to "all" if None
            "format": format if format else "json",  # Use provided format, default to "json"
        }
        # Making an asynchronous GET request to SearxNG API with the search query and increased timeout
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(SEARXNG_API_URL, params=params)

        # Log response status and content
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response Content: {response.text}")

        # Check if the SearxNG API request was successful
        if response.status_code == 200:
            search_results = response.json().get("results", [])  # Extract the results from the response

            # Initialize list to store cleaned content
            url_contents = []

            # Process the top results
            for result in search_results[:5]:
                url = result.get('url')  # Adjust key based on your actual response structure
                title = result.get("title")
    
                loader = WebBaseLoader(url)
                try:
                    # Load and clean the content from the URL
                    docs = loader.load()
                    page_content = docs[0].page_content
                    cleaned_content = clean_whitespace(page_content)

                    # Store the cleaned content with URL
                    url_contents.append({"url": url,"title": title, "content": cleaned_content})
                except httpx.RequestError as e:
                    logging.error(f"Request Error while fetching {url}: {e}")
                    continue
                except Exception as e:
                    logging.error(f"Error while processing {url}: {e}")
                    continue 

            # Summarize content for each URL
            summaries = []
            for item in url_contents:
                title = item["title"]
                url = item["url"]
                content = item["content"]
                summary =  summarize_content(content, q)
                summaries.append({"url": url,"title": title, "summary": summary})

            return {"summaries": summaries}  # Return the summarized content

        else:
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching data from SearxNG API: {response.text}")

    except httpx.RequestError as exc:
        # Handle any request errors, such as connection issues
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting SearxNG API: {exc}")
    
# Configure logging to output debug information
logging.basicConfig(level=logging.DEBUG)



@router.get("/playground-json")
def search_pg_json(query: str, 
                   api_key: str,
                   categories: str = Query("general", description="The categories to filter by"),
                    engines: str = Query("all", description="The engines to use"),
                    format: str = Query("json", description="The response format"),
                    count: int = Query(10, description="Number of results to return"),
                   db: Session = Depends(get_db)
                   ):
    # Check if API key exists and is active
    db_key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.status == True).first()
    if not db_key:
        raise HTTPException(status_code=403, detail="Invalid or disabled API key")

    # Retrieve the user associated with the API key
    user = db.query(User).filter(User.id == db_key.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User associated with the API key not found")

    # Check if the user has the role 'customer'
    if user.role == "customer":
        # Count the number of queries made with this API key
        user_plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
        
        if not user_plan or user_plan.remain_request <= 0 or user_plan.plan_expire_date < datetime.now():
            if user_plan and user_plan.plan_expire_date < datetime.now():
                user_plan.plan_status = False
                user_plan.remain_request = 0
                user_plan.total_request = 0
                db.commit()
            return {"message": "You have exhausted your request quota or your plan has expired. Please upgrade your plan or wait for it to reset."}
        # Count the number of queries made with this API key
        # query_count = db.query(func.count(RequestLog.id)).filter(RequestLog.api_key == api_key).scalar()

        # # Check if the number of queries exceeds the free quota
        # if query_count >= 10:
        #     return {"message": "Your free quota is over. Please make a payment to continue using the service."}

        # Decrement the remaining requests by 1
        user_plan.remain_request -= 1
        db.commit()

    # Log the request
    log = RequestLog(api_key=api_key, query=query,model_id=None)
    db.add(log)
    db.commit()

    try:
        # Define the query parameters
        params = {
            "q": query,
            "categories": categories if categories else "general",  # Default to "general" if None
            "engines": engines if engines else "all",  # Default to "all" if None
            "count": count,
            "format": format if format else "json",  # Use provided format, default to "json"
        }

        # Send the GET request to SearxNG
        response = requests.get(SEARXNG_API_URL, params=params, timeout=1000)

        # Log response status and content
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response Content: {response.text}")

        # Check if the SearxNG API request was successful
        if response.status_code == 200:
            response_data = response.json()

            # Extract relevant result fields
            results = [
                {
                    "url": result.get("url"),
                    "title": result.get("title"),
                    "content": result.get("content"),
                    "score": result.get("score"),
                    "thumbnail": result.get("thumbnail"),
                    "category":result.get("category"),
                    "score":result.get("score"),
                }
                for result in response_data.get("results", [])
            ]
            limited_results = results[:count]
            # Return the filtered results and the number of results
            return {
                "followup": response_data.get("suggestions"),
                "category":response_data.get("category"),
                "query": query,
                "number_of_results": len(limited_results),
                "results": limited_results
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching data from Search API: {response.text}")

    except requests.RequestException as exc:
        # Handle any request errors, such as connection issues
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting SearxNG API: {exc}")

@router.get("/searchjson/")
def searchjson(
    q: str = Query(..., description="The search query"),
    categories: str = Query("general", description="The categories to filter by"),
    engines: str = Query("all", description="The engines to use"),
    format: str = Query("json", description="The response format")
):
    try:
        # Define the query parameters
        params = {
            "q": q,
            "categories": categories if categories else "general",  # Default to "general" if None
            "engines": engines if engines else "all",  # Default to "all" if None
            "format": format if format else "json",  # Use provided format, default to "json"
        }

        # Send the GET request to SearxNG
        response = requests.get(SEARXNG_API_URL, params=params, timeout=1000)

        # Log response status and content
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response Content: {response.text}")

        # Check if the SearxNG API request was successful
        if response.status_code == 200:
            return response.json()  # Return the JSON response from SearxNG API
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching data from SearxNG API: {response.text}")

    except requests.RequestException as exc:
        # Handle any request errors, such as connection issues
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting SearxNG API: {exc}")


















###not used


DSE_WEBSITES = [
    "https://www.dsebd.org",
    "https://www.amarstock.com",
    "https://www.dse.com.bd",
    "https://dsemonitor.com",
    "https://lankabd.com",
    "https://stocknow.com.bd",
    "https://tradingeconomics.com/bangladesh/stock-market"
    # "https://www.investing.com/indices/bd-dhaka-stock-exchange",
    
    # Add other reliable sources as necessary
]

@router.websocket("/ws/dse-updates")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time DSE updates.
    """
    await websocket.accept()
    try:
        timeout = httpx.Timeout(100.0, read=100.0)  # Set timeout to 100 seconds

        async with httpx.AsyncClient(timeout=timeout) as client:
            for website in DSE_WEBSITES:
                try:
                    # Initialize WebBaseLoader with the correct parameters
                    loader = WebBaseLoader()  # Initialize without url

                    # Load content from the URL directly
                    response = await client.get(website)
                    page_content = response.text

                    # Clean and process the content
                    cleaned_content = clean_whitespace(page_content)

                    # Summarize content
                    summary = summarize_content_dse(cleaned_content)
                    
                    # Send summary to client
                    await websocket.send_json({
                        "url": website,
                        "summary": summary
                    })

                except Exception as e:
                    logging.error(f"Error while loading {website}: {e}")
                    continue

                await asyncio.sleep(1)  # Adding delay to simulate real-time streaming

    except WebSocketDisconnect:
        logging.info("Client disconnected from WebSocket")
    except Exception as e:
        logging.error(f"Error during WebSocket communication: {e}")
    finally:
        await websocket.close()


# @router.get("/getlatestdseupdates")
# async def get_latest_dse_updates():
#     try:
#         # Increase timeout to 100 seconds
#         timeout = httpx.Timeout(100.0, read=100.0)

#         # Store data from all sources
#         url_contents = []

#         async with httpx.AsyncClient(timeout=timeout) as client:
#             for website in DSE_WEBSITES:
#                 try:
#                     # Use WebBaseLoader to load content from the URL
#                     loader = WebBaseLoader(website)
#                     docs = loader.load()

#                     # Clean and process the content
#                     page_content = docs[0].page_content
#                     cleaned_content = clean_whitespace(page_content)

#                     # Store the cleaned content with URL and title
#                     url_contents.append({
#                         "url": website,
#                         "content": cleaned_content
#                     })

#                 except httpx.RequestError as e:
#                     logging.error(f"Request Error for {website}: {e}")
#                     continue
#                 except Exception as e:
#                     logging.error(f"Error while loading {website}: {e}")
#                     continue

#         # Summarize content for each website
#         summaries = []
#         for item in url_contents:
#             url = item["url"]
#             content = item["content"]
#             summary = summarize_content_dse(content)
#             summaries.append({"url": url, "summary": summary})

#         return {"summaries": summaries}  # Return the summarized content

#     except httpx.RequestError as exc:
#         # Handle any request errors
#         raise HTTPException(status_code=500, detail=f"An error occurred while fetching data: {exc}")




def clean_whitespace(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()




def summarize_content_dse(content: str) -> str:
    try:
        chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"Please note that the current date and time is: {get_current_date_and_time}. I will provide a summary and analysis of the main points and update data of Dhaka Stock Exchange as an expert."
            },
            {
                "role": "user",
                "content": f"Please summarize the content with 3 line and top will be date of that contents . The content is: {content}"
            }
        ],
        model="llama-3.1-70b-versatile",
)
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return ''
