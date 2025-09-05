from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class LLMResponse(BaseModel):
    """Schema for LLM classification response"""
    filtered: bool
    priority: str = Field(..., regex="^(High Priority|Medium Priority|Low Priority)$")
    classification: str = Field(..., regex="^(Support|Query|Request|Help)$")
    sentiment: str = Field(..., regex="^(Positive|Neutral|Negative)$")
    suggested_responses: List[str] = Field(default_factory=list, max_items=3)
    other_details: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EmailSearchRequest(BaseModel):
    """Schema for email search request"""
    query: str
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None

class EmailFilterRequest(BaseModel):
    """Schema for email filtering"""
    priority: Optional[List[str]] = None
    sentiment: Optional[List[str]] = None
    classification: Optional[List[str]] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    sender: Optional[str] = None
    filtered: Optional[bool] = None
