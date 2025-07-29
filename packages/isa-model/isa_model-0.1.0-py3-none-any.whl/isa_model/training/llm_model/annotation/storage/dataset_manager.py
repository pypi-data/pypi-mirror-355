# app/services/llm_model/annotation/dataset/dataset_manager.py
from typing import Dict, Any, List
from datetime import datetime
import json
import io
from app.config.config_manager import config_manager
from .dataset_schema import Dataset, DatasetType, DatasetStatus, DatasetFiles, DatasetStats
from bson import ObjectId

class DatasetManager:
    def __init__(self):
        self.logger = config_manager.get_logger(__name__)
        self.minio_client = None
        self.bucket_name = "training-datasets"

    async def _ensure_minio_client(self):
        if not self.minio_client:
            self.minio_client = await config_manager.get_storage_client()

    async def create_dataset(
        self, 
        name: str,
        type: DatasetType,
        version: str,
        source_annotations: List[str]
    ) -> Dataset:
        """Create a new dataset record"""
        db = await config_manager.get_db('mongodb')
        collection = db['training_datasets']
        
        dataset = Dataset(
            name=name,
            type=type,
            version=version,
            storage_path=f"datasets/{type.value}/{version}",
            files=DatasetFiles(
                train="train.jsonl",
                eval=None,
                test=None
            ),
            stats=DatasetStats(
                total_examples=0,
                avg_length=0.0,
                num_conversations=0,
                additional_metrics={}
            ),
            source_annotations=source_annotations,
            created_at=datetime.utcnow(),
            status=DatasetStatus.PENDING,
            metadata={}
        )
        
        result = await collection.insert_one(dataset.dict(exclude={'id'}))
        return Dataset(**{**dataset.dict(), '_id': result.inserted_id})

    async def upload_dataset_file(
        self,
        dataset_id: str,
        data: List[Dict[str, Any]],
        file_type: str = "train"
    ) -> bool:
        """Upload dataset to MinIO"""
        try:
            await self._ensure_minio_client()
            db = await config_manager.get_db('mongodb')
            
            object_id = ObjectId(dataset_id)
            dataset = await db['training_datasets'].find_one({"_id": object_id})
            
            if not dataset:
                self.logger.error(f"Dataset not found with id: {dataset_id}")
                return False
            
            # Convert to JSONL
            buffer = io.StringIO()
            for item in data:
                buffer.write(json.dumps(item) + "\n")
            
            storage_path = dataset['storage_path'].rstrip('/')
            file_path = f"{storage_path}/{file_type}.jsonl"
            
            buffer_value = buffer.getvalue().encode()
            
            self.logger.debug(f"Uploading to MinIO path: {file_path}")
            
            self.minio_client.put_object(
                self.bucket_name,
                file_path,
                io.BytesIO(buffer_value),
                len(buffer_value)
            )
            
            avg_length = sum(len(str(item)) for item in data) / len(data) if data else 0
            
            await db['training_datasets'].update_one(
                {"_id": object_id},
                {
                    "$set": {
                        f"files.{file_type}": f"{file_type}.jsonl",
                        "stats.total_examples": len(data),
                        "stats.avg_length": avg_length,
                        "stats.num_conversations": len(data),
                        "status": DatasetStatus.READY
                    }
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload dataset: {e}")
            return False

    async def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """Get dataset information"""
        try:
            db = await config_manager.get_db('mongodb')
            object_id = ObjectId(dataset_id)  # Convert string ID to ObjectId
            dataset = await db['training_datasets'].find_one({"_id": object_id})
            
            if not dataset:
                self.logger.error(f"Dataset not found with id: {dataset_id}")
                return None
            
            # Convert ObjectId to string for JSON serialization
            dataset['_id'] = str(dataset['_id'])
            return dataset
            
        except Exception as e:
            self.logger.error(f"Failed to get dataset info: {e}")
            return None