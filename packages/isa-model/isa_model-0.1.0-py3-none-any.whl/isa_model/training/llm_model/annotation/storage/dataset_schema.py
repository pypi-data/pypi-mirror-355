# app/services/llm_model/annotation/dataset/dataset_schema.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from bson import ObjectId

class DatasetType(str, Enum):
    SFT = "sft"
    RLHF = "rlhf"

class DatasetStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class DatasetFiles(BaseModel):
    train: str
    eval: Optional[str]
    test: Optional[str]

class DatasetStats(BaseModel):
    total_examples: int
    avg_length: Optional[float]
    num_conversations: Optional[int]
    additional_metrics: Optional[Dict] = {}

class Dataset(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    name: str
    type: DatasetType
    version: str
    storage_path: str
    files: DatasetFiles
    stats: DatasetStats
    source_annotations: List[str]
    created_at: datetime
    status: DatasetStatus
    metadata: Optional[Dict] = {}

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True