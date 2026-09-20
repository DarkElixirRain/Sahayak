import requests
import json
import uuid

chat_id = str(uuid.uuid4())
base_url = "http://localhost:8000/query"

prompts = [
    "मेरो भाइले मलाई मुद्दा हाल्यो।",
    "जग्गाको विषयमा हो।",
    "अदालतबाट म्याद पनि आएको छ।",
    "अब मैले के गर्नुपर्छ?"
]

for prompt in prompts:
    print(f"\nQ: {prompt}")
    resp = requests.post(
        base_url, 
        json={"query": prompt, "chat_id": chat_id}
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"A: {data.get('completion', '')[:200]}...")
        print(f"Sources: {len(data.get('sources', []))}")
    else:
        print(f"Error: {resp.status_code}")

