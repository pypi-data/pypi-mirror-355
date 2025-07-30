"""
Request and response schemas for BubbleTea
"""

from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field
from .components import Component


class ImageInput(BaseModel):
    """Image input that can be either a URL or base64 encoded data"""
    url: Optional[str] = Field(None, description="URL of the image")
    base64: Optional[str] = Field(None, description="Base64 encoded image data")
    mime_type: Optional[str] = Field(None, description="MIME type of the image (e.g., image/jpeg, image/png)")


class ComponentChatRequest(BaseModel):
    """Incoming chat request from BubbleTea"""
    type: Literal["user"]
    message: str
    images: Optional[List[ImageInput]] = Field(None, description="Optional images to include with the message")


class ComponentChatResponse(BaseModel):
    """Non-streaming response containing list of components"""
    responses: List[Component]