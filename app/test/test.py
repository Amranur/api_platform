import json
import requests
import base64

with open('D:/Imran Nur/api_platform-backend/app/test/chat.jpg', 'rb') as image_file:
    image_data = image_file.read()

encoded_image_data = base64.b64encode(image_data).decode('utf-8')

url = 'http://36.50.40.36:11435/api/chat'
headers = {
    'Content-Type': 'application/json'
}
payload = {
    "model": "llama3.2-vision:11b-instruct-q4_K_M",
    "messages": [
        {"role": "system", "content": "You are an assistant designed to provide helpful responses.Always try to generate full code for the given image"},
        {
            "role": "user",
            "content": " continue where you stop to full the code",
            "images": [encoded_image_data]
        }
    ]
}

try:
   
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  
    
    response_content = response.content.decode('utf-8')
   
    json_objects = response_content.split('\n')
    for json_object in json_objects:
        if json_object:  
            data = json.loads(json_object)
            text = data["message"]["content"]
            print(text,end=" ")
except requests.exceptions.ConnectionError as e:
    print(f"Connection error: {e}")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")








def call_llm_api(messages):
    url = "http://36.50.40.36/api/chat"
    data = {
        "model": "llama3.2:latest",
        "messages": messages,
        "stream": True 
    }

    response = requests.post(url, json=data, stream=True)
    if response.status_code == 200:
        print("Streaming output:")
        
        # Process each line in the response as it arrives
        for line in response.iter_lines():
            if line:  # Ensure line is not empty
                try:
                    # Parse each line as JSON
                    json_line = json.loads(line.decode('utf-8'))  # Decode bytes to string
                    # Extract and print the content if it exists
                    if 'message' in json_line and 'content' in json_line['message']:
                        print(json_line['message']['content'], end=' ', flush=True)  # Flush to ensure immediate output
                except json.JSONDecodeError:
                    print("Failed to decode JSON:", line)
    else:
        print("Error:", response.status_code, response.text)

messages = [
    
        {"role": "system", "content": "You are an assistant designed to provide helpful responses."},
        {"role": "user", "content": f"to do"}
    ]


# Call the Ollama API and get the response
# response_text = call_llm_api(messages)