import os
import logging
from datetime import datetime
# import sqlalchemy # To be uncommented when DB logic is implemented
# from sqlalchemy import create_engine, text # To be uncommented
# import requests # To be uncommented for downloading files

from .invoice_ingestion_agent import (
    load_state,
    has_been_processed,
    mark_as_processed,
    publish_to_queue,
    metrics,
    DB_CONNECTION_STRING, # Assuming this is defined in the main agent
    logger # Assuming logger is configured in main agent
)

# If logger is not easily shared, configure a local one for this module
# logger = logging.getLogger(__name__)

def ingest_from_db():
    """
    Connects to DB, fetches unprocessed invoices, downloads files,
    builds messages, publishes, and updates DB.
    """
    logger.info("Starting DB ingestion...")
    current_state = load_state() # DB state might be managed by 'processed' flag, but good for consistency

    # Placeholder for DB client logic (e.g., psycopg2/sqlalchemy)
    # try:
    #     engine = create_engine(DB_CONNECTION_STRING)
    #     with engine.connect() as connection:
    #         # Consider adding a LIMIT clause for batching if many unprocessed invoices
    #         result = connection.execute(text("SELECT id, vendor, file_url, uploaded_at FROM invoices WHERE processed = FALSE ORDER BY uploaded_at ASC"))
    #         processed_in_cycle = 0
    #         for row in result:
    #             db_invoice_id = row.id
    #             vendor = row.vendor if row.vendor else "unknown_vendor"
    #             file_url = row.file_url
    #             uploaded_at = row.uploaded_at
    #
    #             # Construct a unique source_id for DB items
    #             source_id_db = f"db_{vendor}_{db_invoice_id}"
    #
    #             # Optional: Check against local state store as well, though DB 'processed' flag is primary
    #             if has_been_processed(current_state, source_id_db):
    #                 logger.debug(f"Skipping already processed DB invoice (by state file): {db_invoice_id}")
    #                 continue
    #
    #             try:
    #                 # Create raw directory if it doesn't exist
    #                 raw_dir = "raw/" # Consider making this configurable
    #                 os.makedirs(raw_dir, exist_ok=True)
    #
    #                 local_path = ""
    #                 original_filename = ""
    #
    #                 if not file_url:
    #                     logger.warning(f"File URL is missing for DB invoice ID: {db_invoice_id}. Skipping.")
    #                     metrics["ingestion_errors"] += 1
    #                     # Optionally, mark as processed with error in DB or skip DB update
    #                     # connection.execute(text("UPDATE invoices SET processed=TRUE, error_message='Missing file_url' WHERE id=:id"), {"id": db_invoice_id})
    #                     # connection.commit()
    #                     continue
    #
    #                 if file_url.startswith("http://") or file_url.startswith("https://"):
    #                     # Download if it's a URL
    #                     # import requests # Moved to top-level import
    #                     original_filename = file_url.split('/')[-1].split('?')[0] # Basic way to get filename
    #                     safe_original_filename = "".join(c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in original_filename)
    #                     local_path = os.path.join(raw_dir, f"{vendor}_{db_invoice_id}_{safe_original_filename}")
    #
    #                     logger.info(f"Downloading {file_url} to {local_path} for DB invoice {db_invoice_id}")
    #                     # response = requests.get(file_url, stream=True, timeout=30) # Added timeout
    #                     # response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
    #                     # with open(local_path, 'wb') as f_download:
    #                     #     for chunk in response.iter_content(chunk_size=8192):
    #                     #         f_download.write(chunk)
    #                 elif os.path.exists(file_url): # Check if it's an existing local file path
    #                     original_filename = os.path.basename(file_url)
    #                     # Decide whether to copy to raw_dir or use directly
    #                     # Copying to raw_dir standardizes paths for downstream processing
    #                     safe_original_filename = "".join(c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in original_filename)
    #                     local_path = os.path.join(raw_dir, f"{vendor}_{db_invoice_id}_{safe_original_filename}")
    #                     logger.info(f"Copying local file {file_url} to {local_path} for DB invoice {db_invoice_id}")
    #                     # import shutil
    #                     # shutil.copy2(file_url, local_path) # copy2 preserves metadata
    #                 else:
    #                     logger.warning(f"Cannot determine how to access file_url: {file_url} for DB invoice {db_invoice_id}. It's not a URL and not a local path.")
    #                     metrics["ingestion_errors"] += 1
    #                     # Optionally, mark as processed with error in DB
    #                     # connection.execute(text("UPDATE invoices SET processed=TRUE, error_message='Invalid file_url' WHERE id=:id"), {"id": db_invoice_id})
    #                     # connection.commit()
    #                     continue # Skip this invoice
    #
    #                 message = {
    #                     "file_path": local_path,
    #                     "source_id": source_id_db,
    #                     "source_type": "database",
    #                     "vendor": vendor,
    #                     "original_filename": original_filename,
    #                     "db_invoice_id": db_invoice_id,
    #                     "timestamp": uploaded_at.isoformat() if uploaded_at else datetime.now().isoformat()
    #                 }
    #                 publish_to_queue(message)
    #
    #                 # Update DB: Mark as processed
    #                 # connection.execute(text("UPDATE invoices SET processed=TRUE, processed_at=NOW(), error_message=NULL WHERE id=:id"), {"id": db_invoice_id})
    #                 # connection.commit() # Important if not using autocommit
    #
    #                 mark_as_processed(current_state, source_id_db) # Also mark in local state for robustness
    #                 metrics["db_processed"] += 1
    #                 processed_in_cycle += 1
    #                 logger.info(f"Successfully processed DB invoice: {db_invoice_id}")
    #
    #             except Exception as e:
    #                 logger.error(f"Error processing DB invoice {db_invoice_id} (URL: {file_url}): {e}", exc_info=True)
    #                 metrics["ingestion_errors"] += 1
    #                 # Optionally, mark as processed with error in DB
    #                 # try:
    #                 #     connection.execute(text("UPDATE invoices SET processed=TRUE, processed_at=NOW(), error_message=:error WHERE id=:id"), {"id": db_invoice_id, "error": str(e)[:255]}) # Limit error message length
    #                 #     connection.commit()
    #                 # except Exception as db_update_err:
    #                 #     logger.error(f"Failed to update DB with error status for invoice {db_invoice_id}: {db_update_err}")
    #                 # TODO: Write to dead-letter file or queue
    #
    #         if processed_in_cycle > 0:
    #             logger.info(f"Processed {processed_in_cycle} invoices from DB in this cycle.")
    #         else:
    #             logger.info("No new unprocessed invoices found in DB.")
    #
    # except Exception as e: # Catch specific DB connection/query errors if possible
    #     logger.error(f"Error connecting to or querying DB ({DB_CONNECTION_STRING[:30]}...): {e}", exc_info=True)
    #     metrics["ingestion_errors"] += 1
    logger.info("DB ingestion finished (Placeholder).")
    pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Testing db_ingester.py directly...")

    # Mock necessary components for direct test
    if not hasattr(invoice_ingestion_agent, 'publish_to_queue'):
        def _mock_publish(msg): logger.info(f"Mock publish: {msg}")
        invoice_ingestion_agent.publish_to_queue = _mock_publish
        invoice_ingestion_agent.metrics = {"db_processed": 0, "ingestion_errors": 0}
        invoice_ingestion_agent.DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "test-db-string-direct")
        invoice_ingestion_agent.STATE_STORE_PATH = "test_db_ingester_state.json"
        if os.path.exists(invoice_ingestion_agent.STATE_STORE_PATH):
            os.remove(invoice_ingestion_agent.STATE_STORE_PATH)

    ingest_from_db()
    logger.info(f"Direct test metrics: {invoice_ingestion_agent.metrics}")
    if os.path.exists(invoice_ingestion_agent.STATE_STORE_PATH):
        os.remove(invoice_ingestion_agent.STATE_STORE_PATH)
