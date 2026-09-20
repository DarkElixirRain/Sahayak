import requests
import json

base_url = "http://localhost:8000/retrieve/chunks"
query = "मेरो भाइले मलाई मुद्दा हाल्यो।"
resp = requests.post(base_url, json={"query": query})
if resp.status_code == 200:
    data = resp.json()
    print(f"Retrieved Chunks: {len(data)}")
    for i, chunk in enumerate(data[:1]):
        print(json.dumps(chunk, indent=2))
else:
    print(f"Error: {resp.status_code} - {resp.text}")

