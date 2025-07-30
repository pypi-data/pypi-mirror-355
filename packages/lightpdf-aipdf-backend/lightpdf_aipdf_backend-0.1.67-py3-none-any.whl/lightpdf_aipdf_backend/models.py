from typing import List, Optional, Dict
from pydantic import BaseModel

class FileInfoSimple(BaseModel):
    """简化的文件信息模型，用于直接引用不上传的文件"""
    filename: str
    path: str
    password: Optional[str] = None

class FileInfo(FileInfoSimple):
    """文件信息模型"""
    file_id: str
    content_type: str

class Message(BaseModel):
    """聊天消息模型"""
    role: str
    content: str
    file_ids: Optional[List[str]] = None
    file_infos: Optional[List[FileInfoSimple]] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class ChatRequest(BaseModel):
    """聊天请求模型"""
    content: str
    file_ids: Optional[List[str]] = None
    file_infos: Optional[List[FileInfoSimple]] = None
    instructions: Optional[str] = None
    language: Optional[str] = None