"""
EchoForge API Schemas

This module defines Pydantic schemas for API requests and responses.
"""

from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


class Gender(str, Enum):
    """Gender enum for character voices."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class CharacterVoice(BaseModel):
    """Schema for a character voice."""
    id: int
    name: str
    description: Optional[str] = None
    gender: Gender = Gender.NEUTRAL
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class GenerationOptions(BaseModel):
    """Options for voice generation."""
    temperature: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(50, ge=1, le=100)
    style: Optional[str] = None
    
    @validator("temperature")
    def validate_temperature(cls, v):
        """Validate temperature range."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v
    
    @validator("top_k")
    def validate_top_k(cls, v):
        """Validate top_k range."""
        if v < 1:
            raise ValueError("top_k must be at least 1")
        return v


class GenerationRequest(BaseModel):
    """Request for voice generation."""
    text: str = Field(..., min_length=1, max_length=1000)
    speaker_id: int = Field(1, ge=1)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator("text")
    def validate_text(cls, v):
        """Validate text content."""
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v


class GenerationResponse(BaseModel):
    """Response for voice generation."""
    task_id: str
    status: str = "pending"


class TaskStatus(str, Enum):
    """Status enum for generation tasks."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatusResponse(BaseModel):
    """Response for task status."""
    task_id: str
    status: TaskStatus
    created_at: float
    completed_at: Optional[float] = None
    result_url: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class HealthResponse(BaseModel):
    """Response for health check."""
    status: str
    version: str
    cuda: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 