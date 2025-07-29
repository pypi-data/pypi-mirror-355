# app/services/llm_model/tracing/annotation/annotation_schema.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class AnnotationType(str, Enum):
    ACCURACY = "accuracy"
    HELPFULNESS = "helpfulness"
    TOXICITY = "toxicity"
    CUSTOM = "custom"

class RatingScale(int, Enum):
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4

class AnnotationAspects(BaseModel):
    factually_correct: bool = True
    relevant: bool = True
    harmful: bool = False
    biased: bool = False
    complete: bool = True
    efficient: bool = True

class BetterResponse(BaseModel):
    content: str
    reason: Optional[str]
    metadata: Optional[Dict[str, Any]] = {}

class AnnotationFeedback(BaseModel):
    rating: RatingScale
    category: AnnotationType
    aspects: AnnotationAspects
    better_response: Optional[BetterResponse]
    comment: Optional[str]
    metadata: Optional[Dict[str, Any]] = {}
    is_selected_for_training: bool = False  

class ItemAnnotation(BaseModel):
    item_id: str
    feedback: Optional[AnnotationFeedback]
    status: str = "pending"  
    annotated_at: Optional[datetime]
    annotator_id: Optional[str]
    training_status: Optional[str] = None  