"""
对话历史记录对话框
"""
import sys
import os
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget,
    QPushButton, QLabel, QFrame, QSizePolicy, QMessageBox,
    QLineEdit, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont


class ConversationCard(QFrame):
    """可折叠的对话卡片"""

    def __init__(self, conversation_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.conversation_data = conversation_data
        self.is_expanded = False

        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setContentsMargins(5, 5, 5, 5)

        self._setup_ui()

    def _get_theme_info(self) -> bool:
        """获取当前主题信息，返回是否为深色主题"""
        try:
            # 向上查找具有 settings_manager 的父级组件
            widget = self
            while widget:
                if hasattr(widget, 'settings_manager'):
                    return widget.settings_manager.get_current_theme() == "dark"
                widget = widget.parent()
        except Exception as e:
            print(f"DEBUG: ConversationCard主题检测失败: {e}", file=sys.stderr)
        return False

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本，超出长度时添加省略号"""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    def _format_timestamp(self, timestamp: str) -> str:
        """格式化时间戳为两行显示格式"""
        if not timestamp:
            return "未知时间<br>--:--"

        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime("%m月%d日")  # 第一行：月日
            time_str = dt.strftime("%H:%M")     # 第二行：时分
            return f"{date_str}<br>{time_str}"
        except:
            # 如果解析失败，尝试从时间戳中提取
            if len(timestamp) >= 8:
                time_part = timestamp[-8:]  # 取最后8位作为时间
                return f"未知日期<br>{time_part[:5]}"  # 只取前5位（HH:MM）
            return "未知时间<br>--:--"

    def _get_theme_colors(self, is_dark: bool) -> dict:
        """根据主题返回颜色配置字典"""
        if is_dark:
            return {
                # 预览区域颜色
                'ai_color': "#ffffff",
                'user_color': "#ffffff",
                'time_color': "#cccccc",
                'time_bg_color': "rgba(255, 255, 255, 0.1)",
                # 详细内容区域颜色
                'label_color': "#ffffff",
                'ai_bg_color': "#1a1a1a",
                'user_bg_color': "#1a1a2a",
                'text_color': "#ffffff",
                'mode_color': "#cccccc",
                # 卡片样式颜色
                'card_bg': "#1a1a1a",
                'card_border': "#444444",
                'card_hover_border': "#666666",
                'card_hover_bg': "#222222"
            }
        else:
            return {
                # 预览区域颜色
                'ai_color': "#000000",
                'user_color': "#000000",
                'time_color': "#666666",
                'time_bg_color': "rgba(0, 0, 0, 0.05)",
                # 详细内容区域颜色
                'label_color': "#000000",
                'ai_bg_color': "#ffffff",
                'user_bg_color': "#f0f8ff",
                'text_color': "#000000",
                'mode_color': "#666666",
                # 卡片样式颜色
                'card_bg': "#ffffff",
                'card_border': "#dddddd",
                'card_hover_border': "#bbbbbb",
                'card_hover_bg': "#f8f8f8"
            }
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        # 创建折叠头部
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # 获取主题信息和颜色配置
        is_dark = self._get_theme_info()
        colors = self._get_theme_colors(is_dark)

        # 时间戳显示（两行格式）
        time_display = self._format_timestamp(self.conversation_data.get("timestamp", ""))

        self.time_label = QLabel(time_display)
        self.time_label.setStyleSheet(f"""
            color: {colors['time_color']} !important;
            font-size: 11px !important;
            font-weight: 500 !important;
            padding: 8px 10px !important;
            background-color: {colors['time_bg_color']} !important;
            border-radius: 6px !important;
            min-width: 60px !important;
            max-width: 80px !important;
            line-height: 1.2 !important;
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setWordWrap(True)  # 允许换行
        header_layout.addWidget(self.time_label)

        # 右侧内容布局：AI消息预览和用户反馈
        content_layout = QVBoxLayout()
        content_layout.setSpacing(3)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # AI消息预览（增加字符数以更好利用空间）
        ai_preview = self._truncate_text(self.conversation_data.get("ai_message", ""), 90)
        self.ai_preview_label = QLabel(f"🤖 {ai_preview}")
        self.ai_preview_label.setWordWrap(True)
        self.ai_preview_label.setStyleSheet(f"color: {colors['ai_color']}; font-size: 13px; font-weight: 500; padding: 2px 0px;")
        content_layout.addWidget(self.ai_preview_label)

        # 用户反馈预览（如果有的话，显示在第二行）
        user_preview = self._truncate_text(self.conversation_data.get("user_feedback", ""), 70)

        if user_preview.strip():  # 只有当用户有反馈时才显示
            self.user_preview_label = QLabel(f"👤 {user_preview}")
            self.user_preview_label.setWordWrap(True)
            self.user_preview_label.setStyleSheet(f"color: {colors['user_color']}; font-size: 12px; font-weight: 400; padding: 2px 0px; margin-left: 4px;")
            content_layout.addWidget(self.user_preview_label)

        header_layout.addLayout(content_layout, 1)  # 占用剩余空间
        
        layout.addWidget(self.header_widget)
        
        # 创建详细内容区域（初始隐藏）
        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(20, 10, 10, 10)
        detail_layout.setSpacing(10)

        # AI完整消息
        ai_full_label = QLabel("🤖 AI完整回复:")
        ai_full_label.setStyleSheet(f"font-weight: 600; color: {colors['label_color']}; font-size: 13px; margin-top: 5px;")
        detail_layout.addWidget(ai_full_label)

        self.ai_full_content = QLabel(self.conversation_data.get("ai_full_response", ""))
        self.ai_full_content.setWordWrap(True)
        self.ai_full_content.setStyleSheet(f"""
            background: {colors['ai_bg_color']};
            padding: 12px;
            border-radius: 6px;
            color: {colors['text_color']};
            border: 1px solid rgba(0, 0, 0, 0.1);
            line-height: 1.4;
        """)
        self.ai_full_content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detail_layout.addWidget(self.ai_full_content)

        # 用户完整反馈
        user_feedback = self.conversation_data.get("user_feedback", "")
        if user_feedback.strip():  # 只有当用户有反馈时才显示
            user_full_label = QLabel("👤 用户反馈:")
            user_full_label.setStyleSheet(f"font-weight: 600; color: {colors['label_color']}; font-size: 13px; margin-top: 8px;")
            detail_layout.addWidget(user_full_label)

            self.user_full_content = QLabel(user_feedback)
            self.user_full_content.setWordWrap(True)
            self.user_full_content.setStyleSheet(f"""
                background: {colors['user_bg_color']};
                padding: 12px;
                border-radius: 6px;
                color: {colors['text_color']};
                border: 1px solid rgba(0, 0, 0, 0.1);
                line-height: 1.4;
            """)
            self.user_full_content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            detail_layout.addWidget(self.user_full_content)

        self.detail_widget.setVisible(False)
        layout.addWidget(self.detail_widget)

        # 应用卡片样式
        self._apply_card_styles(colors)

        # 设置鼠标点击事件
        self.mousePressEvent = self._on_mouse_press

    def _apply_card_styles(self, colors: dict):
        """应用卡片样式"""
        if colors['card_bg'] == "#1a1a1a":  # 深色主题
            self.setStyleSheet(f"""
                ConversationCard {{
                    background-color: {colors['card_bg']} !important;
                    border: 1px solid {colors['card_border']} !important;
                    border-radius: 6px;
                    margin: 2px;
                    padding: 2px;
                }}
                ConversationCard:hover {{
                    border-color: {colors['card_hover_border']} !important;
                    background-color: {colors['card_hover_bg']} !important;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
                }}
                QLabel {{
                    color: #ffffff !important;
                    background-color: transparent;
                }}
            """)
        else:  # 浅色主题
            self.setStyleSheet(f"""
                ConversationCard {{
                    background-color: {colors['card_bg']} !important;
                    border: 1px solid {colors['card_border']} !important;
                    border-radius: 6px;
                    margin: 2px;
                    padding: 2px;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                }}
                ConversationCard:hover {{
                    border-color: {colors['card_hover_border']} !important;
                    background-color: {colors['card_hover_bg']} !important;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
                }}
                QLabel {{
                    color: #000000 !important;
                    background-color: transparent;
                }}
            """)
    

    
    def _on_mouse_press(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_expanded()
    
    def toggle_expanded(self):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        self.detail_widget.setVisible(self.is_expanded)


class ConversationHistoryDialog(QDialog):
    """对话历史记录对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_manager = None
        self.current_sessions = []
        self.original_sessions = []  # 保存原始会话列表用于搜索

        self.setWindowTitle("📚 对话历史记录")
        self.setModal(True)

        # 设置默认大小，然后尝试恢复保存的几何信息
        self.resize(900, 650)
        self._load_geometry_settings()

        # 应用主题样式
        self._apply_dialog_theme()

        self._setup_ui()
        self._load_conversation_history()

    def _get_dialog_theme_info(self) -> bool:
        """获取对话框主题信息，返回是否为深色主题"""
        settings_manager = self._get_settings_manager()
        if settings_manager:
            try:
                return settings_manager.get_current_theme() == "dark"
            except Exception:
                pass
        return False

    def _apply_dialog_theme(self):
        """应用对话框主题样式"""
        is_dark = self._get_dialog_theme_info()

        if is_dark:
            self.setStyleSheet("""
                QDialog {
                    background-color: #1a1a1a !important;
                    color: #ffffff !important;
                }
                QLineEdit {
                    background-color: #2a2a2a !important;
                    border: 1px solid #555555 !important;
                    border-radius: 4px;
                    padding: 8px;
                    color: #ffffff !important;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #0078d4 !important;
                }
                QPushButton {
                    background-color: #333333 !important;
                    border: 1px solid #555555 !important;
                    border-radius: 4px;
                    padding: 8px 16px;
                    color: #ffffff !important;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #444444 !important;
                    border-color: #666666 !important;
                }
                QPushButton:pressed {
                    background-color: #222222 !important;
                }
                QScrollArea {
                    background-color: #1a1a1a !important;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff !important;
                    color: #000000 !important;
                }
                QLineEdit {
                    background-color: #ffffff !important;
                    border: 1px solid #cccccc !important;
                    border-radius: 4px;
                    padding: 8px;
                    color: #000000 !important;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #0078d4 !important;
                }
                QPushButton {
                    background-color: #f8f8f8 !important;
                    border: 1px solid #cccccc !important;
                    border-radius: 4px;
                    padding: 8px 16px;
                    color: #000000 !important;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #eeeeee !important;
                    border-color: #aaaaaa !important;
                }
                QPushButton:pressed {
                    background-color: #dddddd !important;
                }
                QScrollArea {
                    background-color: #ffffff !important;
                    border: none;
                }
            """)

    def _update_stats_label_style(self):
        """更新统计信息标签样式"""
        is_dark = self._get_dialog_theme_info()
        stats_color = "#ffffff" if is_dark else "#000000"

        self.stats_label.setStyleSheet(f"""
            color: {stats_color};
            font-size: 12px;
            font-weight: 400;
            padding: 4px 8px;
            margin: 2px 0px;
        """)

    def _setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 顶部搜索框（移除刷新按钮）
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索对话内容...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self.search_input)

        # 添加动态统计信息显示
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._update_stats_label_style()
        layout.addWidget(self.stats_label)
        
        # 主要内容区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
        
        # 底部按钮
        button_layout = QHBoxLayout()

        # 左侧清除全部按钮
        clear_all_button = QPushButton("🗑️ 清除全部")
        clear_all_button.clicked.connect(self._clear_all_conversations)
        clear_all_button.setToolTip("清除所有对话历史记录")
        button_layout.addWidget(clear_all_button)

        button_layout.addStretch()

        # 右侧关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _get_settings_manager(self):
        """获取设置管理器"""
        return self.parent().settings_manager if (self.parent() and hasattr(self.parent(), 'settings_manager')) else None

    def _load_geometry_settings(self):
        """加载保存的窗口几何信息"""
        settings_manager = self._get_settings_manager()
        if not settings_manager:
            self._center_window()
            return

        try:
            geometry = settings_manager.get_conversation_history_geometry()
            if geometry and self.restoreGeometry(geometry):
                return  # 成功恢复几何信息
        except Exception as e:
            print(f"DEBUG: 加载对话历史窗口几何信息失败: {e}", file=sys.stderr)

        # 恢复失败或没有保存的几何信息，居中显示
        self._center_window()

    def _center_window(self):
        """将窗口居中显示"""
        try:
            screen = QApplication.primaryScreen().geometry()
            window_rect = self.geometry()

            # 计算居中位置
            x = (screen.width() - window_rect.width()) // 2
            y = (screen.height() - window_rect.height()) // 2

            # 确保窗口在屏幕范围内
            x = max(0, min(x, screen.width() - window_rect.width()))
            y = max(0, min(y, screen.height() - window_rect.height()))

            self.move(x, y)
        except Exception as e:
            print(f"DEBUG: 窗口居中失败: {e}", file=sys.stderr)

    def closeEvent(self, event):
        """窗口关闭事件，保存几何信息"""
        settings_manager = self._get_settings_manager()
        if settings_manager:
            try:
                settings_manager.set_conversation_history_geometry(self.saveGeometry())
            except Exception as e:
                print(f"DEBUG: 保存对话历史窗口几何信息失败: {e}", file=sys.stderr)

        super().closeEvent(event)

    def _show_confirmation_dialog(self, title: str, message: str) -> bool:
        """显示确认对话框的通用方法"""
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _refresh_sessions_display(self):
        """刷新会话显示的通用方法"""
        self.current_sessions = []
        self.original_sessions = []
        self._display_sessions()

    def _clear_all_conversations(self):
        """清除所有对话历史记录"""
        if not self.session_manager:
            QMessageBox.warning(self, "错误", "会话管理器未初始化")
            return

        # 检查是否有对话记录
        if not self.current_sessions:
            QMessageBox.information(self, "提示", "暂无对话历史记录需要清除")
            return

        # 确认对话框
        count = len(self.current_sessions)
        if self._show_confirmation_dialog(
            "确认清除",
            f"确定要清除所有 {count} 组对话历史记录吗？\n\n此操作不可撤销！"
        ):
            try:
                # 执行清除操作
                if self.session_manager.clear_all_sessions():
                    self._refresh_sessions_display()
                    QMessageBox.information(self, "成功", "所有对话历史记录已清除")
                else:
                    QMessageBox.warning(self, "错误", "清除对话历史记录失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清除操作发生异常：{str(e)}")

    def _load_conversation_history(self):
        """加载对话历史记录"""
        try:
            # 导入会话管理器
            import sys
            import os
            
            # 添加项目根目录到路径
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from src.interactive_feedback_server.conversation_history import ConversationSessionManager
            
            # 创建会话管理器
            self.session_manager = ConversationSessionManager()
            
            # 获取所有会话
            self.original_sessions = self.session_manager.list_all_sessions()
            self.current_sessions = self.original_sessions.copy()

            # 显示会话
            self._display_sessions()

            # 更新统计信息
            self._update_statistics()
            
        except Exception as e:
            print(f"ERROR: 加载对话历史失败: {e}", file=sys.stderr)
            self._show_error_message(f"加载对话历史失败：{str(e)}")
    
    def _display_sessions(self):
        """显示会话列表"""
        # 清除现有内容
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.current_sessions:
            # 显示空状态
            empty_label = QLabel("暂无对话历史记录")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")
            self.content_layout.addWidget(empty_label)
            return
        
        # 显示会话
        for session_info in self.current_sessions:
            session_widget = self._create_session_widget(session_info)
            self.content_layout.addWidget(session_widget)
        
        # 添加弹性空间
        self.content_layout.addStretch()

        # 更新统计信息
        self._update_statistics()
    
    def _create_session_widget(self, session_info: Dict[str, Any]) -> QWidget:
        """创建会话组件"""
        session_widget = QFrame()
        session_widget.setFrameStyle(QFrame.Shape.Box)
        session_widget.setLineWidth(1)

        # 根据主题设置会话组件样式
        is_dark = self._get_dialog_theme_info()

        if is_dark:
            session_widget.setStyleSheet("""
                QFrame {
                    background-color: #1a1a1a !important;
                    border: 1px solid #444444 !important;
                    border-radius: 8px;
                    margin: 4px;
                    padding: 6px;
                }
                QLabel {
                    color: #ffffff !important;
                }
            """)
        else:
            session_widget.setStyleSheet("""
                QFrame {
                    background-color: #ffffff !important;
                    border: 1px solid #dddddd !important;
                    border-radius: 8px;
                    margin: 4px;
                    padding: 6px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                QLabel {
                    color: #000000 !important;
                }
            """)
        
        layout = QVBoxLayout(session_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 会话标题和信息
        header_layout = QHBoxLayout()

        # 根据主题设置颜色
        title_color = "#ffffff" if is_dark else "#000000"
        info_color = "#cccccc" if is_dark else "#666666"

        # 使用第一次用户反馈作为标题
        session_title = self._get_session_title_from_first_user_feedback(session_info)
        title_label = QLabel(f"💬 {session_title}")
        title_label.setStyleSheet(f"font-weight: 600; font-size: 15px; color: {title_color}; padding: 4px 0px;")
        title_label.setWordWrap(True)  # 允许换行以显示更多内容
        header_layout.addWidget(title_label, 1)  # 占用更多空间

        info_label = QLabel(f"📊 {session_info.get('conversation_count', 0)} 条对话")
        info_label.setStyleSheet(f"color: {info_color}; font-size: 12px; font-weight: 500;")
        header_layout.addWidget(info_label)
        
        layout.addLayout(header_layout)
        
        # 加载并显示对话
        try:
            session = self.session_manager.load_session(session_info["session_id"])
            if session:
                for conversation in session.conversations:
                    card = ConversationCard(conversation.to_dict(), self)
                    layout.addWidget(card)
        except Exception as e:
            error_label = QLabel(f"加载会话失败: {str(e)}")
            error_label.setStyleSheet("color: red; font-size: 12px;")
            layout.addWidget(error_label)
        
        return session_widget
    
    def _on_search_text_changed(self, text: str):
        """搜索文本变化处理 - 优化的实时搜索"""
        search_text = text.lower().strip()

        if not search_text:
            # 显示所有会话（从原始列表恢复）
            self.current_sessions = self.original_sessions.copy()
            self._display_sessions()
            return

        # 从原始会话列表中过滤
        filtered_sessions = []
        for session_info in self.original_sessions:
            # 检查标题是否匹配
            if search_text in session_info.get("title", "").lower():
                filtered_sessions.append(session_info)
                continue

            # 检查对话内容是否匹配
            try:
                session = self.session_manager.load_session(session_info["session_id"])
                if session:
                    for conversation in session.conversations:
                        if (search_text in conversation.ai_message.lower() or
                            search_text in conversation.ai_full_response.lower() or
                            search_text in conversation.user_feedback.lower()):
                            filtered_sessions.append(session_info)
                            break
            except:
                pass

        # 更新当前显示的会话列表
        self.current_sessions = filtered_sessions
        self._display_sessions()
    
    def _show_error_message(self, message: str):
        """显示错误消息"""
        error_label = QLabel(message)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14px; padding: 40px;")
        
        # 清除现有内容
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        self.content_layout.addWidget(error_label)

    def _update_statistics(self):
        """更新统计信息显示"""
        if not hasattr(self, 'stats_label'):
            return

        session_count = len(self.current_sessions)
        total_conversations = 0

        # 计算总对话数
        for session_info in self.current_sessions:
            total_conversations += session_info.get('conversation_count', 0)

        # 更新统计信息文本
        if session_count == 0:
            stats_text = "暂无对话记录"
        else:
            stats_text = f"{session_count}组对话，共{total_conversations}条对话"

        self.stats_label.setText(stats_text)

    def _get_session_title_from_first_user_feedback(self, session_info: Dict[str, Any]) -> str:
        """从第一次用户反馈获取会话标题"""
        try:
            # 检查session_manager是否已初始化
            if not self.session_manager:
                return session_info.get('title', '未命名会话')

            session = self.session_manager.load_session(session_info["session_id"])
            if session and session.conversations:
                # 查找第一个有用户反馈的对话
                for conversation in session.conversations:
                    user_feedback = conversation.user_feedback.strip()
                    if user_feedback:
                        # 智能截断，保留更多有用信息
                        max_length = 60  # 增加显示长度
                        if len(user_feedback) > max_length:
                            return user_feedback[:max_length-3] + "..."
                        return user_feedback

                # 如果没有用户反馈，使用AI消息
                first_ai_message = session.conversations[0].ai_message.strip()
                if first_ai_message:
                    max_length = 60
                    if len(first_ai_message) > max_length:
                        return first_ai_message[:max_length-3] + "..."
                    return first_ai_message
        except Exception as e:
            print(f"DEBUG: 获取会话标题失败: {e}", file=sys.stderr)

        # 回退到原始标题
        return session_info.get('title', '未命名会话')
