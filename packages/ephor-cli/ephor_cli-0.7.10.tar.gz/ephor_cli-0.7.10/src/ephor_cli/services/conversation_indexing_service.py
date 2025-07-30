import os
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from ephor_cli.services.opensearch_client import OpenSearchClient
from ephor_cli.services.embedding_service import EmbeddingService
from ephor_cli.services.text_processor import TextProcessor
from ephor_cli.services.conversation_attachment import ConversationAttachmentService
from ephor_cli.services.s3 import S3Service
from ephor_cli.services.image_captioning_service import ImageCaptioningService

logger = logging.getLogger(__name__)

class ConversationIndexingService:
    """Main service for indexing conversation attachments with vector embeddings."""
    
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.embedding_service = EmbeddingService()
        self.text_processor = TextProcessor()
        self.attachment_service = ConversationAttachmentService()
        self.s3_service = S3Service()
        self.image_captioning_service = ImageCaptioningService()
        
        self.max_retrieved_chunks = 10  # Hardcoded max chunks to retrieve
        self.similarity_threshold = 0.5  # Fixed similarity calculation, back to 0.5
        self.image_caption_threshold = 0.5  # Threshold for image captions - balanced filtering
        
        # JSON dump configuration
        self.dump_search_results = False # Enable JSON dumping for debugging
        self.dump_file_path = "/workspace/ephor-ti/search_results_dump.json"
        
        # Ensure vector index exists
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Ensure the vector index exists in OpenSearch."""
        try:
            success = self.opensearch_client.create_vector_index()
            if success:
                logger.info("Vector index ready for use")
            else:
                logger.error("Failed to create/verify vector index")
        except Exception as e:
            logger.error(f"Error ensuring index exists: {e}")
    
    def _dump_search_results(self, query_text: str, conversation_id: str, results: List[Dict[str, Any]], 
                           query_embedding: List[float] = None):
        """Dump search results to JSON file for debugging."""
        if not self.dump_search_results:
            return
            
        try:
            dump_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "query": {
                    "text": query_text,
                    "conversation_id": conversation_id,
                    "similarity_threshold": self.similarity_threshold,
                    "image_caption_threshold": self.image_caption_threshold,
                    "max_chunks": self.max_retrieved_chunks
                },
                "results": {
                    "total_found": len(results),
                    "chunks": []
                }
            }
            
            # Add detailed chunk information
            for i, result in enumerate(results):
                chunk_info = {
                    "rank": i + 1,
                    "similarity_score": result.get('similarity_score', 0),
                    "filename": result.get('filename', 'unknown'),
                    "chunk_index": result.get('chunk_index', 0),
                    "chunk_text": result.get('chunk_text', ''),
                    "token_count": result.get('token_count', 0),
                    "file_type": result.get('file_type', 'unknown'),
                    "content_type": result.get('content_type', 'text'),
                    "created_at": result.get('created_at', 'unknown')
                }
                dump_data["results"]["chunks"].append(chunk_info)
            
            # Save to file
            with open(self.dump_file_path, 'w', encoding='utf-8') as f:
                json.dump(dump_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"🗂️ Search results dumped to: {self.dump_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to dump search results: {e}")
    
    def index_conversation_attachments(self, user_id: str, project_id: str, 
                                     conversation_id: str) -> Dict[str, Any]:
        """Index all attachments for a conversation."""
        try:
            # Get all conversation attachments
            attachments = self.attachment_service.list_attachments(
                user_id, project_id, conversation_id
            )
            
            if not attachments:
                logger.info(f"No attachments found for conversation {conversation_id}")
                return {"status": "success", "indexed_attachments": 0}
            
            indexed_count = 0
            total_chunks = 0
            processing_stats = []
            
            for attachment in attachments:
                try:
                    result = self._index_single_attachment(attachment, conversation_id)
                    if result["success"]:
                        indexed_count += 1
                        total_chunks += result["chunk_count"]
                        processing_stats.append(result["stats"])
                        
                        logger.info(f"Indexed {attachment.file_name}: {result['chunk_count']} chunks")
                    else:
                        logger.warning(f"Failed to index {attachment.file_name}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Error indexing attachment {attachment.file_name}: {e}")
                    continue
            
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "total_attachments": len(attachments),
                "indexed_attachments": indexed_count,
                "total_chunks": total_chunks,
                "processing_stats": processing_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to index conversation attachments: {e}")
            return {
                "status": "error",
                "error": str(e),
                "conversation_id": conversation_id
            }
    
    def _index_single_attachment(self, attachment, conversation_id: str) -> Dict[str, Any]:
        """Index a single attachment file."""
        try:
            # Handle images with captioning
            if attachment.file_type.startswith("image/"):
                return self._index_image_attachment(attachment, conversation_id)
            
            if attachment.file_type not in ["application/pdf", "text/plain"]:
                logger.info(f"Skipping unsupported file type: {attachment.file_type}")
                return {
                    "success": True,
                    "chunk_count": 0,
                    "stats": {"skipped": True, "reason": "unsupported_type"},
                    "attachment_id": attachment.id
                }
            
            # Download file content from S3
            file_content = self.s3_service.get_file_content(attachment.s3_key)
            if not file_content:
                return {
                    "success": False,
                    "error": "Failed to download file from S3",
                    "attachment_id": attachment.id
                }
            
            # Extract text content
            text_content = self.text_processor.extract_text_from_file(
                file_content, attachment.file_type
            )
            
            if not text_content or len(text_content.strip()) < 100:
                logger.warning(f"Insufficient text content in {attachment.file_name}")
                return {
                    "success": True,
                    "chunk_count": 0,
                    "stats": {"skipped": True, "reason": "insufficient_content"},
                    "attachment_id": attachment.id
                }
            
            # Create text chunks
            chunks = self.text_processor.create_chunks(
                text_content,
                attachment.id,
                attachment.file_name,
                conversation_id,
                attachment.file_type
            )
            
            if not chunks:
                return {
                    "success": True,
                    "chunk_count": 0,
                    "stats": {"skipped": True, "reason": "no_chunks_created"},
                    "attachment_id": attachment.id
                }
            
            # Generate embeddings
            chunk_texts = [chunk["chunk_text"] for chunk in chunks]
            embeddings = self.embedding_service.generate_embeddings(chunk_texts)
            
            # Add embeddings to chunks
            for i, chunk in enumerate(chunks):
                if i < len(embeddings):
                    chunk["embedding_vector"] = embeddings[i]
                else:
                    # Fallback for any missing embeddings
                    chunk["embedding_vector"] = [0.0] * 1536
            
            # Store chunks in OpenSearch
            success = self.opensearch_client.store_chunks(chunks)
            
            if success:
                stats = self.text_processor.get_processing_stats(chunks)
                return {
                    "success": True,
                    "chunk_count": len(chunks),
                    "stats": stats,
                    "attachment_id": attachment.id
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store chunks in OpenSearch",
                    "attachment_id": attachment.id
                }
                
        except Exception as e:
            logger.error(f"Error indexing attachment {attachment.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "attachment_id": attachment.id
            }
    
    def _index_image_attachment(self, attachment, conversation_id: str) -> Dict[str, Any]:
        """Index an image attachment by generating and storing its caption."""
        try:
            logger.info(f"Processing image file: {attachment.file_name}")
            
            # Download image content from S3
            image_content = self.s3_service.get_file_content(attachment.s3_key)
            if not image_content:
                return {
                    "success": False,
                    "error": "Failed to download image from S3",
                    "attachment_id": attachment.id
                }
            
            # Generate caption for the image
            caption = self.image_captioning_service.generate_caption(
                image_content, attachment.file_type, attachment.file_name
            )
            
            if not caption:
                logger.warning(f"Failed to generate caption for {attachment.file_name}")
                return {
                    "success": True,
                    "chunk_count": 0,
                    "stats": {"skipped": True, "reason": "caption_generation_failed"},
                    "attachment_id": attachment.id
                }
            
            # Create a chunk for the image caption
            image_chunk = {
                "chunk_id": f"{attachment.id}_caption_0",
                "attachment_id": attachment.id,
                "conversation_id": conversation_id,
                "chunk_index": 0,
                "chunk_text": caption,
                "token_count": len(caption.split()),
                "filename": attachment.file_name,
                "file_type": attachment.file_type,
                "content_type": "image_caption",  # Mark as image caption
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Generate embedding for the caption
            embedding = self.embedding_service.generate_query_embedding(caption)
            image_chunk["embedding_vector"] = embedding
            
            # Store the chunk in OpenSearch
            success = self.opensearch_client.store_chunks([image_chunk])
            
            if success:
                logger.info(f"Successfully indexed image caption for {attachment.file_name}")
                return {
                    "success": True,
                    "chunk_count": 1,
                    "stats": {
                        "processed": True,
                        "caption_generated": True,
                        "caption_length": len(caption),
                        "token_count": image_chunk["token_count"]
                    },
                    "attachment_id": attachment.id
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store image caption in OpenSearch",
                    "attachment_id": attachment.id
                }
                
        except Exception as e:
            logger.error(f"Error indexing image attachment {attachment.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "attachment_id": attachment.id
            }
    
    def search_conversation_content(self, conversation_id: str, query_text: str, 
                                  previous_response: str = "") -> List[Dict[str, Any]]:
        """Search for relevant content in a conversation using semantic similarity."""
        try:
            # Combine current query with previous response for better context
            combined_query = query_text
            if previous_response:
                # Add previous response as context, but weight the current query more heavily
                combined_query = f"{query_text} [Context from previous response: {previous_response}]"
                logger.info(f"🔍 Using combined query with previous response context")
            
            logger.info(f"🔍 Semantic search - Query: '{query_text}' | Conversation: {conversation_id}")
            logger.info(f"🎯 Using threshold: {self.similarity_threshold} | Max chunks: {self.max_retrieved_chunks}")
            
            # Generate query embedding
            query_embedding = self.embedding_service.generate_query_embedding(combined_query)
            logger.debug(f"📊 Generated embedding with {len(query_embedding)} dimensions")
            
            # Perform similarity search
            results = self.opensearch_client.similarity_search(
                query_embedding,
                conversation_id,
                top_k=self.max_retrieved_chunks,
                similarity_threshold=self.similarity_threshold
            )
            
            # Apply content-type specific filtering
            filtered_results = self._filter_results_by_content_type(results, query_text)
            
            logger.info(f"✅ Found {len(results)} total chunks, {len(filtered_results)} after content filtering")
            
            # Log similarity scores for debugging
            if filtered_results:
                for i, result in enumerate(filtered_results[:3]):  # Log top 3 results
                    score = result.get('similarity_score', 0)
                    filename = result.get('filename', 'unknown')
                    content_type = result.get('content_type', 'text')
                    chunk_preview = result.get('chunk_text', '')[:50]
                    logger.info(f"  Result {i+1}: {score:.3f} | {content_type} | {filename} | {chunk_preview}...")
            else:
                logger.warning("❌ No relevant chunks found after filtering - consider lowering thresholds")
            
            # Dump search results to JSON
            self._dump_search_results(combined_query, conversation_id, filtered_results, query_embedding)
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching conversation content: {e}")
            return []
    
    def get_conversation_index_status(self, user_id: str, project_id: str, 
                                    conversation_id: str) -> Dict[str, Any]:
        """Get indexing status for a conversation."""
        try:
            # Get conversation attachments
            attachments = self.attachment_service.list_attachments(
                user_id, project_id, conversation_id
            )
            
            total_attachments = len(attachments)
            indexable_attachments = []
            indexed_attachments = []
            pending_attachments = []
            
            for att in attachments:
                if att.file_type in ["application/pdf", "text/plain"] or att.file_type.startswith("image/"):
                    indexable_attachments.append({
                        "id": att.id,
                        "file_name": att.file_name,
                        "file_type": att.file_type,
                        "is_indexed": att.is_indexed
                    })
                    
                    if att.is_indexed:
                        indexed_attachments.append(att.id)
                    else:
                        pending_attachments.append(att.id)
            
            # Check if chunks exist in OpenSearch for indexed attachments
            indexed_chunks_exist = False
            if indexed_attachments:
                # Try a simple search to see if any chunks exist
                test_results = self.opensearch_client.similarity_search(
                    [0.0] * 1536,  # Dummy vector
                    conversation_id,
                    top_k=1,
                    similarity_threshold=0.0
                )
                indexed_chunks_exist = len(test_results) > 0
            
            return {
                "conversation_id": conversation_id,
                "total_attachments": total_attachments,
                "indexable_attachments": len(indexable_attachments),
                "indexed_attachments": len(indexed_attachments),
                "pending_attachments": len(pending_attachments),
                "has_indexed_content": indexed_chunks_exist,
                "indexing_supported": len(indexable_attachments) > 0,
                "attachment_details": indexable_attachments
            }
            
        except Exception as e:
            logger.error(f"Error checking index status: {e}")
            return {
                "conversation_id": conversation_id,
                "error": str(e),
                "has_indexed_content": False
            }
    
    def reindex_conversation(self, user_id: str, project_id: str, 
                           conversation_id: str) -> Dict[str, Any]:
        """Reindex all attachments for a conversation (clears existing chunks first)."""
        try:
            # Delete existing chunks
            self.opensearch_client.delete_conversation_chunks(conversation_id)
            logger.info(f"Cleared existing chunks for conversation {conversation_id}")
            
            # Reindex all attachments
            return self.index_conversation_attachments(user_id, project_id, conversation_id)
            
        except Exception as e:
            logger.error(f"Error reindexing conversation: {e}")
            return {
                "status": "error",
                "error": str(e),
                "conversation_id": conversation_id
            }
    
    def delete_conversation_index(self, conversation_id: str) -> bool:
        """Delete all indexed content for a conversation."""
        try:
            return self.opensearch_client.delete_conversation_chunks(conversation_id)
        except Exception as e:
            logger.error(f"Error deleting conversation index: {e}")
            return False
    
    def delete_attachment_index(self, attachment_id: str) -> bool:
        """Delete all indexed content for a specific attachment."""
        try:
            success = self.opensearch_client.delete_attachment_chunks(attachment_id)
            if success:
                logger.info(f"Successfully deleted indexed content for attachment {attachment_id}")
            else:
                logger.warning(f"No indexed content found for attachment {attachment_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting attachment index: {e}")
            return False
    
    def delete_specific_attachment_chunks(self, conversation_id: str, attachment_id: str) -> bool:
        """Delete indexed chunks for a specific attachment within a conversation."""
        try:
            success = self.opensearch_client.delete_specific_chunks(conversation_id, attachment_id)
            if success:
                logger.info(f"Successfully deleted chunks for attachment {attachment_id} in conversation {conversation_id}")
            else:
                logger.warning(f"No chunks found for attachment {attachment_id} in conversation {conversation_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting specific attachment chunks: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all indexing components."""
        try:
            opensearch_health = self.opensearch_client.health_check()
            openai_health = self.embedding_service.test_connection()
            
            return {
                "status": "healthy" if opensearch_health["connected"] and openai_health else "unhealthy",
                "opensearch": opensearch_health,
                "openai_embeddings": {
                    "connected": openai_health,
                    "model": self.embedding_service.model
                },
                "indexing_config": {
                    "chunk_size": self.text_processor.chunk_size,
                    "chunk_overlap": self.text_processor.chunk_overlap,
                    "similarity_threshold": self.similarity_threshold,
                    "image_caption_threshold": self.image_caption_threshold,
                    "max_retrieved_chunks": self.max_retrieved_chunks
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def cleanup_orphaned_chunks(self, user_id: str, project_id: str, conversation_id: str) -> Dict[str, Any]:
        """Find and clean up chunks that have no corresponding attachment."""
        try:
            # Get current attachments
            attachments = self.attachment_service.list_attachments(user_id, project_id, conversation_id)
            current_attachment_ids = {att.id for att in attachments}
            
            # Get all indexed chunks for this conversation
            all_chunks_response = self.opensearch_client.client.search(
                index=self.opensearch_client.index_name,
                body={
                    "query": {"term": {"conversation_id": conversation_id}},
                    "size": 1000,
                    "_source": ["attachment_id"]
                }
            )
            
            indexed_attachment_ids = set()
            for hit in all_chunks_response['hits']['hits']:
                indexed_attachment_ids.add(hit['_source']['attachment_id'])
            
            # Find orphaned attachment IDs
            orphaned_ids = indexed_attachment_ids - current_attachment_ids
            
            cleaned_count = 0
            if orphaned_ids:
                logger.info(f"Found {len(orphaned_ids)} orphaned attachment chunks in conversation {conversation_id}")
                
                for orphaned_id in orphaned_ids:
                    success = self.delete_specific_attachment_chunks(conversation_id, orphaned_id)
                    if success:
                        cleaned_count += 1
            
            return {
                "conversation_id": conversation_id,
                "orphaned_attachments_found": len(orphaned_ids),
                "orphaned_attachments_cleaned": cleaned_count,
                "current_attachments": len(current_attachment_ids),
                "indexed_attachments": len(indexed_attachment_ids)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned chunks: {e}")
            return {
                "conversation_id": conversation_id,
                "error": str(e)
            }

    def retry_failed_indexing(self, user_id: str, project_id: str, conversation_id: str) -> Dict[str, Any]:
        """Retry indexing for attachments that failed to index.
        
        Args:
            user_id: The ID of the user who owns the conversation
            project_id: The ID of the project the conversation belongs to
            conversation_id: The ID of the conversation
            
        Returns:
            Dict containing retry results
        """
        try:
            # Get all attachments for the conversation
            attachments = self.attachment_service.list_attachments(user_id, project_id, conversation_id)
            
            # Find attachments that should be indexed but aren't
            failed_attachments = []
            for att in attachments:
                is_indexable = (
                    att.file_type in ["application/pdf", "text/plain"] or 
                    att.file_type.startswith("image/")
                )
                
                if is_indexable and not att.is_indexed:
                    failed_attachments.append(att)
            
            if not failed_attachments:
                return {
                    "conversation_id": conversation_id,
                    "message": "No failed attachments found to retry",
                    "retry_count": 0
                }
            
            logger.info(f"Found {len(failed_attachments)} failed attachments to retry indexing")
            
            retry_results = []
            successful_retries = 0
            
            for attachment in failed_attachments:
                try:
                    logger.info(f"Retrying indexing for {attachment.file_name}")
                    
                    # Attempt to index the attachment
                    result = self._index_single_attachment(attachment, conversation_id)
                    
                    if result["success"]:
                        # Update the attachment status to indexed
                        self.attachment_service.update_attachment_index_status(
                            user_id, project_id, conversation_id, attachment.id, True
                        )
                        successful_retries += 1
                        logger.info(f"Successfully retried indexing for {attachment.file_name}")
                    else:
                        logger.warning(f"Retry failed for {attachment.file_name}: {result.get('error', 'Unknown error')}")
                    
                    retry_results.append({
                        "attachment_id": attachment.id,
                        "file_name": attachment.file_name,
                        "success": result["success"],
                        "chunk_count": result.get("chunk_count", 0),
                        "error": result.get("error")
                    })
                    
                except Exception as e:
                    logger.error(f"Error retrying indexing for {attachment.file_name}: {e}")
                    retry_results.append({
                        "attachment_id": attachment.id,
                        "file_name": attachment.file_name,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "conversation_id": conversation_id,
                "total_retries": len(failed_attachments),
                "successful_retries": successful_retries,
                "failed_retries": len(failed_attachments) - successful_retries,
                "retry_results": retry_results
            }
            
        except Exception as e:
            logger.error(f"Error retrying failed indexing: {e}")
            return {
                "conversation_id": conversation_id,
                "error": str(e)
            }

    def get_indexing_statistics(self, user_id: str, project_id: str, conversation_id: str) -> Dict[str, Any]:
        """Get detailed indexing statistics for a conversation.
        
        Args:
            user_id: The ID of the user who owns the conversation
            project_id: The ID of the project the conversation belongs to
            conversation_id: The ID of the conversation
            
        Returns:
            Dict containing detailed indexing statistics
        """
        try:
            # Get all attachments
            attachments = self.attachment_service.list_attachments(user_id, project_id, conversation_id)
            
            stats = {
                "conversation_id": conversation_id,
                "total_attachments": len(attachments),
                "indexable_attachments": 0,
                "indexed_attachments": 0,
                "pending_attachments": 0,
                "non_indexable_attachments": 0,
                "total_chunks": 0,
                "file_type_breakdown": {},
                "indexing_status": []
            }
            
            # Analyze each attachment
            for att in attachments:
                is_indexable = (
                    att.file_type in ["application/pdf", "text/plain"] or 
                    att.file_type.startswith("image/")
                )
                
                # File type breakdown
                if att.file_type not in stats["file_type_breakdown"]:
                    stats["file_type_breakdown"][att.file_type] = {
                        "count": 0,
                        "indexed": 0,
                        "pending": 0
                    }
                
                stats["file_type_breakdown"][att.file_type]["count"] += 1
                
                if is_indexable:
                    stats["indexable_attachments"] += 1
                    
                    if att.is_indexed:
                        stats["indexed_attachments"] += 1
                        stats["file_type_breakdown"][att.file_type]["indexed"] += 1
                    else:
                        stats["pending_attachments"] += 1
                        stats["file_type_breakdown"][att.file_type]["pending"] += 1
                else:
                    stats["non_indexable_attachments"] += 1
                
                # Individual attachment status
                stats["indexing_status"].append({
                    "id": att.id,
                    "file_name": att.file_name,
                    "file_type": att.file_type,
                    "file_size": att.file_size,
                    "is_indexable": is_indexable,
                    "is_indexed": att.is_indexed,
                    "created_at": att.created_at
                })
            
            # Get total chunk count from OpenSearch
            try:
                chunks_response = self.opensearch_client.client.search(
                    index=self.opensearch_client.index_name,
                    body={
                        "query": {"term": {"conversation_id": conversation_id}},
                        "size": 0,
                        "aggs": {
                            "total_chunks": {"value_count": {"field": "chunk_id"}}
                        }
                    }
                )
                stats["total_chunks"] = chunks_response["aggregations"]["total_chunks"]["value"]
            except Exception as e:
                logger.warning(f"Could not get chunk count from OpenSearch: {e}")
                stats["total_chunks"] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting indexing statistics: {e}")
            return {
                "conversation_id": conversation_id,
                "error": str(e)
            }

    def _filter_results_by_content_type(self, results: List[Dict[str, Any]], query_text: str) -> List[Dict[str, Any]]:
        """Filter results based on content type and apply appropriate thresholds.
        
        Args:
            results: List of search results from OpenSearch
            query_text: The original query text for context
            
        Returns:
            Filtered list of results with content-type specific thresholds applied
        """
        filtered_results = []
        
        for result in results:
            content_type = result.get('content_type', 'text')
            similarity_score = result.get('similarity_score', 0.0)
            
            # Apply different thresholds based on content type
            if content_type == 'image_caption':
                # Use higher threshold for image captions to ensure relevance
                if similarity_score >= self.image_caption_threshold:
                    filtered_results.append(result)
                    logger.info(f"✅ Image caption passed threshold: {similarity_score:.3f} >= {self.image_caption_threshold} | {result.get('filename', 'unknown')}")
                else:
                    logger.info(f"❌ Image caption filtered out: {similarity_score:.3f} < {self.image_caption_threshold} | {result.get('filename', 'unknown')}")
            
            elif content_type == 'text':
                # Use standard threshold for text content
                if similarity_score >= self.similarity_threshold:
                    filtered_results.append(result)
                else:
                    logger.info(f"❌ Text content filtered out: {similarity_score:.3f} < {self.similarity_threshold}")
            
            else:
                # For any other content types, use standard threshold
                if similarity_score >= self.similarity_threshold:
                    filtered_results.append(result)
                    
        # Log filtering summary
        total_results = len(results)
        filtered_count = len(filtered_results)
        image_captions = len([r for r in results if r.get('content_type') == 'image_caption'])
        filtered_images = len([r for r in filtered_results if r.get('content_type') == 'image_caption'])
        
        logger.info(f"🔍 Content filtering summary: {total_results} → {filtered_count} results")
        if image_captions > 0:
            logger.info(f"🖼️ Image captions: {image_captions} found, {filtered_images} passed stricter threshold ({self.image_caption_threshold})")
        
        return filtered_results

    def set_image_caption_threshold(self, threshold: float) -> bool:
        """Set the similarity threshold for image captions.
        
        Args:
            threshold: New threshold value (0.0 to 1.0)
            
        Returns:
            True if threshold was set successfully
        """
        try:
            if 0.0 <= threshold <= 1.0:
                old_threshold = self.image_caption_threshold
                self.image_caption_threshold = threshold
                logger.info(f"🖼️ Updated image caption threshold: {old_threshold} → {threshold}")
                return True
            else:
                logger.error(f"Invalid threshold value: {threshold}. Must be between 0.0 and 1.0")
                return False
        except Exception as e:
            logger.error(f"Error setting image caption threshold: {e}")
            return False

    def get_filtering_config(self) -> Dict[str, Any]:
        """Get current filtering configuration.
        
        Returns:
            Dict containing current threshold configurations
        """
        return {
            "text_similarity_threshold": self.similarity_threshold,
            "image_caption_threshold": self.image_caption_threshold,
            "max_retrieved_chunks": self.max_retrieved_chunks,
            "filtering_enabled": True
        }