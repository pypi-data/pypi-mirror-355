"""
会话边界检测器
"""
import time
import re
from typing import Optional


class SessionBoundaryDetector:
    """会话边界检测器"""
    
    def __init__(self):
        # 会话超时时间（秒）
        self.SESSION_TIMEOUT = 30 * 60  # 30分钟
        self.NATURAL_END_TIMEOUT = 2 * 60 * 60  # 2小时
        
        # 新任务指示词
        self.NEW_TASK_INDICATORS = [
            "新的任务", "开始新的", "接下来我们", "现在让我们", "让我们开始",
            "new task", "let's start", "now let's", "next we'll", "let's begin",
            "我来帮你", "我需要", "让我分析", "我发现了新的", "现在我来",
            "接下来", "下面我们", "现在开始", "让我们处理", "我们来看看"
        ]
        
        # 用户新任务信号
        self.USER_NEW_TASK_SIGNALS = [
            "新任务", "重新开始", "开始新的", "换个话题", "新的问题",
            "new task", "start over", "begin new", "different topic", "new issue",
            "另一个问题", "下一个", "接下来", "换一个", "重新来"
        ]
        
        # 完成信号
        self.COMPLETION_SIGNALS = [
            "完成", "结束", "谢谢", "好的，就这样", "没问题了", "搞定",
            "done", "finished", "complete", "thank you", "that's all", "perfect",
            "很好", "可以了", "没事了", "解决了", "成功了"
        ]
        
        # AI完成信号
        self.AI_COMPLETION_SIGNALS = [
            "任务完成", "已完成", "全部完成", "工作完成", "实现完成",
            "task completed", "all done", "finished", "completed successfully",
            "功能实现完成", "修改完成", "优化完成", "问题解决"
        ]
    
    def should_start_new_session(self, last_interaction_time: Optional[float],
                                ai_message: str, ai_full_response: str, 
                                user_feedback: str) -> bool:
        """
        判断是否应该开始新会话
        
        Args:
            last_interaction_time: 上次交互时间戳
            ai_message: AI消息
            ai_full_response: AI完整回复
            user_feedback: 用户反馈
            
        Returns:
            bool: 是否应该开始新会话
        """
        # 优先级1：用户明确表示开始新任务
        if self._is_new_session_by_user_feedback(user_feedback):
            return True
        
        # 优先级2：时间间隔过长
        if self._is_new_session_by_time(last_interaction_time):
            return True
        
        # 优先级3：AI内容表示新任务开始
        if self._is_new_session_by_content(ai_message, ai_full_response):
            return True
        
        return False
    
    def should_end_session(self, user_feedback: str, ai_message: str) -> bool:
        """
        判断是否应该结束当前会话
        
        Args:
            user_feedback: 用户反馈
            ai_message: AI消息
            
        Returns:
            bool: 是否应该结束会话
        """
        # 检查用户反馈中的完成信号
        if self._has_completion_signal(user_feedback, self.COMPLETION_SIGNALS):
            return True
        
        # 检查AI消息中的完成信号
        if self._has_completion_signal(ai_message, self.AI_COMPLETION_SIGNALS):
            return True
        
        return False
    
    def is_natural_session_end(self, last_interaction_time: Optional[float]) -> bool:
        """
        检测会话是否自然结束（长时间无交互）
        
        Args:
            last_interaction_time: 最后交互时间戳
            
        Returns:
            bool: 是否自然结束
        """
        if last_interaction_time is None:
            return False
        
        current_time = time.time()
        time_gap = current_time - last_interaction_time
        
        return time_gap > self.NATURAL_END_TIMEOUT
    
    def _is_new_session_by_time(self, last_interaction_time: Optional[float]) -> bool:
        """基于时间间隔判断是否开始新会话"""
        if last_interaction_time is None:
            return True  # 首次交互
        
        current_time = time.time()
        time_gap = current_time - last_interaction_time
        return time_gap > self.SESSION_TIMEOUT
    
    def _is_new_session_by_content(self, ai_message: str, ai_full_response: str) -> bool:
        """基于AI消息内容判断是否开始新任务"""
        combined_text = f"{ai_message} {ai_full_response}".lower()
        return any(indicator.lower() in combined_text for indicator in self.NEW_TASK_INDICATORS)
    
    def _is_new_session_by_user_feedback(self, user_feedback: str) -> bool:
        """基于用户反馈判断是否明确开始新任务"""
        feedback_lower = user_feedback.lower()
        return any(signal.lower() in feedback_lower for signal in self.USER_NEW_TASK_SIGNALS)
    
    def _has_completion_signal(self, text: str, signals: list) -> bool:
        """检查文本中是否包含完成信号"""
        text_lower = text.lower()
        return any(signal.lower() in text_lower for signal in signals)
    
    def generate_session_title(self, first_user_feedback: str, ai_message: str) -> str:
        """
        生成会话标题
        
        Args:
            first_user_feedback: 首次用户反馈
            ai_message: AI消息
            
        Returns:
            str: 会话标题
        """
        # 优先使用用户反馈作为标题
        if first_user_feedback and len(first_user_feedback.strip()) > 0:
            title_source = first_user_feedback
        else:
            # 回退到AI消息
            title_source = ai_message
        
        # 清理和截断标题
        title = self._clean_title(title_source)
        
        # 限制长度
        max_length = 25  # 为日期前缀留出空间
        if len(title) > max_length:
            title = title[:max_length-3] + "..."
        
        return title
    
    def _clean_title(self, text: str) -> str:
        """清理标题文本"""
        # 移除换行符和多余空格
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符
        cleaned = re.sub(r'[<>:"/\\|?*]', '', cleaned)
        
        # 移除常见的无意义开头
        prefixes_to_remove = [
            "好的，", "好的", "明白了，", "明白了", "我来", "让我", "现在",
            "ok,", "ok", "sure,", "sure", "i'll", "let me", "now"
        ]
        
        cleaned_lower = cleaned.lower()
        for prefix in prefixes_to_remove:
            if cleaned_lower.startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        return cleaned if cleaned else "对话记录"
