
"""
在这里定义（使用Pydantic或Protobuf）一个标准的 ChatMessageSchema，它包含 role: str, content: Optional[str], 
tool_calls: Optional[List[ToolCallSchema]], tool_call_id: Optional[str] 等字段。
UnifiedRestInvokeRequest (或gRPC的 UnifiedRequest) 中的 task_specific_payload 字段，在处理聊天任务时，
其内部的 "messages" 键对应的值就是 List[ChatMessageSchema]。

"""

from pydantic import BaseModel

class UnifiedChatResponse(BaseModel):
    pass 

class UnifiedTextResponse(BaseModel):
    pass
