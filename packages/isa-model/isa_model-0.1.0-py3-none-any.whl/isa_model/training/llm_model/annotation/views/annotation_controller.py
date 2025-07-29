# app/services/llm_model/tracing/annotation/annotation_controller.py
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from app.config.config_manager import config_manager
from app.services.training.llm_model.annotation.annotation_schema import AnnotationFeedback, RatingScale
from app.services.training.llm_model.annotation.storage.dataset_manager import DatasetManager


class AnnotationController:
    def __init__(self):
        self.logger = config_manager.get_logger(__name__)
        
    async def get_pending_annotations(
        self, 
        project_name: str,
        category: Optional[str] = None,
        min_rating: Optional[int] = None,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get filtered list of pending annotations"""
        db = await config_manager.get_db('mongodb')
        collection = db['annotations']
        
        # Build query with filters
        query = {"status": "pending", "project_name": project_name}
        if category:
            query["annotation_type"] = category
        if min_rating:
            query["items.feedback.rating"] = {"$gte": min_rating}
            
        annotations = await collection.find(query)\
            .sort("created_at", -1)\
            .skip((page - 1) * limit)\
            .limit(limit)\
            .to_list(length=limit)
            
        return {
            "annotations": annotations,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": await collection.count_documents(query)
            }
        }

    async def submit_annotation(
        self,
        annotation_id: str,
        item_id: str,
        feedback: AnnotationFeedback,
        annotator_id: str
    ) -> Dict[str, Any]:
        """Submit and process annotation feedback"""
        db = await config_manager.get_db('mongodb')
        collection = db['annotations']
        
        # Determine if annotation should be selected for training
        is_selected = self._evaluate_for_training(feedback)
        feedback_dict = feedback.dict()
        feedback_dict["is_selected_for_training"] = is_selected
        
        # Update annotation
        result = await collection.update_one(
            {
                "_id": ObjectId(annotation_id),
                "items.item_id": item_id
            },
            {
                "$set": {
                    "items.$.feedback": feedback_dict,
                    "items.$.status": "completed",
                    "items.$.annotated_at": datetime.utcnow().isoformat(),
                    "items.$.annotator_id": annotator_id,
                    "items.$.training_status": "pending" if is_selected else "none"
                }
            }
        )
        
        # Process for training if selected
        if is_selected:
            await self._queue_for_training(annotation_id, item_id, feedback)
        
        return {
            "status": "success",
            "selected_for_training": is_selected,
            "message": "Annotation submitted successfully"
        }

    def _evaluate_for_training(self, feedback: AnnotationFeedback) -> bool:
        """Evaluate if annotation should be used for training"""
        # Select for SFT if rating is excellent and aspects are positive
        if feedback.rating == RatingScale.EXCELLENT:
            aspects = feedback.aspects
            if all([
                aspects.factually_correct,
                aspects.relevant,
                not aspects.harmful,
                not aspects.biased
            ]):
                return True
        
        # Select for RLHF if better response is provided
        if feedback.better_response:
            return True
            
        return False

    async def _queue_for_training(
        self,
        annotation_id: str,
        item_id: str,
        feedback: AnnotationFeedback
    ):
        """Queue selected annotations for training data generation"""
        db = await config_manager.get_db('mongodb')
        training_queue = db['training_queue']
        
        await training_queue.insert_one({
            "annotation_id": annotation_id,
            "item_id": item_id,
            "type": "sft" if feedback.rating == RatingScale.EXCELLENT else "rlhf",
            "feedback": feedback.dict(),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        })

class DatasetPreparationProcessor:
    def __init__(self):
        self.logger = config_manager.get_logger(__name__)
        self.dataset_manager = DatasetManager()
        self.batch_size = 1000  # Configure as needed
    
    async def process_annotation_queue(self) -> None:
        """Process pending annotations and prepare datasets"""
        db = await config_manager.get_db('mongodb')
        annotation_queue = db['dataset_preparation_queue']
        
        # Process items for SFT dataset
        sft_items = await self._get_pending_annotations("sft")
        if len(sft_items) >= self.batch_size:
            await self._create_sft_dataset(sft_items)
        
        # Process items for RLHF dataset
        rlhf_items = await self._get_pending_annotations("rlhf")
        if len(rlhf_items) >= self.batch_size:
            await self._create_rlhf_dataset(rlhf_items)

    async def _get_pending_annotations(self, dataset_type: str) -> List[Dict[str, Any]]:
        """Get pending annotations for dataset preparation"""
        db = await config_manager.get_db('mongodb')
        queue = db['dataset_preparation_queue']
        
        return await queue.find({
            "status": "pending",
            "dataset_type": dataset_type
        }).to_list(length=self.batch_size)