import asyncio
from .state import set_qa_state

def format_tool_call_aggregate_result(yield_messages: list) -> dict:
    """
    聚合多个工具调用的yield_message，返回统一格式。
    Args:
        yield_messages: 所有工具的yield_message列表
    Returns:
        dict: 聚合后的主消息
    """
    if len(yield_messages) == 1:
        return yield_messages[0]
    return {
        "type": "tool_end",
        "results": yield_messages
    }

# 异步工具调用任务（单工具版）
async def tool_task_async(qa_id: str, session_id: str, tool_call: dict) -> tuple:
    """
    工具调用任务（异步版，单工具）。
    Args:
        qa_id: 问答ID
        session_id: 会话ID
        tool_call: 单个工具调用参数
    Returns:
        tuple: (tool_response_message, yield_message)
    """
    from .chat_handler import handle_tool_call
    from .state import append_session_history, get_session_history
    try:
        history = get_session_history(session_id)
        api_messages = history.copy()
        from .chat_handler import ToolCall, ToolCallFunction
        tc_obj = ToolCall(
            id=tool_call.get("id"),
            function=ToolCallFunction(
                name=tool_call["function"]["name"],
                arguments=tool_call["function"]["arguments"]
            )
        )
        tool_response_message, yield_message = await handle_tool_call(tc_obj, api_messages, session_id)
        append_session_history(session_id, tool_response_message)
        set_qa_state(qa_id, {"status": "tool_call_end_ready", "tool_call_end_message": yield_message, "session_id": session_id})
        return tool_response_message, yield_message
    except Exception as e:
        error_result = {"type": "error", "step_type": "end", "content": f"工具调用异常: {str(e)}"}
        set_qa_state(qa_id, {"status": "finished", "content": f"工具调用异常: {str(e)}", "session_id": session_id})
        return None, error_result