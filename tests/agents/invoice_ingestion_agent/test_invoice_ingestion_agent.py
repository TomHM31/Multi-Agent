import os
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# Adjust the import path based on your project structure
# This assumes your tests are run from the root of the project
from agents.invoice_ingestion_agent import invoice_ingestion_agent
from agents.invoice_ingestion_agent import s3_ingester
from agents.invoice_ingestion_agent import db_ingester
from agents.invoice_ingestion_agent import email_ingester

# --- Fixtures ---

@pytest.fixture(autouse=True)
def setup_env_vars(monkeypatch):
    """Mock environment variables for tests."""
    monkeypatch.setenv("S3_BUCKET_RAW", "test-s3-bucket")
    monkeypatch.setenv("DB_CONNECTION_STRING", "test-db-string")
    monkeypatch.setenv("IMAP_HOST", "test-imap-host")
    monkeypatch.setenv("IMAP_USER", "test-imap-user")
    monkeypatch.setenv("IMAP_PASSWORD", "test-imap-password")
    monkeypatch.setenv("PREPROCESS_QUEUE_URL", "test-queue-url")
    monkeypatch.setenv("STATE_STORE_PATH", "test_state_store.json")
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "1") # Short poll interval for tests

@pytest.fixture
def state_file_path():
    """Returns the configured state store path for cleanup."""
    return invoice_ingestion_agent.STATE_STORE_PATH

@pytest.fixture(autouse=True)
def cleanup_state_file(state_file_path):
    """Ensure state file is removed before and after each test."""
    if os.path.exists(state_file_path):
        os.remove(state_file_path)
    yield
    if os.path.exists(state_file_path):
        os.remove(state_file_path)

# --- Test State Management ---

def test_load_state_file_not_exists(state_file_path):
    """
    Tests load_state when the state file does not exist.
    Expected: Returns an empty dictionary.
    """
    assert not os.path.exists(state_file_path)
    state = invoice_ingestion_agent.load_state()
    assert state == {}

def test_load_state_file_exists_valid_json(state_file_path):
    """
    Tests load_state when the state file exists with valid JSON.
    Expected: Returns the loaded dictionary.
    """
    expected_state = {"item1": "timestamp1"}
    with open(state_file_path, 'w') as f:
        json.dump(expected_state, f)
    state = invoice_ingestion_agent.load_state()
    assert state == expected_state

def test_load_state_file_exists_invalid_json(state_file_path, mock_logger_main_agent):
    """
    Tests load_state when the state file exists but contains invalid JSON.
    Expected: Logs an error and returns an empty dictionary.
    """
    with open(state_file_path, 'w') as f:
        f.write("this is not json")
    state = invoice_ingestion_agent.load_state()
    assert state == {}
    mock_logger_main_agent.error.assert_called_once_with(f"Error decoding JSON from state file: {state_file_path}")

def test_save_state(state_file_path):
    """
    Tests save_state correctly writes to the file.
    Expected: File contains the JSON representation of the state.
    """
    state_to_save = {"item2": "timestamp2"}
    invoice_ingestion_agent.save_state(state_to_save)
    assert os.path.exists(state_file_path)
    with open(state_file_path, 'r') as f:
        loaded_state = json.load(f)
    assert loaded_state == state_to_save

def test_mark_as_processed_and_has_been_processed(state_file_path):
    """
    Tests marking an item as processed and checking its status.
    Expected: Item is marked, and has_been_processed returns True.
    """
    initial_state = {}
    invoice_ingestion_agent.save_state(initial_state) # Start with empty state file

    item_id = "test_item_123"
    assert not invoice_ingestion_agent.has_been_processed(initial_state, item_id)

    current_state = invoice_ingestion_agent.load_state()
    invoice_ingestion_agent.mark_as_processed(current_state, item_id)

    # Verify it's saved to file
    with open(state_file_path, 'r') as f:
        saved_state_on_disk = json.load(f)
    assert item_id in saved_state_on_disk
    assert datetime.fromisoformat(saved_state_on_disk[item_id])

    # Verify in-memory state and has_been_processed
    reloaded_state = invoice_ingestion_agent.load_state()
    assert invoice_ingestion_agent.has_been_processed(reloaded_state, item_id)


# --- Test Queue Publishing (Placeholder) ---

@patch.object(invoice_ingestion_agent, 'logger') # Mock logger inside publish_to_queue
def test_publish_to_queue_logs_message(mock_publish_logger):
    """
    Tests that publish_to_queue logs the message (as it's a placeholder).
    Expected: Logger is called with info about publishing.
    """
    test_message = {"data": "test_payload"}
    invoice_ingestion_agent.publish_to_queue(test_message)
    mock_publish_logger.info.assert_called_with(
        f"Publishing to queue {invoice_ingestion_agent.PREPROCESS_QUEUE_URL}: {test_message}"
    )

# --- Test Ingestion Functions (Placeholders - to be expanded with mocks for boto3, db, imap) ---

# Fixture for mocking the main agent's logger for state management tests
@pytest.fixture
def mock_logger_main_agent():
    """Fixture to mock the logger in the main invoice_ingestion_agent module."""
    with patch.object(invoice_ingestion_agent, 'logger') as mock_log:
        yield mock_log

@patch.object(invoice_ingestion_agent, 'load_state', return_value={})
@patch.object(invoice_ingestion_agent, 'publish_to_queue')
@patch('agents.invoice_ingestion_agent.s3_ingester.os.makedirs') # Mock os.makedirs in s3_ingester
@patch.object(s3_ingester, 'logger') # Mock logger in s3_ingester
def test_ingest_from_s3_placeholder(mock_logger_s3, mock_makedirs, mock_publish, mock_load_state):
    """
    Placeholder test for S3 ingestion.
    Expected: Logs start and finish messages.
    """
    s3_ingester.ingest_from_s3()
    mock_logger_s3.info.assert_any_call("Starting S3 ingestion...")
    mock_logger_s3.info.assert_any_call("S3 ingestion finished (Placeholder).")
    mock_publish.assert_not_called()


@patch.object(invoice_ingestion_agent, 'load_state', return_value={})
@patch.object(invoice_ingestion_agent, 'publish_to_queue')
@patch('agents.invoice_ingestion_agent.db_ingester.os.makedirs') # Mock os.makedirs in db_ingester
@patch.object(db_ingester, 'logger') # Mock logger in db_ingester
def test_ingest_from_db_placeholder(mock_logger_db, mock_makedirs, mock_publish, mock_load_state):
    """
    Placeholder test for DB ingestion.
    Expected: Logs start and finish messages.
    """
    db_ingester.ingest_from_db()
    mock_logger_db.info.assert_any_call("Starting DB ingestion...")
    mock_logger_db.info.assert_any_call("DB ingestion finished (Placeholder).")
    mock_publish.assert_not_called()


@patch.object(invoice_ingestion_agent, 'load_state', return_value={})
@patch.object(invoice_ingestion_agent, 'publish_to_queue')
@patch('agents.invoice_ingestion_agent.email_ingester.os.makedirs') # Mock os.makedirs in email_ingester
@patch.object(email_ingester, 'logger') # Mock logger in email_ingester
def test_ingest_from_email_placeholder(mock_logger_email, mock_makedirs, mock_publish, mock_load_state):
    """
    Placeholder test for Email ingestion.
    Expected: Logs start and finish messages.
    """
    email_ingester.ingest_from_email()
    mock_logger_email.info.assert_any_call("Starting Email ingestion...")
    mock_logger_email.info.assert_any_call("Email ingestion finished (Placeholder).")
    mock_publish.assert_not_called()

# --- Test Main Loop (Simplified) ---

@patch.object(invoice_ingestion_agent, 'ingest_from_s3')
@patch.object(invoice_ingestion_agent, 'ingest_from_db')
@patch.object(invoice_ingestion_agent, 'ingest_from_email')
@patch.object(invoice_ingestion_agent, 'time') # Mock time.sleep
@patch('agents.invoice_ingestion_agent.invoice_ingestion_agent.os.makedirs')
@patch.object(invoice_ingestion_agent, 'logger') # Mock logger in main_loop
def test_main_loop_calls_ingestion_functions_and_sleeps(
    mock_logger_main_loop, mock_makedirs, mock_time, mock_email, mock_db, mock_s3
):
    """
    Tests that the main loop calls ingestion functions and sleeps.
    It will run one iteration and then raise KeyboardInterrupt to stop.
    """
    # Make one of the ingestion functions raise KeyboardInterrupt to stop the loop after one iteration
    mock_s3.side_effect = KeyboardInterrupt("Stopping loop for test")

    with pytest.raises(KeyboardInterrupt, match="Stopping loop for test"):
        invoice_ingestion_agent.main_loop()

    mock_logger_main_loop.info.assert_any_call("Invoice Ingestion Agent started.")
    mock_logger_main_loop.info.assert_any_call("Starting new ingestion cycle...")
    mock_s3.assert_called_once()
    # Because mock_s3 raises KeyboardInterrupt, db and email might not be called if the try/except
    # for KeyboardInterrupt is outside the while True loop in the agent.
    # If the agent's main_loop is robust to KeyboardInterrupt inside the loop,
    # then these might be called. Given the current agent code, they won't be.
    # mock_db.assert_called_once()
    # mock_email.assert_called_once()

    # Check if the "Invoice Ingestion Agent stopped by user." is logged
    # This depends on where the KeyboardInterrupt is caught in the agent's main function.
    # For this test, we assume it's caught by the `if __name__ == "__main__":` block.

    # Check if os.makedirs("raw/", exist_ok=True) was called
    mock_makedirs.assert_called_with("raw/", exist_ok=True)


# TODO: Add more comprehensive tests for each ingestion function by mocking:
# 1. S3 client (boto3) and its responses (list_objects_v2, download_file)
# 2. Database client (sqlalchemy/psycopg2) and its responses (execute for SELECT, UPDATE)
# 3. IMAP client (imaplib) and its responses (login, select, search, fetch, store)
# 4. File system operations (open, os.path.exists, os.makedirs) where necessary.
# 5. Test error handling and dead-letter queue/file logic.
# 6. Test metrics incrementing correctly.
