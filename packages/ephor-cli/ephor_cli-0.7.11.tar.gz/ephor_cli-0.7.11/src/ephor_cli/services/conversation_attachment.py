from typing import List
import os
import logging
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from ephor_cli.clients.ddb.conversation_attachment import ConversationAttachmentDDBClient
from ephor_cli.types.conversation_attachment import ConversationAttachment
from ephor_cli.constant import DYNAMODB_TABLE_NAME

logger = logging.getLogger(__name__)

class ConversationAttachmentService:
    """Service for handling conversation attachment operations."""

    def __init__(self):
        self.ddb_client = ConversationAttachmentDDBClient(table_name=DYNAMODB_TABLE_NAME)
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="indexing")

    def __del__(self):
        """Clean up the thread pool executor when the service is destroyed."""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
                logger.debug("[ConversationAttachmentService] Thread pool executor shut down")
        except Exception as e:
            logger.error(f"[ConversationAttachmentService] Error shutting down thread pool: {e}")

    def shutdown(self):
        """Explicitly shut down the thread pool executor."""
        try:
            self.executor.shutdown(wait=True)
            logger.info("[ConversationAttachmentService] Thread pool executor shut down gracefully")
        except Exception as e:
            logger.error(f"[ConversationAttachmentService] Error shutting down thread pool: {e}")

    def create_attachment(self, attachment: ConversationAttachment) -> ConversationAttachment:
        """Create a new conversation attachment.

        Args:
            attachment: The attachment to create

        Returns:
            The created attachment
        """
        success = self.ddb_client.store_attachment(attachment)
        if not success:
            raise Exception("Failed to store conversation attachment")
        
        # Trigger asynchronous indexing for supported file types
        self._trigger_attachment_indexing_async(attachment)
        
        return attachment

    def _trigger_attachment_indexing_async(self, attachment: ConversationAttachment):
        """Trigger asynchronous indexing for PDF, text, and image file attachments."""
        try:
            # Check if the file type is indexable
            is_indexable = (
                attachment.file_type in ["application/pdf", "text/plain"] or 
                attachment.file_type.startswith("image/")
            )
            
            if is_indexable:
                logger.info(f"[ConversationAttachmentService] Scheduling async indexing for {attachment.file_name} ({attachment.file_type})")
                
                # Submit indexing task to thread pool
                future = self.executor.submit(self._perform_indexing, attachment)
                
                # Add callback to handle completion
                future.add_done_callback(lambda f: self._handle_indexing_completion(f, attachment))
                    
            else:
                logger.debug(f"[ConversationAttachmentService] Skipping indexing for {attachment.file_name} ({attachment.file_type}) - not an indexable type (supports: PDF, text, images)")
                
        except Exception as e:
            logger.error(f"[ConversationAttachmentService] Error scheduling indexing for {attachment.file_name}: {e}")

    def _perform_indexing(self, attachment: ConversationAttachment) -> dict:
        """Perform the actual indexing of an attachment in a background thread."""
        logger.info(f"[ConversationAttachmentService] Starting indexing for {attachment.file_name}")
        
        try:
            # Import here to avoid circular dependencies
            from ephor_cli.services.conversation_indexing_service import ConversationIndexingService
            
            indexing_service = ConversationIndexingService()
            
            # Index the specific attachment
            result = indexing_service._index_single_attachment(attachment, attachment.conversation_id)
            
            return {
                "success": result.get("success", False),
                "chunk_count": result.get("chunk_count", 0),
                "error": result.get("error"),
                "attachment_id": attachment.id
            }
                
        except ImportError:
            logger.warning("[ConversationAttachmentService] Indexing service not available")
            return {"success": False, "error": "Indexing service not available", "attachment_id": attachment.id}
        except Exception as e:
            logger.error(f"[ConversationAttachmentService] Error performing indexing for {attachment.file_name}: {e}")
            return {"success": False, "error": str(e), "attachment_id": attachment.id}

    def _handle_indexing_completion(self, future, attachment: ConversationAttachment):
        """Handle the completion of an indexing task."""
        try:
            result = future.result()
            
            if result["success"]:
                logger.info(f"[ConversationAttachmentService] Successfully indexed {attachment.file_name}: {result.get('chunk_count', 0)} chunks")
                is_indexed = True
            else:
                logger.warning(f"[ConversationAttachmentService] Failed to index {attachment.file_name}: {result.get('error', 'Unknown error')}")
                is_indexed = False
            
            # Update the attachment's indexing status
            self.update_attachment_index_status(
                attachment.user_id,
                attachment.project_id, 
                attachment.conversation_id,
                attachment.id,
                is_indexed
            )
            
        except Exception as e:
            logger.error(f"[ConversationAttachmentService] Error handling indexing completion for {attachment.file_name}: {e}")
            # Mark as failed indexing
            self.update_attachment_index_status(
                attachment.user_id,
                attachment.project_id,
                attachment.conversation_id, 
                attachment.id,
                False
            )

    def update_attachment_index_status(self, user_id: str, project_id: str, conversation_id: str, attachment_id: str, is_indexed: bool) -> bool:
        """Update the indexing status of an attachment.
        
        Args:
            user_id: The ID of the user who owns the conversation
            project_id: The ID of the project the conversation belongs to
            conversation_id: The ID of the conversation
            attachment_id: The ID of the attachment to update
            is_indexed: The new indexing status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.ddb_client.update_attachment_index_status(
                user_id, project_id, conversation_id, attachment_id, is_indexed
            )
            
            if success:
                status_text = "indexed" if is_indexed else "failed to index"
                logger.info(f"[ConversationAttachmentService] Updated attachment {attachment_id} status to: {status_text}")
            else:
                logger.warning(f"[ConversationAttachmentService] Failed to update indexing status for attachment {attachment_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"[ConversationAttachmentService] Error updating indexing status for attachment {attachment_id}: {e}")
            return False

    def _trigger_attachment_indexing(self, attachment: ConversationAttachment):
        """Trigger indexing for PDF, text, and image file attachments."""
        # This method is kept for backward compatibility but now delegates to async version
        self._trigger_attachment_indexing_async(attachment)

    def _extract_conversation_id(self, attachment: ConversationAttachment) -> str:
        """Extract conversation ID from attachment context."""
        # TODO: Implement based on your attachment model structure
        # This might be a direct field or extracted from composite keys
        return getattr(attachment, 'conversation_id', None)
    
    def _extract_user_id(self, attachment: ConversationAttachment) -> str:
        """Extract user ID from attachment context."""
        # TODO: Implement based on your attachment model structure
        return getattr(attachment, 'user_id', None)
    
    def _extract_project_id(self, attachment: ConversationAttachment) -> str:
        """Extract project ID from attachment context.""" 
        # TODO: Implement based on your attachment model structure
        return getattr(attachment, 'project_id', None)

    def list_attachments(
        self, user_id: str, project_id: str, conversation_id: str
    ) -> List[ConversationAttachment]:
        """List all attachments for a conversation.

        Args:
            user_id: The ID of the user who owns the conversation
            project_id: The ID of the project the conversation belongs to
            conversation_id: The ID of the conversation

        Returns:
            List of conversation attachments
        """
        return self.ddb_client.list_attachments(user_id, project_id, conversation_id)

    def delete_attachment(
        self, user_id: str, project_id: str, conversation_id: str, attachment_id: str
    ) -> bool:
        """Delete a conversation attachment and its indexed content.

        Args:
            user_id: The ID of the user who owns the conversation
            project_id: The ID of the project the conversation belongs to
            conversation_id: The ID of the conversation
            attachment_id: The ID of the attachment to delete

        Returns:
            True if successful, False otherwise
        """
        success = self.ddb_client.delete_attachment(user_id, project_id, conversation_id, attachment_id)
        
        if success:
            # Also clean up indexed content for this attachment
            self._cleanup_attachment_index(conversation_id, attachment_id)
            
        return success
    
    def _cleanup_attachment_index(self, conversation_id: str, attachment_id: str):
        """Clean up indexed chunks for a deleted attachment."""
        try:
            from ephor_cli.services.conversation_indexing_service import ConversationIndexingService
            
            logger.info(f"[ConversationAttachmentService] Cleaning up indexed chunks for attachment {attachment_id}")
            
            indexing_service = ConversationIndexingService()
            
            # Delete chunks for this specific attachment
            success = indexing_service.delete_specific_attachment_chunks(conversation_id, attachment_id)
            
            if success:
                logger.info(f"[ConversationAttachmentService] Successfully cleaned up indexed chunks for attachment {attachment_id}")
            else:
                logger.info(f"[ConversationAttachmentService] No indexed chunks found for attachment {attachment_id} (might not have been indexed)")
            
        except ImportError:
            logger.warning("[ConversationAttachmentService] Indexing service not available for cleanup")
        except Exception as e:
            logger.error(f"[ConversationAttachmentService] Error cleaning up index for attachment {attachment_id}: {e}")

    def get_attachment_count(self, user_id: str, project_id: str, conversation_id: str) -> int:
        """Get the total count of attachments for a conversation.

        Args:
            user_id: The ID of the user who owns the conversation
            project_id: The ID of the project the conversation belongs to
            conversation_id: The ID of the conversation

        Returns:
            Total number of attachments
        """
        return self.ddb_client.get_attachment_count(user_id, project_id, conversation_id) 