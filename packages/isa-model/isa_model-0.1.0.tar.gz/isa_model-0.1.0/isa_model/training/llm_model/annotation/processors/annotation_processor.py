from typing import Dict, Any, List
from datetime import datetime
from app.config.config_manager import config_manager
from app.services.training.llm_model.annotation.annotation_schema import AnnotationFeedback, RatingScale, AnnotationAspects
from bson.objectid import ObjectId
from app.services.training.llm_model.annotation.storage.dataset_manager import DatasetManager

class AnnotationProcessor:
    def __init__(self):
        self.logger = config_manager.get_logger(__name__)
        self.dataset_manager = DatasetManager()
        self.batch_size = 1000  # Configure as needed
    
    async def process_queue(self) -> None:
        """Process pending items and create datasets"""
        db = await config_manager.get_db('mongodb')
        queue = db['training_queue']
        
        # Process SFT items
        sft_items = await self._get_pending_items("sft")
        if len(sft_items) >= self.batch_size:
            await self._create_sft_dataset(sft_items)
        
        # Process RLHF items
        rlhf_items = await self._get_pending_items("rlhf")
        if len(rlhf_items) >= self.batch_size:
            await self._create_rlhf_dataset(rlhf_items)

    async def _create_sft_dataset(self, items: List[Dict[str, Any]]):
        """Create and upload SFT dataset"""
        dataset = await self.dataset_manager.create_dataset(
            name=f"sft_dataset_v{datetime.now().strftime('%Y%m%d')}",
            type="sft",
            version=datetime.now().strftime("%Y%m%d"),
            source_annotations=[item["annotation_id"] for item in items]
        )
        
        formatted_data = [
            await self._process_sft_item(item) 
            for item in items
        ]
        
        await self.dataset_manager.upload_dataset_file(
            dataset.id,
            formatted_data
        )

    async def _process_sft_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process item for SFT dataset generation
        Format follows HF conversation format for SFT training
        """
        db = await config_manager.get_db('mongodb')
        annotations = db['annotations']
        
        # Get full annotation context
        annotation = await annotations.find_one({"_id": ObjectId(item["annotation_id"])})
        target_item = next(i for i in annotation["items"] if i["item_id"] == item["item_id"])
        
        # Format as conversation
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that provides accurate and relevant information."
            },
            {
                "role": "user",
                "content": target_item["input"]["messages"][0]["content"]
            },
            {
                "role": "assistant", 
                "content": target_item["output"]["content"]
            }
        ]

        return {
            "messages": messages,
            "metadata": {
                "rating": item["feedback"]["rating"],
                "aspects": item["feedback"]["aspects"],
                "category": item["feedback"]["category"]
            }
        }

    async def _process_rlhf_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process item for RLHF dataset generation
        Format follows preference pairs structure for RLHF training
        """
        db = await config_manager.get_db('mongodb')
        annotations = db['annotations']
        
        # Get full annotation context
        annotation = await annotations.find_one({"_id": ObjectId(item["annotation_id"])})
        target_item = next(i for i in annotation["items"] if i["item_id"] == item["item_id"])
        
        # Format as preference pairs
        return {
            "prompt": target_item["input"]["messages"][0]["content"],
            "chosen": item["feedback"]["better_response"]["content"],
            "rejected": target_item["output"]["content"],
            "metadata": {
                "reason": item["feedback"]["better_response"]["reason"],
                "category": item["feedback"]["category"]
            }
        }

    async def get_training_data(
        self,
        data_type: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Retrieve formatted training data"""
        db = await config_manager.get_db('mongodb')
        training_data = db['training_data']
        
        data = await training_data.find(
            {"type": data_type}
        ).limit(limit).to_list(length=limit)
        
        if data_type == "sft":
            return [item["data"]["messages"] for item in data]
        else:  # rlhf
            return [{
                "prompt": item["data"]["prompt"],
                "chosen": item["data"]["chosen"],
                "rejected": item["data"]["rejected"]
            } for item in data]