import os
import time
import logging
import json
from datetime import datetime

# --- Configuration (from env vars or config file) ---
S3_BUCKET_RAW = os.getenv("S3_BUCKET_RAW", "your-s3-bucket-raw")
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "your-db-connection-string")
IMAP_HOST = os.getenv("IMAP_HOST", "your-imap-host")
IMAP_USER = os.getenv("IMAP_USER", "your-imap-user")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "your-imap-password")
PREPROCESS_QUEUE_URL = os.getenv("PREPROCESS_QUEUE_URL", "your-preprocess-queue-url") # e.g., Redis, SQS
STATE_STORE_PATH = os.getenv("STATE_STORE_PATH", "state_store.json") # Local file to track processed items
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300")) # Default to 5 minutes

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Metrics ---
metrics = {
    "s3_processed": 0,
    "db_processed": 0,
    "emails_processed": 0,
    "ingestion_errors": 0,
}

# --- State Management ---
def load_state():
    """Loads the state from the STATE_STORE_PATH."""
    if os.path.exists(STATE_STORE_PATH):
        try:
            with open(STATE_STORE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from state file: {STATE_STORE_PATH}")
            return {} # Return empty state if file is corrupted
    return {}

def save_state(state):
    """Saves the state to the STATE_STORE_PATH."""
    try:
        with open(STATE_STORE_PATH, 'w') as f:
            json.dump(state, f, indent=4)
    except IOError:
        logger.error(f"Could not write to state file: {STATE_STORE_PATH}")

def mark_as_processed(state, item_id):
    """Marks an item as processed in the state."""
    state[item_id] = datetime.now().isoformat()
    save_state(state)

def has_been_processed(state, item_id):
    """Checks if an item has already been processed."""
    return item_id in state

# --- Queue Client (Placeholder - to be implemented based on chosen queue) ---
def publish_to_queue(message):
    """
    Publishes a message to the PREPROCESS_QUEUE_URL.
    This is a placeholder and needs to be implemented based on the queue system (Redis, SQS, RabbitMQ).
    """
    # Example for logging, replace with actual queue publishing logic
    logger.info(f"Publishing to queue {PREPROCESS_QUEUE_URL}: {message}")
    # For SQS (boto3):
    # import boto3
    # sqs = boto3.client('sqs')
    # sqs.send_message(QueueUrl=PREPROCESS_QUEUE_URL, MessageBody=json.dumps(message))

    # For Redis (redis-py):
    # import redis
    # r = redis.Redis(host='localhost', port=6379, db=0) # Update with actual connection
    # r.rpush(PREPROCESS_QUEUE_URL, json.dumps(message)) # Assuming PREPROCESS_QUEUE_URL is the queue name

    # For RabbitMQ (pika):
    # import pika
    # connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost')) # Update
    # channel = connection.channel()
    # channel.queue_declare(queue=PREPROCESS_QUEUE_URL)
    # channel.basic_publish(exchange='', routing_key=PREPROCESS_QUEUE_URL, body=json.dumps(message))
    # connection.close()
    pass

# --- Import Ingestion Modules ---
# These are imported here so they can access the shared components like logger, metrics, etc.
# defined in this main agent file.
from .s3_ingester import ingest_from_s3
from .db_ingester import ingest_from_db
from .email_ingester import ingest_from_email

# --- Main Loop ---
def main_loop():
    """
    Main ingestion loop that runs continuously or can be triggered.
    """
    logger.info("Invoice Ingestion Agent started.")
    logger.info(f"Configuration: S3_BUCKET_RAW='{S3_BUCKET_RAW}', DB_CONNECTION_STRING='{DB_CONNECTION_STRING[:30]}...', "
                f"IMAP_HOST='{IMAP_HOST}', PREPROCESS_QUEUE_URL='{PREPROCESS_QUEUE_URL}', "
                f"STATE_STORE_PATH='{STATE_STORE_PATH}', POLL_INTERVAL_SECONDS={POLL_INTERVAL_SECONDS}")

    # Ensure raw directory exists for downloads
    os.makedirs("raw/", exist_ok=True)

    while True:
        logger.info("Starting new ingestion cycle...")
        try:
            ingest_from_s3()
        except Exception as e:
            logger.error(f"Unhandled exception in ingest_from_s3: {e}", exc_info=True)
            metrics["ingestion_errors"] += 1

        try:
            ingest_from_db()
        except Exception as e:
            logger.error(f"Unhandled exception in ingest_from_db: {e}", exc_info=True)
            metrics["ingestion_errors"] += 1

        try:
            ingest_from_email()
        except Exception as e:
            logger.error(f"Unhandled exception in ingest_from_email: {e}", exc_info=True)
            metrics["ingestion_errors"] += 1

        logger.info(f"Ingestion cycle finished. Metrics: {metrics}")
        logger.info(f"Sleeping for {POLL_INTERVAL_SECONDS} seconds...")
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Invoice Ingestion Agent stopped by user.")
    except Exception as e:
        logger.critical(f"Critical unhandled exception in main_loop: {e}", exc_info=True)
    finally:
        logger.info(f"Final Metrics: {metrics}")
        # Optionally, save final state one last time if needed, though it's saved per item.
