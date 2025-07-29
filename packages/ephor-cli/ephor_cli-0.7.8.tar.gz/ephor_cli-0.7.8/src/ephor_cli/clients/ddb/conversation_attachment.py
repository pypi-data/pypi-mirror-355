import datetime
import json
from typing import List, Optional

from ephor_cli.clients.ddb.base import BaseDDBClient
from ephor_cli.types.conversation_attachment import ConversationAttachment


class ConversationAttachmentDDBClient(BaseDDBClient):
    """DynamoDB client for conversation attachment operations."""

    def _get_conversation_attachments_pk(self, user_id: str, project_id: str, conversation_id: str) -> str:
        """Create the partition key for conversation attachments."""
        return f"USER#{user_id}#PROJECT#{project_id}#CONVERSATION#{conversation_id}"

    def _get_conversation_attachments_sk(self) -> str:
        """Create the sort key for conversation attachments."""
        return "ATTACHMENTS"

    def _validate_attachment_size(self, current_attachments: List[dict], new_attachment: dict) -> bool:
        """Validate that adding a new attachment won't exceed DynamoDB item size limit.
        
        Args:
            current_attachments: List of existing attachment dictionaries
            new_attachment: New attachment dictionary to add
            
        Returns:
            True if the size is within limits, False otherwise
        """
        # Calculate current size (rough estimate)
        current_size = len(json.dumps(current_attachments, default=str))
        new_attachment_size = len(json.dumps(new_attachment, default=str))
        
        # Leave buffer for DynamoDB overhead and metadata
        max_allowed_size = 350000  # 350KB out of 400KB limit
        
        return (current_size + new_attachment_size) <= max_allowed_size

    def store_attachment(self, attachment: ConversationAttachment) -> bool:
        """Store a conversation attachment in DynamoDB.

        Args:
            attachment: The attachment object to store

        Returns:
            True if successful, False otherwise
        """
        try:
            pk = self._get_conversation_attachments_pk(
                attachment.user_id, attachment.project_id, attachment.conversation_id
            )
            sk = self._get_conversation_attachments_sk()
            
            # Prepare attachment data
            attachment_data = {
                "id": attachment.id,
                "s3_key": attachment.s3_key,
                "file_name": attachment.file_name,
                "file_type": attachment.file_type,
                "file_size": attachment.file_size,
                "is_indexed": attachment.is_indexed,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "updated_at": datetime.datetime.utcnow().isoformat(),
            }
            
            # Get current attachments to validate size
            try:
                response = self.table.get_item(Key={"PK": pk, "SK": sk})
                current_attachments = response.get("Item", {}).get("attachments", [])
                
                # Validate size before adding
                if not self._validate_attachment_size(current_attachments, attachment_data):
                    raise ValueError("Adding this attachment would exceed DynamoDB item size limit")
                    
            except Exception as e:
                if "exceed DynamoDB item size limit" in str(e):
                    raise e
                # If item doesn't exist, current_attachments will be empty
                current_attachments = []

            # Use UpdateItem to append the new attachment
            self.table.update_item(
                Key={"PK": pk, "SK": sk},
                UpdateExpression="SET attachments = list_append(if_not_exists(attachments, :empty_list), :new_attachment), "
                                "total_count = if_not_exists(total_count, :zero) + :one, "
                                "updated_at = :updated_at",
                ExpressionAttributeValues={
                    ":empty_list": [],
                    ":new_attachment": [self.sanitize_for_dynamodb(attachment_data)],
                    ":zero": 0,
                    ":one": 1,
                    ":updated_at": datetime.datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error storing conversation attachment: {e}")
            return False

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
        try:
            pk = self._get_conversation_attachments_pk(user_id, project_id, conversation_id)
            sk = self._get_conversation_attachments_sk()
            
            response = self.table.get_item(Key={"PK": pk, "SK": sk})
            
            if "Item" not in response:
                return []
            
            item = response["Item"]
            attachments_data = item.get("attachments", [])
            
            attachments = []
            for attachment_dict in attachments_data:
                # Convert back from DynamoDB format
                attachment_dict = self.sanitize_from_dynamodb(attachment_dict)
                # Add required fields for ConversationAttachment
                attachment_dict["user_id"] = user_id
                attachment_dict["project_id"] = project_id
                attachment_dict["conversation_id"] = conversation_id
                
                attachments.append(ConversationAttachment(**attachment_dict))

            return attachments
        except Exception as e:
            print(f"Error listing conversation attachments: {e}")
            return []

    def delete_attachment(
        self, user_id: str, project_id: str, conversation_id: str, attachment_id: str
    ) -> bool:
        """Delete a conversation attachment.

        Args:
            user_id: The ID of the user who owns the conversation
            project_id: The ID of the project the conversation belongs to
            conversation_id: The ID of the conversation
            attachment_id: The ID of the attachment to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            pk = self._get_conversation_attachments_pk(user_id, project_id, conversation_id)
            sk = self._get_conversation_attachments_sk()
            
            # Get current attachments
            response = self.table.get_item(Key={"PK": pk, "SK": sk})
            
            if "Item" not in response:
                return False  # No attachments exist
                
            item = response["Item"]
            attachments = item.get("attachments", [])
            
            # Find and remove the attachment
            updated_attachments = [att for att in attachments if att.get("id") != attachment_id]
            
            if len(updated_attachments) == len(attachments):
                return False  # Attachment not found
            
            # Update the item
            if updated_attachments:
                # Update with remaining attachments
                self.table.update_item(
                    Key={"PK": pk, "SK": sk},
                    UpdateExpression="SET attachments = :attachments, total_count = :count, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":attachments": updated_attachments,
                        ":count": len(updated_attachments),
                        ":updated_at": datetime.datetime.utcnow().isoformat()
                    }
                )
            else:
                # Delete the entire item if no attachments remain
                self.table.delete_item(Key={"PK": pk, "SK": sk})
            
            return True
        except Exception as e:
            print(f"Error deleting conversation attachment: {e}")
            return False

    def get_attachment_count(self, user_id: str, project_id: str, conversation_id: str) -> int:
        """Get the total count of attachments for a conversation.

        Args:
            user_id: The ID of the user who owns the conversation
            project_id: The ID of the project the conversation belongs to
            conversation_id: The ID of the conversation

        Returns:
            Total number of attachments
        """
        try:
            pk = self._get_conversation_attachments_pk(user_id, project_id, conversation_id)
            sk = self._get_conversation_attachments_sk()
            
            response = self.table.get_item(
                Key={"PK": pk, "SK": sk},
                ProjectionExpression="total_count"
            )
            
            if "Item" not in response:
                return 0
                
            return response["Item"].get("total_count", 0)
        except Exception as e:
            print(f"Error getting attachment count: {e}")
            return 0 

    def update_attachment_index_status(
        self, user_id: str, project_id: str, conversation_id: str, attachment_id: str, is_indexed: bool
    ) -> bool:
        """Update the indexing status of a specific attachment.

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
            pk = self._get_conversation_attachments_pk(user_id, project_id, conversation_id)
            sk = self._get_conversation_attachments_sk()
            
            # Get current attachments
            response = self.table.get_item(Key={"PK": pk, "SK": sk})
            
            if "Item" not in response:
                return False  # No attachments exist
                
            item = response["Item"]
            attachments = item.get("attachments", [])
            
            # Find and update the attachment
            updated = False
            for attachment in attachments:
                if attachment.get("id") == attachment_id:
                    attachment["is_indexed"] = is_indexed
                    attachment["updated_at"] = datetime.datetime.utcnow().isoformat()
                    updated = True
                    break
            
            if not updated:
                return False  # Attachment not found
            
            # Update the item
            self.table.update_item(
                Key={"PK": pk, "SK": sk},
                UpdateExpression="SET attachments = :attachments, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ":attachments": attachments,
                    ":updated_at": datetime.datetime.utcnow().isoformat()
                }
            )
            
            return True
        except Exception as e:
            print(f"Error updating attachment index status: {e}")
            return False 