"""
BubbleTea component classes for building rich chatbot responses
"""

from typing import Literal, Optional, Union
from pydantic import BaseModel


class Text(BaseModel):
    """A text component for displaying plain text messages"""
    type: Literal["text"] = "text"
    content: str

    def __init__(self, content: str):
        super().__init__(content=content)


class Image(BaseModel):
    """An image component for displaying images"""
    type: Literal["image"] = "image"
    url: str
    alt: Optional[str] = None

    def __init__(self, url: str, alt: Optional[str] = None):
        super().__init__(url=url, alt=alt)


class Markdown(BaseModel):
    """A markdown component for rich text formatting"""
    type: Literal["markdown"] = "markdown"
    content: str

    def __init__(self, content: str):
        super().__init__(content=content)


class Done(BaseModel):
    """A done component to signal end of streaming"""
    type: Literal["done"] = "done"


# Type alias for all components
Component = Union[Text, Image, Markdown, Done]