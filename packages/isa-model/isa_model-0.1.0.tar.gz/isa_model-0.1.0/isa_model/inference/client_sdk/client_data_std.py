# Inside UniversalInferenceClient.chat method
processed_messages = []
for user_msg in messages: # messages is what the end-user provided to the SDK
    if isinstance(user_msg, dict) and "role" in user_msg and "content" in user_msg:
        processed_messages.append(user_msg)
    elif isinstance(user_msg, BaseMessage): # If user passes LangChain messages directly
        # Serialize BaseMessage to our standard dict format
        msg_dict = {"role": "", "content": user_msg.content}
        if isinstance(user_msg, HumanMessage):
            msg_dict["role"] = "user"
        elif isinstance(user_msg, AIMessage):
            msg_dict["role"] = "assistant"
            if hasattr(user_msg, "tool_calls") and user_msg.tool_calls:
                 # Serialize tool_calls to a list of dicts
                msg_dict["tool_calls"] = [
                    {"id": tc.get("id"), "type": "function", "function": {"name": tc.get("name"), "arguments": json.dumps(tc.get("args", {}))}}
                    for tc in user_msg.tool_calls # Assuming user_msg.tool_calls are already dicts or serializable
                ]
        elif isinstance(user_msg, SystemMessage):
            msg_dict["role"] = "system"
        elif isinstance(user_msg, ToolMessage):
            msg_dict["role"] = "tool"
            msg_dict["tool_call_id"] = user_msg.tool_call_id
        else:
            # Handle other BaseMessage types or raise error
            pass
        processed_messages.append(msg_dict)
    # ... (add more flexible input handling if needed, e.g., a list of tuples)
    else:
        raise ValueError("Unsupported message format in chat method input.")

# task_specific_payload for orchestrator would be:
# task_payload = {"messages": processed_messages}
# Then call self._invoke_orchestrator(model_id, task_payload, ...)