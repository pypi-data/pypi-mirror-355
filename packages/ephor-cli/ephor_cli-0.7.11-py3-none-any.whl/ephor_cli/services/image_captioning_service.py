import base64
import logging
from typing import Optional, Dict, Any
import requests
import json

logger = logging.getLogger(__name__)

class ImageCaptioningService:
    """Service for generating captions/descriptions for images."""
    
    def __init__(self):
        # You can configure different captioning models here
        self.model_type = "openai"  # or "huggingface", "local", etc.
        
    def generate_caption(self, image_data: bytes, file_type: str, filename: str) -> Optional[str]:
        """Generate a caption for an image.
        
        Args:
            image_data: Raw image bytes
            file_type: MIME type of the image (e.g., 'image/jpeg')
            filename: Original filename of the image
            
        Returns:
            Generated caption string or None if failed
        """
        try:
            if self.model_type == "openai":
                return self._caption_with_openai(image_data, file_type, filename)
            elif self.model_type == "huggingface":
                return self._caption_with_huggingface(image_data, file_type, filename)
            else:
                logger.warning(f"Unknown captioning model type: {self.model_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating caption for {filename}: {e}")
            return None
    
    def _caption_with_openai(self, image_data: bytes, file_type: str, filename: str) -> Optional[str]:
        """Generate caption using OpenAI Vision API."""
        try:
            import openai
            from openai import OpenAI
            
            client = OpenAI()
            
            # Encode image as base64
            b64_image = base64.b64encode(image_data).decode('utf-8')
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please provide a detailed but concise description of this image. Focus on the main subjects, objects, activities, and context. This description will be used for semantic search, so include relevant keywords."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{file_type};base64,{b64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            caption = response.choices[0].message.content
            logger.info(f"Generated caption for {filename}: {caption[:100]}...")
            return caption
            
        except Exception as e:
            logger.error(f"OpenAI captioning failed for {filename}: {e}")
            return None
    
    def _caption_with_huggingface(self, image_data: bytes, file_type: str, filename: str) -> Optional[str]:
        """Generate caption using Hugging Face models."""
        try:
            # Example implementation with Hugging Face Inference API
            # You would need to configure your HF API key and model
            
            import io
            from PIL import Image
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # This is a placeholder - you'd implement actual HF API call here
            # For example, using BLIP or other vision-language models
            
            # Placeholder caption
            caption = f"Image analysis for {filename} - implement HF model here"
            logger.info(f"Generated HF caption for {filename}")
            return caption
            
        except Exception as e:
            logger.error(f"Hugging Face captioning failed for {filename}: {e}")
            return None
    
    def generate_caption_with_metadata(self, image_data: bytes, file_type: str, filename: str) -> Dict[str, Any]:
        """Generate caption with additional metadata.
        
        Returns:
            Dictionary containing caption, confidence, model used, etc.
        """
        caption = self.generate_caption(image_data, file_type, filename)
        
        return {
            "caption": caption,
            "filename": filename,
            "file_type": file_type,
            "model_type": self.model_type,
            "success": caption is not None
        } 