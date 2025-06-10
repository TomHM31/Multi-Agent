import os
import logging
# import boto3 # To be uncommented when S3 logic is implemented

from .invoice_ingestion_agent import (
    load_state,
    has_been_processed,
    mark_as_processed,
    publish_to_queue,
    metrics,
    S3_BUCKET_RAW, # Assuming this is defined in the main agent and imported
    logger # Assuming logger is configured in main agent and can be used or re-configured
)

# If logger is not easily shared, configure a local one for this module
# logger = logging.getLogger(__name__) # Alternative: module-specific logger

def ingest_from_s3():
    """
    Lists objects in S3_BUCKET_RAW, downloads new ones, builds a message,
    publishes to PREPROCESS_QUEUE_URL, and updates the state.
    """
    logger.info("Starting S3 ingestion...")
    current_state = load_state() # Renamed from 'state' to avoid conflict if boto3.client('s3') is named 's3'

    # Placeholder for boto3 S3 client logic
    # s3_client = boto3.client('s3')
    # try:
    #     response = s3_client.list_objects_v2(Bucket=S3_BUCKET_RAW)
    #     if 'Contents' not in response:
    #         logger.info(f"No objects found in S3 bucket: {S3_BUCKET_RAW}")
    #         return
    #
    #     for obj in response['Contents']:
    #         s3_object_key = obj['Key']
    #         # Construct a unique source_id for S3 objects
    #         # Using a consistent format: type_bucket_key
    #         source_id_s3 = f"s3_{S3_BUCKET_RAW}_{s3_object_key.replace('/', '_')}"
    #
    #         if has_been_processed(current_state, source_id_s3):
    #             logger.debug(f"Skipping already processed S3 object: {s3_object_key}")
    #             continue
    #
    #         try:
    #             # Create raw directory if it doesn't exist
    #             raw_dir = "raw/" # Consider making this configurable or relative to a base path
    #             os.makedirs(raw_dir, exist_ok=True)
    #             # Sanitize basename for local path
    #             base_name = os.path.basename(s3_object_key)
    #             safe_base_name = "".join(c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in base_name)
    #             local_path = os.path.join(raw_dir, safe_base_name)
    #
    #             logger.info(f"Downloading {s3_object_key} from bucket {S3_BUCKET_RAW} to {local_path}")
    #             # s3_client.download_file(S3_BUCKET_RAW, s3_object_key, local_path)
    #
    #             # Infer vendor (example: from a prefix like "vendor_name/invoice.pdf")
    #             vendor = "unknown_vendor"
    #             if "/" in s3_object_key:
    #                 # Takes the first part of the path as vendor, could be more sophisticated
    #                 vendor = s3_object_key.split('/')[0]
    #
    #             message = {
    #                 "file_path": local_path,
    #                 "source_id": source_id_s3,
    #                 "source_type": "s3",
    #                 "vendor": vendor,
    #                 "original_filename": base_name, # Original name from S3
    #                 "s3_bucket": S3_BUCKET_RAW,
    #                 "s3_key": s3_object_key,
    #                 "timestamp": obj["LastModified"].isoformat()
    #             }
    #             publish_to_queue(message)
    #             mark_as_processed(current_state, source_id_s3) # Pass the loaded state
    #             metrics["s3_processed"] += 1
    #             logger.info(f"Successfully processed S3 object: {s3_object_key}")
    #
    #         except Exception as e: # Catch specific boto3 errors if possible
    #             logger.error(f"Error processing S3 object {s3_object_key}: {e}", exc_info=True)
    #             metrics["ingestion_errors"] += 1
    #             # TODO: Write to dead-letter file or queue: { "source_id": source_id_s3, "error": str(e) }
    #
    # except Exception as e: # Catch specific boto3 errors if possible
    #     logger.error(f"Error listing S3 objects in bucket {S3_BUCKET_RAW}: {e}", exc_info=True)
    #     metrics["ingestion_errors"] += 1
    logger.info("S3 ingestion finished (Placeholder).")
    pass

if __name__ == '__main__':
    # This allows testing this module directly if needed,
    # though it's better to test through the main agent or pytest.
    # Ensure environment variables are set if running directly.
    # For direct execution, logger might need to be configured here.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Testing s3_ingester.py directly...")
    
    # Mock necessary components if run directly for simple test
    if not hasattr(invoice_ingestion_agent, 'publish_to_queue'): # Check if imported correctly
        def _mock_publish(msg): logger.info(f"Mock publish: {msg}")
        invoice_ingestion_agent.publish_to_queue = _mock_publish
        invoice_ingestion_agent.metrics = {"s3_processed": 0, "ingestion_errors": 0}
        invoice_ingestion_agent.S3_BUCKET_RAW = os.getenv("S3_BUCKET_RAW", "test-s3-bucket-direct")
        invoice_ingestion_agent.STATE_STORE_PATH = "test_s3_ingester_state.json"
        if os.path.exists(invoice_ingestion_agent.STATE_STORE_PATH):
            os.remove(invoice_ingestion_agent.STATE_STORE_PATH)

    ingest_from_s3()
    logger.info(f"Direct test metrics: {invoice_ingestion_agent.metrics}")
    if os.path.exists(invoice_ingestion_agent.STATE_STORE_PATH): # Clean up test state file
        os.remove(invoice_ingestion_agent.STATE_STORE_PATH)
