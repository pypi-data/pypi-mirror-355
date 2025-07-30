"""
对话会话管理器
"""
import sys
from typing import Optional, List, Dict, Any
from .models import ConversationSession, ConversationRecord
from .storage import ConversationStorage
from .boundary_detector import SessionBoundaryDetector

# 配置常量
MAX_SESSIONS_LIMIT = 50  # 最大会话数量限制


class ConversationSessionManager:
    """对话会话管理器"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化会话管理器
        
        Args:
            base_dir: 存储基础目录
        """
        self.storage = ConversationStorage(base_dir)
        self.detector = SessionBoundaryDetector()
        self.current_session: Optional[ConversationSession] = None
        
        print("DEBUG: ConversationSessionManager 初始化完成", file=sys.stderr)
    
    def process_interaction(self, ai_message: str, ai_full_response: str, 
                          user_feedback: str, display_mode: str) -> bool:
        """
        处理一次交互，决定会话分组并保存记录
        
        Args:
            ai_message: AI在UI中展示的消息
            ai_full_response: AI的完整回复内容
            user_feedback: 用户的反馈内容
            display_mode: 当时使用的显示模式
            
        Returns:
            bool: 处理是否成功
        """
        try:
            print(f"DEBUG: 处理交互 - AI消息: {ai_message[:50]}...", file=sys.stderr)
            print(f"DEBUG: 用户反馈: {user_feedback[:50]}...", file=sys.stderr)
            
            # 1. 检查是否需要开始新会话
            should_start_new = self._should_start_new_session(
                ai_message, ai_full_response, user_feedback
            )
            
            if should_start_new:
                print("DEBUG: 检测到需要开始新会话", file=sys.stderr)
                # 结束当前会话（如果存在）
                if self.current_session:
                    self._end_current_session()
                
                # 开始新会话
                self._start_new_session(ai_message, user_feedback)
            
            # 2. 将当前交互添加到会话中
            if self.current_session:
                record = ConversationRecord.create_now(
                    ai_message, ai_full_response, user_feedback, display_mode
                )
                self.current_session.add_conversation(record)
                print(f"DEBUG: 添加对话记录到会话 {self.current_session.session_id}", file=sys.stderr)
            else:
                print("ERROR: 当前没有活动会话", file=sys.stderr)
                return False
            
            # 3. 检查是否需要结束会话
            if self._should_end_session(user_feedback, ai_message):
                print("DEBUG: 检测到会话结束信号", file=sys.stderr)
                self._end_current_session()
            
            return True
            
        except Exception as e:
            print(f"ERROR: 处理交互失败: {e}", file=sys.stderr)
            return False
    
    def get_current_session(self) -> Optional[ConversationSession]:
        """获取当前活动会话"""
        return self.current_session
    
    def list_all_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        return self.storage.list_sessions()
    
    def load_session(self, session_id: str) -> Optional[ConversationSession]:
        """加载指定会话"""
        return self.storage.load_session(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """删除指定会话"""
        # 如果删除的是当前会话，清除当前会话引用
        if self.current_session and self.current_session.session_id == session_id:
            self.current_session = None
        
        return self.storage.delete_session(session_id)

    def clear_all_sessions(self) -> bool:
        """清除所有会话"""
        # 清除当前会话引用
        self.current_session = None
        return self.storage.clear_all_sessions()

    def force_end_current_session(self):
        """强制结束当前会话"""
        if self.current_session:
            self._end_current_session()
    
    def force_start_new_session(self, title: str = "手动开始的会话"):
        """强制开始新会话"""
        if self.current_session:
            self._end_current_session()
        
        self.current_session = ConversationSession.create_new(title)
        print(f"DEBUG: 强制开始新会话: {title}", file=sys.stderr)
    
    def _should_start_new_session(self, ai_message: str, ai_full_response: str, 
                                user_feedback: str) -> bool:
        """判断是否应该开始新会话"""
        # 如果没有当前会话，肯定需要开始新会话
        if not self.current_session:
            return True
        
        # 获取最后交互时间
        last_interaction_time = self.current_session.get_last_interaction_time()
        
        # 使用边界检测器判断
        return self.detector.should_start_new_session(
            last_interaction_time, ai_message, ai_full_response, user_feedback
        )
    
    def _should_end_session(self, user_feedback: str, ai_message: str) -> bool:
        """判断是否应该结束会话"""
        return self.detector.should_end_session(user_feedback, ai_message)
    
    def _start_new_session(self, ai_message: str, user_feedback: str):
        """开始新会话"""
        try:
            # 生成会话标题
            title = self.detector.generate_session_title(user_feedback, ai_message)
            
            # 创建新会话
            self.current_session = ConversationSession.create_new(title)
            
            print(f"DEBUG: 开始新会话 - ID: {self.current_session.session_id}", file=sys.stderr)
            print(f"DEBUG: 会话标题: {title}", file=sys.stderr)
            
        except Exception as e:
            print(f"ERROR: 开始新会话失败: {e}", file=sys.stderr)
            # 创建一个默认会话作为备用
            self.current_session = ConversationSession.create_new("对话记录")
    
    def _end_current_session(self):
        """结束当前会话"""
        if not self.current_session:
            return
        
        try:
            # 只有当会话包含对话记录时才保存
            if self.current_session.get_conversation_count() > 0:
                success = self.storage.save_session(self.current_session)
                if success:
                    print(f"DEBUG: 会话已保存 - ID: {self.current_session.session_id}", file=sys.stderr)
                    print(f"DEBUG: 对话数量: {self.current_session.get_conversation_count()}", file=sys.stderr)

                    # 检查并清理超出限制的会话
                    self.cleanup_old_sessions(max_sessions=MAX_SESSIONS_LIMIT)
                else:
                    print("ERROR: 保存会话失败", file=sys.stderr)
            else:
                print("DEBUG: 空会话，不保存", file=sys.stderr)
            
            # 清除当前会话
            self.current_session = None
            
        except Exception as e:
            print(f"ERROR: 结束会话失败: {e}", file=sys.stderr)
    
    def cleanup_old_sessions(self, max_sessions: int = 100):
        """清理旧会话（保留最近的N个会话）"""
        try:
            sessions = self.list_all_sessions()
            if len(sessions) <= max_sessions:
                return
            
            # 删除最旧的会话
            sessions_to_delete = sessions[max_sessions:]
            for session_info in sessions_to_delete:
                self.delete_session(session_info["session_id"])
                print(f"DEBUG: 删除旧会话: {session_info['title']}", file=sys.stderr)
                
        except Exception as e:
            print(f"ERROR: 清理旧会话失败: {e}", file=sys.stderr)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            sessions = self.list_all_sessions()
            total_conversations = sum(s["conversation_count"] for s in sessions)
            
            return {
                "total_sessions": len(sessions),
                "total_conversations": total_conversations,
                "current_session_active": self.current_session is not None,
                "current_session_conversations": (
                    self.current_session.get_conversation_count() 
                    if self.current_session else 0
                )
            }
        except Exception as e:
            print(f"ERROR: 获取统计信息失败: {e}", file=sys.stderr)
            return {
                "total_sessions": 0,
                "total_conversations": 0,
                "current_session_active": False,
                "current_session_conversations": 0
            }
