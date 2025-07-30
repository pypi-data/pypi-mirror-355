from typing import Dict, List, Optional, Any
import time
from openai import AsyncOpenAI
from mcp import ClientSession
from .config import Config
import redis
import json

# 全局变量
mcp_session: Optional[ClientSession] = None
_openai_client = None

# 用户会话存储
# user_sessions: Dict[str, Dict] = {}

# 按会话ID组织文件
session_files: Dict[str, Dict[str, Any]] = {}

# 假设redis配置在本地，后续可用config.py统一管理
redis_client = redis.Redis(host='localhost', port=6379, db=4, decode_responses=True)

"""
qa_state结构说明（存储于redis，key=qa:{qa_id}）：

典型字段：
- status: 当前流程状态（如 tool_calling, tool_call_end_ready, finished 等）
- session_id: 会话ID，关联多轮上下文
- tool_call_args: 工具调用参数（遇到工具调用时写入）
- tool_call_end_message: 工具调用完成后的聚合结果
- content: 状态描述或异常信息
- usage: LLM推理的token统计信息（通常在stream_end消息中透传）

典型状态流转：
1. LLM推理中遇到工具调用，status -> tool_calling，写入tool_call_args，异步调度工具。
2. 工具调用完成，status -> tool_call_end_ready，写入tool_call_end_message。
3. LLM继续推理，正常结束时status -> finished，写入content和usage。
4. 任何异常均写入status=finished，content为异常信息。
"""

class UserSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict] = []
        self.created_at = time.time()
        self.last_active = time.time()

def create_user_session(session_id: str) -> UserSession:
    """创建新的用户会话"""
    pass
#     session = UserSession(session_id)
#     user_sessions[session_id] = session
#     return session

def get_user_session(session_id: str) -> Optional[UserSession]:
    """获取用户会话"""
    pass
#     return user_sessions.get(session_id)

def update_user_session(session_id: str, messages: List[Dict]):
    """更新用户会话消息"""
    pass
#     if session_id in user_sessions:
#         user_sessions[session_id].messages = messages
#         user_sessions[session_id].last_active = time.time()

def store_file_info(session_id: str, file_info: Any):
    """存储文件信息到会话
    
    Args:
        session_id: 会话ID
        file_info: 文件信息对象
    """
    if session_id not in session_files:
        session_files[session_id] = {}
    session_files[session_id][file_info.file_id] = file_info

def get_session_files(session_id: str) -> Dict[str, Any]:
    """获取会话的文件信息
    
    Args:
        session_id: 会话ID
        
    Returns:
        Dict[str, Any]: 文件信息字典
    """
    return session_files.get(session_id, {})

def cleanup_inactive_sessions():
    """清理不活跃的会话和文件"""
    pass
#     current_time = time.time()
#     inactive_threshold = 86400  # 1天不活跃则清理
    
#     # 清理不活跃的会话
#     for session_id in list(user_sessions.keys()):
#         session = user_sessions[session_id]
#         if current_time - session.last_active > inactive_threshold:
#             # 删除会话
#             del user_sessions[session_id]
#             # 删除会话相关的文件
#             if session_id in session_files:
#                 del session_files[session_id]

def get_openai_client():
    """获取OpenAI客户端，如果不存在则创建
    
    Returns:
        OpenAI: OpenAI客户端
    """
    global _openai_client
    if _openai_client is None:
        # 验证配置
        Config.validate()
        
        # 创建OpenAI客户端
        _openai_client = AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL
        )
    return _openai_client

def set_mcp_session(session: ClientSession):
    """设置MCP会话"""
    global mcp_session
    mcp_session = session

def get_mcp_session() -> Optional[ClientSession]:
    """获取MCP会话"""
    return mcp_session

def get_qa_state(qa_id: str):
    data = redis_client.get(f"qa:{qa_id}")
    if data:
        return json.loads(data)
    return None

def set_qa_state(qa_id: str, state: dict):
    redis_client.set(f"qa:{qa_id}", json.dumps(state, ensure_ascii=False), ex=3600)

# 新增：session_id级别的history累积（redis实现）
def get_session_history(session_id: str) -> list:
    """获取session_id下的完整history，优先redis，兼容内存。"""
    key = f"session_history:{session_id}"
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    # 兼容内存
    # session = user_sessions.get(session_id)
    # if session and hasattr(session, 'messages'):
    #     return session.messages
    # return []

def set_session_history(session_id: str, history: list):
    """设置session_id下的完整history。"""
    key = f"session_history:{session_id}"
    redis_client.set(key, json.dumps(history, ensure_ascii=False), ex=86400)
    # 兼容内存
    # if session_id in user_sessions:
    #     user_sessions[session_id].messages = history

def append_session_history(session_id: str, message: dict):
    """追加一条消息到session_id的history。"""
    history = get_session_history(session_id)
    history.append(message)
    set_session_history(session_id, history) 