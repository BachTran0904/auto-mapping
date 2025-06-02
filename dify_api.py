import io, os, sys, json, requests
from dotenv import load_dotenv, dotenv_values

load_dotenv()

# Retrieve the Bearer token from the environment variable
BEARER_TOKEN = os.getenv("API_SECRET_KEY")
API_URL = os.getenv("API_URL")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_answer_from_dify(headers: str, title: str):
    headers_str = ", ".join(headers)
    prompt = "prompt.yaml"
    query = f"""

    Objective:
    Map each provided term to the most appropriate attribute and corresponding category using the `mapping_data.txt` knowledge base, by following the steps below.

    Mapping Attributes to Categories — Enhanced Instructions

    For each term in the provided list ({headers_str}), follow these steps:

    Step-by-Step Process:
    1. Attribute Mapping:
    If the finding attribute with its corresponding category has already been mapped for a previous term, then for any subsequent terms that could also map to this same attribute, skip them and do not map again.

    Search through the mapping_data.txt knowledge base chunk by chunk.

    Identify the most correct attribute for the given term with a confidence level over 0.7.

    If no suitable attribute is found, respond with:

    "I cannot find a suitable attribute."

    2. Category Mapping:

    Once an attribute is identified, find the most appropriate main category from the same chunk.

    The attribute and category must co-exist in the same chunk to be considered a valid pair.

    3. Verification by Chunk:

    For each term, fully verify the current chunk before moving on to the next.

    Make sure that the attribute-category is found within the same chunk, if the pair is not in the same chunk. It is invalid, and need to be redo.

    If no valid attribute-category pair is found in the current chunk, proceed to the next chunk.

    Repeat this process until a valid pair is found or all chunks are exhausted.

    4. Final Check:

    If after checking all chunks, no valid attribute-category pair is found, respond with:

    "I cannot find a suitable pair."

    5. Exception:

    If the pair `Hàng hóa: Mã hàng` is found during mapping:

    Only output this specific pair instead: Quy cách hàng hóa: Mã hàng hóa: <original term>, and Hàng hóa: Mã hàng: <original term>.

    
    Ignore and override any other logic for this exception.

    6. Output Format:
    For each term, output only the first valid attribute-category pair found, in this exact, and only format:

    category: attribute: original attribute: {title}

    adding {title} at the end of the line, where {title} is the name of the sheet.

    If no pair is found, output the corresponding message exactly as above.    
    """


    payload = {
        "inputs": {},  # Add the inputs field (it can be an empty dictionary if not needed)
        "query": query,
        "response_mode": "streaming",
        "conversation_id": "",  # Empty string if not needed
        "user": "Bách Trần",  # Correct user identifier
        "files": [
            {
                "type": "image",
                "transfer_method": "remote_url",
                "url": "https://cloud.dify.ai/logo/logo-site.png"  # Example URL
            }
        ]
    }

    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
    
    # Extract the answer tokens from the response and combine them
    response_data = response.text.split('data: ')[1:]  # Split the data blocks based on 'data: '
    answer_tokens = []

    # Iterate over the response data and collect the 'answer' field
    for data in response_data:
        try:
            json_data = json.loads(data)  # Convert each data block to JSON
            if 'answer' in json_data:
                answer_tokens.append(json_data['answer'])  # Append the 'answer' token
        except json.JSONDecodeError:
            continue
    

    # Combine the tokens to form the full answer
    full_answer = ''.join(answer_tokens)

    return full_answer
