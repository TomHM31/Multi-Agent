import os
import logging
from datetime import datetime
# import imaplib # To be uncommented
# import email as email_parser # To be uncommented
# from email.header import decode_header # To be uncommented

from .invoice_ingestion_agent import (
    load_state,
    has_been_processed,
    mark_as_processed,
    publish_to_queue,
    metrics,
    IMAP_HOST, # Assuming these are defined in the main agent
    IMAP_USER,
    IMAP_PASSWORD,
    logger # Assuming logger is configured in main agent
)

# If logger is not easily shared, configure a local one for this module
# logger = logging.getLogger(__name__)

def ingest_from_email():
    """
    Connects to IMAP server, searches for unseen invoices,
    parses attachments, publishes messages, and marks emails as seen.
    """
    logger.info("Starting Email ingestion...")
    current_state = load_state()

    # Placeholder for IMAP client logic (imaplib, email)
    # try:
    #     # Consider connection timeout and error handling for login
    #     mail = imaplib.IMAP4_SSL(IMAP_HOST) # Add timeout e.g. imaplib.IMAP4_SSL(IMAP_HOST, timeout=30)
    #     mail.login(IMAP_USER, IMAP_PASSWORD)
    #     mail.select("inbox") # Or a specific folder, make this configurable?
    #
    #     # Search for UNSEEN emails with "Invoice" in subject (case-insensitive if server supports it)
    #     # The search criteria might need to be more robust or configurable.
    #     search_criteria = '(UNSEEN SUBJECT "Invoice")' # Could also search for keywords in body
    #     status, messages = mail.search(None, search_criteria)
    #
    #     if status != "OK":
    #         logger.error(f"Failed to search emails with criteria '{search_criteria}'. Status: {status}")
    #         metrics["ingestion_errors"] += 1
    #         mail.logout() # Ensure logout on error
    #         return
    #
    #     email_ids = messages[0].split() # List of email IDs as bytes
    #     if not email_ids:
    #         logger.info("No new emails found matching criteria.")
    #         mail.logout()
    #         return
    #
    #     logger.info(f"Found {len(email_ids)} email(s) matching criteria '{search_criteria}'.")
    #
    #     for email_id_bytes in email_ids:
    #         email_id_str = email_id_bytes.decode() # For logging and state key
    #         # Construct a unique source_id for email items
    #         source_id_email_base = f"email_{IMAP_USER}_{email_id_str}"
    #
    #         if has_been_processed(current_state, source_id_email_base):
    #             logger.debug(f"Skipping already processed email (by state file): ID {email_id_str}")
    #             continue
    #
    #         try:
    #             # Fetch the email by ID (RFC822 gets the full message)
    #             res, msg_data = mail.fetch(email_id_bytes, "(RFC822)")
    #             if res != 'OK':
    #                 logger.error(f"Failed to fetch email ID {email_id_str}. Status: {res}")
    #                 metrics["ingestion_errors"] += 1
    #                 continue # Try next email
    #
    #             # msg_data is a list of tuples (data_item, content)
    #             # We expect one item for RFC822 fetch
    #             email_message = email_parser.message_from_bytes(msg_data[0][1])
    #
    #             # Decode email subject
    #             subject_header = email_message["Subject"]
    #             subject_decoded_parts = decode_header(subject_header if subject_header else "")
    #             subject = ""
    #             for part_content, part_charset in subject_decoded_parts:
    #                 if isinstance(part_content, bytes):
    #                     subject += part_content.decode(part_charset if part_charset else "utf-8", errors="replace")
    #                 else:
    #                     subject += part_content
    #
    #             # Get sender
    #             sender = email_message.get("From", "Unknown Sender")
    #
    #             # Infer vendor (e.g., from sender's domain or display name)
    #             # This is a very basic inference and can be significantly improved.
    #             vendor = "unknown_vendor"
    #             if sender and "@" in sender:
    #                 try:
    #                     vendor_domain = sender.split("@")[1]
    #                     if ">" in vendor_domain: # Handle "Display Name <email@example.com>"
    #                         vendor_domain = vendor_domain.split(">")[0]
    #                     vendor = vendor_domain.split(".")[0] # e.g. 'company' from 'user@company.com'
    #                 except IndexError:
    #                     vendor = sender # Fallback if parsing fails
    #             elif sender:
    #                 vendor = sender.split("<")[0].strip() # Use display name if available
    #
    #             # Create raw directory if it doesn't exist
    #             raw_dir = "raw/" # Consider making this configurable
    #             os.makedirs(raw_dir, exist_ok=True)
    #
    #             attachment_processed_count = 0
    #             for part_index, part in enumerate(email_message.walk()):
    #                 content_disposition = str(part.get("Content-Disposition"))
    #                 if "attachment" in content_disposition:
    #                     original_filename = part.get_filename()
    #                     if original_filename:
    #                         # Decode filename (can be complex due to encodings)
    #                         decoded_filename_parts = decode_header(original_filename)
    #                         decoded_filename = ""
    #                         for fn_part, fn_enc in decoded_filename_parts:
    #                             if isinstance(fn_part, bytes):
    #                                 decoded_filename += fn_part.decode(fn_enc if fn_enc else "utf-8", errors="replace")
    #                             else:
    #                                 decoded_filename += fn_part
    #                         original_filename = decoded_filename.strip()
    #
    #                         # Sanitize filename (simple version, consider a robust library for production)
    #                         safe_filename = "".join(c if c.isalnum() or c in ('.', '_', '-') else '_' for c in original_filename)
    #                         if not safe_filename: # Handle empty or all-special-char filenames
    #                             safe_filename = f"attachment_{part_index}"
    #
    #                         local_path = os.path.join(raw_dir, f"{vendor}_{email_id_str}_{safe_filename}")
    #
    #                         logger.info(f"Saving attachment '{original_filename}' from email ID {email_id_str} to '{local_path}'")
    #                         try:
    #                             with open(local_path, 'wb') as f_attach:
    #                                 f_attach.write(part.get_payload(decode=True))
    #                         except Exception as e_write:
    #                             logger.error(f"Failed to write attachment '{original_filename}' to '{local_path}': {e_write}")
    #                             metrics["ingestion_errors"] += 1
    #                             continue # Skip this attachment
    #
    #                         # Unique source_id for each attachment
    #                         attachment_source_id = f"{source_id_email_base}_attachment_{part_index}"
    #
    #                         message = {
    #                             "file_path": local_path,
    #                             "source_id": attachment_source_id,
    #                             "source_type": "email_attachment",
    #                             "vendor": vendor, # Could also try to infer from filename if more reliable
    #                             "original_filename": original_filename,
    #                             "email_subject": subject,
    #                             "email_sender": sender,
    #                             "email_id": email_id_str,
    #                             # Parse email date header for a more accurate timestamp
    #                             "timestamp": email_parser.utils.parsedate_to_datetime(email_message['Date']).isoformat() if email_message['Date'] else datetime.now().isoformat()
    #                         }
    #                         publish_to_queue(message)
    #                         # Mark each attachment as processed in state? Or just the parent email?
    #                         # For now, marking parent email after all attachments.
    #                         attachment_processed_count += 1
    #
    #             if attachment_processed_count > 0:
    #                 # Mark email as SEEN in IMAP server
    #                 # mail.store(email_id_bytes, '+FLAGS', '\\Seen')
    #                 mark_as_processed(current_state, source_id_email_base) # Mark base email ID in local state
    #                 metrics["emails_processed"] += 1 # Count per email, not per attachment
    #                 logger.info(f"Successfully processed {attachment_processed_count} attachment(s) from email ID: {email_id_str} (Subject: '{subject}')")
    #             else:
    #                 logger.info(f"No attachments found or processed for email ID: {email_id_str} (Subject: '{subject}')")
    #                 # Optionally mark as seen even if no attachments, or handle differently (e.g. if invoice is in body)
    #                 # mail.store(email_id_bytes, '+FLAGS', '\\Seen')
    #                 # If no attachments, we might not want to mark it in our state store unless we are sure it's not an invoice.
    #                 # For now, we only mark_as_processed if attachments were handled.
    #
    #         except Exception as e:
    #             logger.error(f"Error processing email ID {email_id_str}: {e}", exc_info=True)
    #             metrics["ingestion_errors"] += 1
    #             # TODO: Write to dead-letter file or queue
    #
    #     mail.logout()
    # except imaplib.IMAP4.error as imap_err: # More specific error for IMAP issues
    #     logger.error(f"IMAP error ({IMAP_HOST}): {imap_err}", exc_info=True)
    #     metrics["ingestion_errors"] += 1
    # except Exception as e: # General catch-all
    #     logger.error(f"Error connecting to or processing emails via IMAP ({IMAP_HOST}): {e}", exc_info=True)
    #     metrics["ingestion_errors"] += 1
    logger.info("Email ingestion finished (Placeholder).")
    pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Testing email_ingester.py directly...")

    if not hasattr(invoice_ingestion_agent, 'publish_to_queue'):
        def _mock_publish(msg): logger.info(f"Mock publish: {msg}")
        invoice_ingestion_agent.publish_to_queue = _mock_publish
        invoice_ingestion_agent.metrics = {"emails_processed": 0, "ingestion_errors": 0}
        invoice_ingestion_agent.IMAP_HOST = os.getenv("IMAP_HOST", "test-imap-host-direct")
        invoice_ingestion_agent.IMAP_USER = os.getenv("IMAP_USER", "test-imap-user-direct")
        invoice_ingestion_agent.IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "test-imap-password-direct")
        invoice_ingestion_agent.STATE_STORE_PATH = "test_email_ingester_state.json"
        if os.path.exists(invoice_ingestion_agent.STATE_STORE_PATH):
            os.remove(invoice_ingestion_agent.STATE_STORE_PATH)

    ingest_from_email()
    logger.info(f"Direct test metrics: {invoice_ingestion_agent.metrics}")
    if os.path.exists(invoice_ingestion_agent.STATE_STORE_PATH):
        os.remove(invoice_ingestion_agent.STATE_STORE_PATH)
