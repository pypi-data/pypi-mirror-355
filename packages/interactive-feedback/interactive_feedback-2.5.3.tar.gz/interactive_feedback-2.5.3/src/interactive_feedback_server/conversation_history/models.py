"""
对话历史记录的数据模型
"""
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class ConversationRecord:
    """单次对话记录"""
    timestamp: str
    ai_message: str
    ai_full_response: str
    user_feedback: str
    display_mode: str
    
    @classmethod
    def create_now(cls, ai_message: str, ai_full_response: str, 
                   user_feedback: str, display_mode: str) -> 'ConversationRecord':
        """创建当前时间的对话记录"""
        return cls(
            timestamp=datetime.now().isoformat(),
            ai_message=ai_message,
            ai_full_response=ai_full_response,
            user_feedback=user_feedback,
            display_mode=display_mode
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationRecord':
        """从字典创建对话记录"""
        return cls(**data)


@dataclass
class ConversationSession:
    """对话会话"""
    session_id: str
    start_time: str
    title: str
    conversations: List[ConversationRecord]
    
    @classmethod
    def create_new(cls, title: str) -> 'ConversationSession':
        """创建新的会话"""
        return cls(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now().isoformat(),
            title=title,
            conversations=[]
        )
    
    def add_conversation(self, record: ConversationRecord):
        """添加对话记录"""
        self.conversations.append(record)
    
    def get_conversation_count(self) -> int:
        """获取对话数量"""
        return len(self.conversations)
    
    def get_last_interaction_time(self) -> float:
        """获取最后交互时间（时间戳）"""
        if not self.conversations:
            return time.mktime(datetime.fromisoformat(self.start_time).timetuple())
        
        last_record = self.conversations[-1]
        return time.mktime(datetime.fromisoformat(last_record.timestamp).timetuple())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "title": self.title,
            "conversations": [conv.to_dict() for conv in self.conversations]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        """从字典创建会话"""
        conversations = [
            ConversationRecord.from_dict(conv_data) 
            for conv_data in data.get("conversations", [])
        ]
        
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            title=data["title"],
            conversations=conversations
        )
    
    def generate_filename(self) -> str:
        """生成文件名"""
        # 提取日期部分
        start_date = datetime.fromisoformat(self.start_time)
        date_prefix = start_date.strftime("%m月%d日")
        
        # 清理标题，移除特殊字符
        import re
        clean_title = re.sub(r'[<>:"/\\|?*]', '', self.title.strip())
        clean_title = re.sub(r'\s+', ' ', clean_title)
        
        # 限制标题长度
        max_title_length = 30 - len(date_prefix) - 1
        if len(clean_title) > max_title_length:
            clean_title = clean_title[:max_title_length-3] + "..."
        
        return f"{date_prefix}_{clean_title}.json"
