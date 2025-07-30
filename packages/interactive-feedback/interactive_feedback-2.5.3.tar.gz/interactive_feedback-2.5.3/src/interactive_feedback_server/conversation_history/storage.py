"""
对话历史记录的存储管理
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import ConversationSession


class ConversationStorage:
    """对话存储管理器"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化存储管理器
        
        Args:
            base_dir: 基础目录，如果为None则使用项目根目录
        """
        if base_dir is None:
            # 获取项目根目录
            base_dir = self._get_project_root()
        
        self.base_dir = Path(base_dir)
        self.history_dir = self.base_dir / "conversation_history"
        self.sessions_dir = self.history_dir / "sessions"
        self.index_file = self.history_dir / "index.json"
        self.metadata_file = self.history_dir / "metadata.json"
        
        # 确保目录存在
        self._ensure_directories()
    
    def _get_project_root(self) -> str:
        """获取项目根目录"""
        # 从当前文件向上查找，直到找到包含pyproject.toml的目录
        current_path = Path(__file__).parent
        while current_path.parent != current_path:
            if (current_path / "pyproject.toml").exists():
                return str(current_path)
            current_path = current_path.parent
        
        # 如果找不到，使用当前工作目录
        return os.getcwd()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        try:
            self.history_dir.mkdir(exist_ok=True)
            self.sessions_dir.mkdir(exist_ok=True)
            
            # 初始化索引文件
            if not self.index_file.exists():
                self._save_index({})
            
            # 初始化元数据文件
            if not self.metadata_file.exists():
                self._save_metadata({
                    "version": "1.0",
                    "created_at": "2024-06-14T00:00:00Z",
                    "total_sessions": 0,
                    "total_conversations": 0
                })
                
        except Exception as e:
            print(f"ERROR: 创建对话历史目录失败: {e}", file=sys.stderr)
    
    def save_session(self, session: ConversationSession) -> bool:
        """
        保存会话到文件
        
        Args:
            session: 要保存的会话
            
        Returns:
            bool: 保存是否成功
        """
        try:
            filename = session.generate_filename()
            filepath = self.sessions_dir / filename
            
            # 确保文件名唯一
            counter = 1
            original_filename = filename
            while filepath.exists():
                name_part = original_filename.replace('.json', '')
                filename = f"{name_part}_{counter:03d}.json"
                filepath = self.sessions_dir / filename
                counter += 1
            
            # 保存会话数据
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self._update_index(session.session_id, filename)
            
            # 更新元数据
            self._update_metadata(session)
            
            return True
            
        except Exception as e:
            print(f"ERROR: 保存会话失败: {e}", file=sys.stderr)
            return False
    
    def load_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        根据会话ID加载会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            ConversationSession: 会话对象，如果不存在则返回None
        """
        try:
            index = self._load_index()
            filename = index.get(session_id)
            
            if not filename:
                return None
            
            filepath = self.sessions_dir / filename
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ConversationSession.from_dict(data)
            
        except Exception as e:
            print(f"ERROR: 加载会话失败: {e}", file=sys.stderr)
            return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话的基本信息
        
        Returns:
            List[Dict]: 会话信息列表
        """
        try:
            sessions = []
            index = self._load_index()
            
            for session_id, filename in index.items():
                filepath = self.sessions_dir / filename
                if filepath.exists():
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        sessions.append({
                            "session_id": session_id,
                            "filename": filename,
                            "title": data.get("title", "未命名会话"),
                            "start_time": data.get("start_time", ""),
                            "conversation_count": len(data.get("conversations", []))
                        })
                    except Exception as e:
                        print(f"WARNING: 读取会话文件失败 {filename}: {e}", file=sys.stderr)
            
            # 按开始时间排序（最新的在前）
            sessions.sort(key=lambda x: x["start_time"], reverse=True)
            return sessions
            
        except Exception as e:
            print(f"ERROR: 列出会话失败: {e}", file=sys.stderr)
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            index = self._load_index()
            filename = index.get(session_id)
            
            if not filename:
                return False
            
            filepath = self.sessions_dir / filename
            if filepath.exists():
                filepath.unlink()
            
            # 从索引中移除
            del index[session_id]
            self._save_index(index)
            
            return True
            
        except Exception as e:
            print(f"ERROR: 删除会话失败: {e}", file=sys.stderr)
            return False

    def clear_all_sessions(self) -> bool:
        """
        清除所有会话

        Returns:
            bool: 清除是否成功
        """
        try:
            # 删除所有会话文件
            for session_file in self.sessions_dir.glob("*.json"):
                session_file.unlink()

            # 清空索引
            self._save_index({})

            # 清空元数据
            self._save_metadata({})

            print("DEBUG: 已清除所有会话", file=sys.stderr)
            return True

        except Exception as e:
            print(f"ERROR: 清除所有会话失败: {e}", file=sys.stderr)
            return False
    
    def _load_index(self) -> Dict[str, str]:
        """加载索引文件"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"ERROR: 加载索引文件失败: {e}", file=sys.stderr)
            return {}
    
    def _save_index(self, index: Dict[str, str]):
        """保存索引文件"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ERROR: 保存索引文件失败: {e}", file=sys.stderr)
    
    def _update_index(self, session_id: str, filename: str):
        """更新索引"""
        index = self._load_index()
        index[session_id] = filename
        self._save_index(index)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载元数据"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"ERROR: 加载元数据失败: {e}", file=sys.stderr)
            return {}
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """保存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ERROR: 保存元数据失败: {e}", file=sys.stderr)
    
    def _update_metadata(self, session: ConversationSession):
        """更新元数据统计"""
        try:
            metadata = self._load_metadata()
            metadata["total_sessions"] = metadata.get("total_sessions", 0) + 1
            metadata["total_conversations"] = (
                metadata.get("total_conversations", 0) + 
                session.get_conversation_count()
            )
            metadata["last_updated"] = session.start_time
            self._save_metadata(metadata)
        except Exception as e:
            print(f"ERROR: 更新元数据失败: {e}", file=sys.stderr)
