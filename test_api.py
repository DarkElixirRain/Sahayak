import sys
import time
import requests
import json
import subprocess
import os
from urllib.parse import urlparse

# We'll start the server in a subprocess
def start_server():
    # Change to the backend directory
    os.chdir("/Users/bishalchaudhary/Sahayak/backend")
    # Start the server
    # We'll use uvicorn to run the app
    # We'll use the same port as in the .env or default to 8000
    # We'll read the port from the .env if available, else default to 8000
    env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
    port = 8000
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('PORT='):
                    port = line.split('=')[1].strip()
                    break
    # Start the server
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(port)]
    print(f"Starting server with command: {' '.join(cmd)}")
    # We'll use subprocess.Popen to start the server in the background
    server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Wait a bit for the server to start
    time.sleep(3)
    # Check if the server is still running
    if server_process.poll() is not None:
        # Server has exited, check the error
        stdout, stderr = server_process.communicate()
        print(f"Server exited early. Stdout early. Stdout: {stdout.decode()}")
        print(f"Stderr: {stderr.decode()}")
        raise RuntimeError("Server failed to start")
    return server_process, port

def wait_for_server(port, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://localhost:{port}/")
            if response.status_code < 500:
                print("Server is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    raise TimeoutError("Server did not start within the timeout period")

def send_message(session_id, message, port):
    url = f"http://localhost:{port}/api/conversations/{session_id}/messages"
    payload = {"message": message}
    print(f"Sending message to {url}: {payload}")
    response = requests.post(url, json=payload)
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    return response.json()

def main():
    # Start the server
    server_process, port = start_server()
    try:
        # Wait for the server to be ready
        wait_for_server(port)
        print("Server is ready. Starting test...")

        # We'll use a fixed session ID for simplicity, but note that the tests use random ones.
        # We'll generate a random session ID for this test.
        import uuid
        session_id = str(uuid.uuid4())
        print(f"Using session ID: {session_id}")

        # Define the user journey
        turns = [
            "Malai mudda halyo, aba maile ke garne?",
            "मेरो भाइले हालेको हो।",
            "सम्पत्तिको विषयमा हो।",
            "जिल्ला अदालतबाट notice आएको छ।",
            "मलाई notice मा १५ दिनभित्र जवाफ दिन भनिएको छ।",
            "म काठमाडौंमा छु।"
        ]

        # We'll store the responses to verify later
        responses = []

        for i, turn in enumerate(turns, 1):
            print(f"\n--- Turn {i} ---")
            print(f"User: {turn}")
            resp = send_message(session_id, turn, port)
            responses.append(resp)
            # We can add a small delay between turns if needed
            time.sleep(1)

        # After the six turns, we can inspect the case context by querying the database?
        # But we don't have direct access to the database from here.
        # Instead, we can check the conversation history via the GET endpoint.
        print("\n--- Fetching conversation history ---")
        history_url = f"http://localhost:{port}/api/conversations/{session_id}"
        history_resp = requests.get(history_url)
        print(f"History response status: {history_resp.status_code}")
        if history_resp.status_code == 200:
            history = history_resp.json()
            print(f"History: {json.dumps(history, indent=2)}")
        else:
            print(f"Failed to get history: {history_resp.text}")

        # We can also try to get the case context from the conversation service? Not directly exposed.
        # We'll rely on the history to see what was stored.

        # Now, we can try to ask a simple legal question to see if we get a grounded answer.
        print("\n--- Testing a simple legal question ---")
        simple_session_id = str(uuid.uuid4())
        simple_question = "नेपालको संविधान कहिले जारी भयो?"
        print(f"User: {simple_question}")
        simple_resp = send_message(simple_session_id, simple_question, port)
        print(f"Response: {json.dumps(simple_resp, indent=2)}")

        # Test a legal but underspecified question
        print("\n--- Testing a legal but underspecified question ---")
        underspec_session_id = str(uuid.uuid4())
        underspec_question = "मलाई अदालतबाट notice आएको छ, अब के गर्ने?"
        print(f"User: {underspec_question}")
        underspec_resp = send_message(underspec_session_id, underspec_question, port)
        print(f"Response: {json.dumps(underspec_resp, indent=2)}")

        # Test Romanized Nepali
        print("\n--- Testing Romanized Nepali ---")
        roman_session_id = str(uuid.uuid4())
        roman_turns = [
            "Malai mudda halyo aba maile ke garne?",
            "Mero bhai le malai mudda haleko ho.",
            "Sampatti ko bisaya ho.",
            "Jilla adalat bata notice aayo.",
            "15 din bhitra jawab dinu parne raicha."
        ]
        for i, turn in enumerate(roman_turns, 1):
            print(f"\n--- Roman Turn {i} ---")
            print(f"User: {turn}")
            roman_resp = send_message(roman_session_id, turn, port)
            print(f"Response: {json.dumps(roman_resp, indent=2)}")
            time.sleep(1)

        # After the Romanized turns, we can check the history
        print("\n--- Fetching Romanized conversation history ---")
        roman_history_url = f"http://localhost:{port}/api/conversations/{roman_session_id}"
        roman_history_resp = requests.get(roman_history_url)
        if roman_history_resp.status_code == 200:
            roman_history = roman_history_resp.json()
            print(f"Romanized History: {json.dumps(roman_history, indent=2)}")
        else:
            print(f"Failed to get Romanized history: {roman_history_resp.text}")

        # Test mixed language
        print("\n--- Testing mixed language ---")
        mixed_session_id = str(uuid.uuid4())
        mixed_question = "Mero bhai le property ko case haleko ho ani district court bata notice aayo."
        print(f"User: {mixed_question}")
        mixed_resp = send_message(mixed_session_id, mixed_question, port)
        print(f"Response: {json.dumps(mixed_resp, indent=2)}")

        # Test English
        print("\n--- Testing English ---")
        english_session_id = str(uuid.uuid4())
        english_question = "Someone filed a property case against me and I received a notice from the district court. What should I do?"
        print(f"User: {english_question}")
        english_resp = send_message(english_session_id, english_question, port)
        print(f"Response: {json.dumps(english_resp, indent=2)}")

        # Test urgency
        print("\n--- Testing urgency ---")
        urgency_session_id = str(uuid.uuid4())
        urgency_question = "मलाई अदालतको notice आएको छ र २ दिनभित्र जवाफ दिन भनिएको छ।"
        print(f"User: {urgency_question}")
        urgency_resp = send_message(urgency_session_id, urgency_question, port)
        print(f"Response: {json.dumps(urgency_resp, indent=2)}")

        # Test document awareness
        print("\n--- Testing document awareness ---")
        doc_session_id = str(uuid.uuid4())
        doc_question = "मसँग अदालतको notice छ।"
        print(f"User: {doc_question}")
        doc_resp = send_message(doc_session_id, doc_question, port)
        print(f"Response: {json.dumps(doc_resp, indent=2)}")

        # Test no hallucination: ask a question for which the verified corpus has no relevant provision
        # We don't know what's in the corpus, but we can try a random question.
        print("\n--- Testing no hallucination (random question) ---")
        nohall_session_id = str(uuid.uuid4())
        nohall_question = "What is the weather like on Mars?"
        print(f"User: {nohall_question}")
        nohall_resp = send_message(nohall_session_id, nohall_question, port)
        print(f"Response: {json.dumps(nohall_resp, indent=2)}")

        # Finally, we can try to get the server status
        print("\n--- Testing server status ---")
        status_resp = requests.get(f"http://localhost:{port}/")
        print(f"Status response: {status_resp.text}")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop the server
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped.")

if __name__ == "__main__":
    main()