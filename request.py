import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def call_gemma(prompt):
    start = time.time()
    res = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('TEMP_API_KEY')}",
            "Content-Type": "application/json"
        },
        json = {
            "model": "google/gemma-4-26b-a4b-it:free",
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    latency = time.time()-start
    
    # Check for errors
    if res.status_code != 200:
        error_data = res.json()
        print(f"❌ Gemma - Error {res.status_code}: {error_data}")
        raise Exception(f"API Error: {error_data}")
    
    data = res.json()
    if "choices" not in data:
        print(f"❌ Unexpected response: {data}")
        raise Exception(f"No choices in response: {data}")
    
    output = data["choices"][0]["message"]["content"]
    return output, latency, 0


def main():
    # Check if API key is set
    if not os.getenv('TEMP_API_KEY'):
        print("ERROR: TEMP_API_KEY environment variable is not set!")
        print("Please set your OpenRouter API key:")
        return
    
    prompt = "How many 'r's in straberryberryberry"
    print(call_gemma(prompt))

if __name__ == "__main__":
    main()
import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def call_gemma(prompt):
    start = time.time()
    res = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('TEMP_API_KEY')}",
            "Content-Type": "application/json"
        },
        json = {
            "model": "google/gemma-4-26b-a4b-it:free",
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    latency = time.time()-start
    
    # Check for errors
    if res.status_code != 200:
        error_data = res.json()
        print(f"❌ Gemma - Error {res.status_code}: {error_data}")
        raise Exception(f"API Error: {error_data}")
    
    data = res.json()
    if "choices" not in data:
        print(f"❌ Unexpected response: {data}")
        raise Exception(f"No choices in response: {data}")
    
    output = data["choices"][0]["message"]["content"]
    return output, latency, 0


# def call_llama(prompt):
#     start = time.time()
#     res = requests.post(
#         url="https://openrouter.ai/api/v1/chat/completions",
#         headers={
#             "Authorization": f"Bearer {os.getenv('TEMP_API_KEY')}",
#             "Content-Type": "application/json"
#         },
#         json = {
#             "model": "meta-llama/llama-3.3-70b-instruct:free",
#             "messages": [{"role": "user", "content": prompt}],
#         },
#     )
#     latency = time.time()-start
    
#     # Check for errors
#     if res.status_code != 200:
#         error_data = res.json()
#         if res.status_code == 429:
#             error_msg = error_data.get('error', {}).get('metadata', {}).get('raw', 'Rate limited')
#             print(f"❌ Llama - Rate Limited: {error_msg}")
#         else:
#             print(f"❌ Llama - Error {res.status_code}: {error_data}")
#         raise Exception(f"API Error: {error_data}")
    
#     data = res.json()
#     if "choices" not in data:
#         print(f"❌ Unexpected response: {data}")
#         raise Exception(f"No choices in response: {data}")
    
#     output = data["choices"][0]["message"]["content"]
#     return output, latency, 0


# def call_nemotron(prompt):
#     start = time.time()
#     res = requests.post(
#         url="https://openrouter.ai/api/v1/chat/completions",
#         headers={
#             "Authorization": f"Bearer {os.getenv('TEMP_API_KEY')}",
#             "Content-Type": "application/json"
#         },
#         json = {
#             "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
#             "messages": [{"role": "user", "content": prompt}],
#         },
#     )
#     latency = time.time()-start
    
#     # Check for errors
#     if res.status_code != 200:
#         error_data = res.json()
#         if res.status_code == 429:
#             error_msg = error_data.get('error', {}).get('metadata', {}).get('raw', 'Rate limited')
#             print(f"❌ Nemotron - Rate Limited: {error_msg}")
#         else:
#             print(f"❌ Nemotron - Error {res.status_code}: {error_data}")
#         raise Exception(f"API Error: {error_data}")
    
#     data = res.json()
#     if "choices" not in data:
#         print(f"❌ Unexpected response: {data}")
#         raise Exception(f"No choices in response: {data}")
    
#     output = data["choices"][0]["message"]["content"]
#     return output, latency, 0


def main():
    # Check if API key is set
    if not os.getenv('TEMP_API_KEY'):
        print("ERROR: TEMP_API_KEY environment variable is not set!")
        print("Please set your OpenRouter API key:")
        return
    
    prompt = "How many 'r's in straberryberryberry"
    print(call_gemma(prompt))
    # print(call_llama(prompt))
    # print(call_nemotron(prompt))

if __name__ == "__main__":
    main()
