# test_annotation_flow.py
import os 
os.environ["ENV"] = "local"

import asyncio
from datetime import datetime
from bson import ObjectId
from app.services.llm_model.annotation.views.annotation_controller import AnnotationController
from app.services.llm_model.annotation.processors.annotation_processor import AnnotationProcessor
from app.services.llm_model.annotation.annotation_schema import (
    AnnotationFeedback, 
    RatingScale, 
    AnnotationType,
    AnnotationAspects,
    BetterResponse
)
from app.config.config_manager import config_manager 

async def setup_test_data():
    """Setup initial test data in MongoDB"""
    db = await config_manager.get_db('mongodb')
    
    # Create a test annotation
    test_annotation = {
        "_id": ObjectId(),
        "project_name": "test_project",
        "items": [{
            "item_id": "test_item_1",
            "input": {
                "messages": [{
                    "role": "user",
                    "content": "What is the capital of France?"
                }]
            },
            "output": {
                "content": "The capital of France is Paris."
            },
            "status": "pending"
        }],
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db['annotations'].insert_one(test_annotation)
    return test_annotation

async def test_annotation_flow():
    """Test the complete annotation flow"""
    try:
        # Initialize controllers
        annotation_controller = AnnotationController()
        annotation_processor = AnnotationProcessor()
        
        # Setup test data
        test_data = await setup_test_data()
        annotation_id = str(test_data["_id"])
        item_id = test_data["items"][0]["item_id"]
        
        print("1. Created test annotation")
        
        # Create test feedback
        feedback = AnnotationFeedback(
            rating=RatingScale.EXCELLENT,
            category=AnnotationType.ACCURACY,
            aspects=AnnotationAspects(
                factually_correct=True,
                relevant=True,
                harmful=False,
                biased=False,
                complete=True,
                efficient=True
            ),
            better_response=BetterResponse(
                content="Paris is the capital city of France, known for its iconic Eiffel Tower.",
                reason="Added more context and detail"
            ),
            comment="Good response, but could be more detailed"
        )
        
        # Submit annotation
        result = await annotation_controller.submit_annotation(
            annotation_id=annotation_id,
            item_id=item_id,
            feedback=feedback,
            annotator_id="test_annotator"
        )
        
        print("2. Submitted annotation:", result)
        
        # Process annotation queue
        await annotation_processor.process_queue()
        print("3. Processed annotation queue")
        
        # Verify dataset creation
        db = await config_manager.get_db('mongodb')
        datasets = await db['training_datasets'].find().to_list(length=10)
        
        print("\nCreated Datasets:")
        for dataset in datasets:
            print(f"- {dataset['name']} ({dataset['type']})")
            print(f"  Status: {dataset['status']}")
            print(f"  Examples: {dataset['stats']['total_examples']}")
            
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    # Run the test
    print("Starting annotation flow test...")
    asyncio.run(test_annotation_flow())