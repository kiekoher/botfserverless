import os
import time
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
import logging

# --- Configuration ---
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from a .env file for local testing
load_dotenv()

# Get configuration from environment
MAIN_API_URL = os.getenv("MAIN_API_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Test parameters
TEST_TIMEOUT = 30  # seconds to wait for API processing

def run_e2e_test():
    """
    Runs an end-to-end test against the main API.
    1.  Checks for required environment variables.
    2.  Creates a unique test user identifier.
    3.  Sends a test message payload to the main API.
    4.  Verifies the API response.
    5.  Polls the database to verify the message was processed and stored.
    6.  Cleans up created test data.
    """
    logging.info("--- Starting End-to-End Test ---")

    # 1. Pre-flight checks for configuration
    if not all([MAIN_API_URL, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
        logging.error("❌ Missing one or more required environment variables: MAIN_API_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        exit(1)

    logging.info(f"Target API URL: {MAIN_API_URL}")
    logging.info(f"Target Supabase URL: {SUPABASE_URL}")

    # Initialize Supabase client with service role key for admin-level access
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logging.info("✅ Connected to Supabase successfully.")
    except Exception as e:
        logging.error(f"❌ Could not connect to Supabase: {e}")
        exit(1)

    # 2. Create unique test data
    test_id = str(uuid.uuid4())
    # Use a unique phone number format for easy identification and cleanup
    test_user_phone = f"+1555000{test_id[:4]}"
    test_message_body = f"E2E test message {test_id}"

    logging.info(f"Test User Phone: {test_user_phone}")
    logging.info(f"Test Message: '{test_message_body}'")

    # 3. Send test message to the API
    message_payload = {
        "userId": test_user_phone,
        "userName": f"E2E Test User {test_id[:4]}",
        "chatId": test_user_phone,
        "timestamp": str(int(time.time())),
        "agentId": "default", # API should handle this
        "body": test_message_body,
        "mediaKey": "",
        "mediaType": ""
    }

    try:
        logging.info(f"POSTing message payload to {MAIN_API_URL}...")
        response = httpx.post(MAIN_API_URL, json=message_payload, timeout=20.0)

        # 4. Verify API response
        # The API might respond with 200 OK or 202 Accepted if processing is async
        if response.status_code not in [200, 202]:
            logging.error(f"❌ API returned non-success status code: {response.status_code}")
            logging.error(f"Response body: {response.text}")
            exit(1)

        logging.info(f"✅ API returned success status: {response.status_code}")

    except httpx.RequestError as e:
        logging.error(f"❌ HTTP request to API failed: {e}")
        exit(1)

    # 5. Poll database to verify message processing
    logging.info("Verifying data in Supabase...")
    start_time = time.time()
    test_user_uuid = None
    verification_passed = False

    while time.time() - start_time < TEST_TIMEOUT:
        try:
            # First, find the user UUID created by the API
            if not test_user_uuid:
                user_res = supabase.table("users").select("id").eq("phone", test_user_phone).execute()
                if user_res.data:
                    test_user_uuid = user_res.data[0]['id']
                    logging.info(f"✅ Found created user in DB with UUID: {test_user_uuid}")

            # If user is found, check for the conversation
            if test_user_uuid:
                convo_res = supabase.table("conversations").select("user_message").eq("user_id", test_user_uuid).execute()
                for convo in convo_res.data:
                    if convo['user_message'] == test_message_body:
                        logging.info("✅ Verification successful: Found matching message in 'conversations' table.")
                        verification_passed = True
                        break

            if verification_passed:
                break

        except Exception as e:
            logging.warning(f"DB verification check failed with error, retrying... Error: {e}")

        time.sleep(2) # Wait before retrying

    # 6. Cleanup
    if test_user_uuid:
        try:
            logging.info(f"Cleaning up test user: {test_user_uuid}")
            # Deleting a user in auth.users should cascade and delete their conversations
            supabase.auth.admin.delete_user(test_user_uuid)
            logging.info("✅ Cleanup successful.")
        except Exception as e:
            logging.error(f"⚠️ Failed to clean up test user. Manual cleanup may be required. Error: {e}")

    # Final result
    if verification_passed:
        logging.info("--- ✅ End-to-End Test Passed ---")
        exit(0)
    else:
        logging.error(f"❌ Test failed. Verification timed out after {TEST_TIMEOUT} seconds.")
        logging.error("--- ❌ End-to-End Test Failed ---")
        exit(1)


if __name__ == "__main__":
    run_e2e_test()
