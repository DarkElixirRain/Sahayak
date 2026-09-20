import requests
import json
import sys
import time

base_url = "http://localhost:8000/query"
queries = [
    "मेरो भाइले मलाई मुद्दा हाल्यो।",
    "mero bhai le malai mudda halyo aba ke garne?"
]

success = True
for query in queries:
    print(f"\n======================================")
    print(f"QUERY: {query}")
    print(f"======================================")
    
    payload = {
        "query": query,
        "k": 5,
        "stream_response": False
    }
    
    try:
        resp = requests.post(base_url, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            if 'text' in data:
                answer = data['text']
                sources = data.get('sources', [])
                
                print(f"ANSWER:\n{answer[:500]}...\n")
                print(f"SOURCES ({len(sources)}):")
                for i, s in enumerate(sources):
                    print(f"  [{i+1}] {s.get('document_id')} / {s.get('chunk_number')} / Score: {s.get('score')}")
                    
                if len(sources) == 0:
                    print("FAIL: No sources retrieved for this query!")
            else:
                print("Unexpected format:", data)
                success = False
        else:
            print(f"HTTP Error {resp.status_code}: {resp.text}")
            success = False
    except Exception as e:
        print(f"Exception: {e}")
        success = False
        
    time.sleep(5)

if not success:
    sys.exit(1)
