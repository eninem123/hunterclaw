# -*- encoding=utf8 -*-
"""
洲明数据中台项目 - Coze 智能体工具（StarRocks数智开发助手）
==================================================
用于调用 Coze 平台上的 StarRocks 数智开发助手智能体，生成和优化 SQL
更新日期：2026-01-16
"""
import os
import sys
from typing import Optional, List, Dict, Any, Iterator
from cozepy import (
    Coze,
    TokenAuth,
    Message,
    ChatStatus,
    MessageContentType,
    ChatEventType,
    COZE_CN_BASE_URL
)

# 尝试从 kb_qa_mvp 配置文件导入设置（可选）
try:
    # 尝试导入 kb_qa_mvp 的配置
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "ai_applications", "kb_qa_mvp", "app", "core", "config.py"
    )
    if os.path.exists(config_path):
        import importlib.util
        spec = importlib.util.spec_from_file_location("kb_config", config_path)
        if spec and spec.loader:
            kb_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(kb_config)
            if hasattr(kb_config, 'settings'):
                _KB_SETTINGS = kb_config.settings
            else:
                _KB_SETTINGS = None
        else:
            _KB_SETTINGS = None
    else:
        _KB_SETTINGS = None
except Exception:
    # 如果导入失败，忽略（工具仍可从环境变量工作）
    _KB_SETTINGS = None


class StarRocksAgent:
    """StarRocks 数智开发助手智能体封装类"""
    
    def __init__(
        self,
        bot_id: Optional[str] = None,
        user_id: Optional[str] = None,
        api_token: Optional[str] = None,
        base_url: str = COZE_CN_BASE_URL
    ):
        """
        初始化 StarRocks 数智开发助手
        
        Args:
            bot_id: Coze Bot ID；不提供则从环境变量 COZE_BOT_ID、COZE_HUNTER_BOT_ID 读取（后者用于猎手等）
            user_id: 用户标识，如果不提供则从环境变量 COZE_USER_ID 读取，或使用默认值
            api_token: Coze API Token；不提供则从 COZE_KEY 或 COZE_TOKEN 读取
            base_url: API 基础地址，默认使用中国区地址
        """
        # 获取环境变量的辅助函数（支持从注册表读取用户环境变量）
        def get_env_var(name):
            value = os.getenv(name)
            if value:
                return value
            # Windows 下从注册表读取用户环境变量
            if sys.platform == 'win32':
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment')
                    try:
                        value, _ = winreg.QueryValueEx(key, name)
                        return value
                    except FileNotFoundError:
                        pass
                    finally:
                        key.Close()
                except Exception:
                    pass
            return None
        
        # 优先从参数获取，其次从环境变量，最后尝试从 kb_qa_mvp 配置读取
        # Token：与 .env 对齐 —— 支持 COZE_KEY（文档名）与 COZE_TOKEN（仓库常用名）
        self.api_token = (
            api_token
            or get_env_var('COZE_KEY')
            or get_env_var('COZE_TOKEN')
            or os.getenv('COZE_KEY', '')
            or os.getenv('COZE_TOKEN', '')
            or (_KB_SETTINGS.COZE_KEY if _KB_SETTINGS and hasattr(_KB_SETTINGS, 'COZE_KEY') else '')
        )
        if not self.api_token:
            raise ValueError(
                "Coze API Token 未设置：请配置环境变量 COZE_KEY 或 COZE_TOKEN，或传入 api_token 参数"
            )

        # Bot：支持 COZE_BOT_ID；猎手等专用 Bot 可用 COZE_HUNTER_BOT_ID（与根目录 .env 一致）
        self.bot_id = (
            bot_id
            or get_env_var('COZE_BOT_ID')
            or get_env_var('COZE_HUNTER_BOT_ID')
            or os.getenv('COZE_BOT_ID', '')
            or os.getenv('COZE_HUNTER_BOT_ID', '')
            or (_KB_SETTINGS.COZE_BOT_ID if _KB_SETTINGS and hasattr(_KB_SETTINGS, 'COZE_BOT_ID') else '')
        )
        if not self.bot_id:
            raise ValueError(
                "Coze Bot ID 未设置：请配置环境变量 COZE_BOT_ID 或 COZE_HUNTER_BOT_ID，或传入 bot_id 参数"
            )
        
        self.user_id = (
            user_id 
            or os.getenv('COZE_USER_ID', '') 
            or (_KB_SETTINGS.COZE_USER_ID if _KB_SETTINGS and hasattr(_KB_SETTINGS, 'COZE_USER_ID') else 'starrocks_dev_user')
        )
        
        # base_url 优先级：参数 > 环境变量 > kb_qa_mvp 配置 > 默认值
        if base_url == COZE_CN_BASE_URL:
            # 如果使用默认值，尝试从配置读取
            env_base_url = os.getenv('COZE_BASE_URL', '')
            if env_base_url:
                self.base_url = env_base_url
            elif _KB_SETTINGS and hasattr(_KB_SETTINGS, 'COZE_BASE_URL'):
                self.base_url = _KB_SETTINGS.COZE_BASE_URL
            else:
                self.base_url = base_url
        else:
            self.base_url = base_url
        
        # 初始化 Coze 客户端
        self.coze = Coze(
            auth=TokenAuth(token=self.api_token),
            base_url=self.base_url
        )
    
    def chat_stream(
        self,
        question: str,
        additional_messages: Optional[List[Message]] = None,
        print_stream: bool = True
    ) -> Iterator[Dict[str, Any]]:
        """
        流式调用智能体（推荐用于长文本生成）
        
        Args:
            question: 用户问题（如 SQL 生成需求）
            additional_messages: 额外的消息列表（可选）
            print_stream: 是否实时打印流式输出（默认 True）
        
        Yields:
            包含事件类型和数据的字典
        """
        messages = [Message.build_user_question_text(question)]
        if additional_messages:
            messages.extend(additional_messages)
        
        full_content = ""
        token_usage = None
        
        try:
            for event in self.coze.chat.stream(
                bot_id=self.bot_id,
                user_id=self.user_id,
                additional_messages=messages
            ):
                event_data = {
                    'event': event.event,
                    'data': None
                }
                
                if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                    content = event.message.content
                    full_content += content
                    event_data['data'] = content
                    if print_stream:
                        print(content, end="", flush=True)
                
                elif event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                    token_usage = event.chat.usage.token_count if event.chat.usage else None
                    event_data['data'] = {
                        'full_content': full_content,
                        'token_usage': token_usage
                    }
                    if print_stream:
                        print()  # 换行
                        if token_usage:
                            print(f"Token 使用量: {token_usage}")
                
                yield event_data
                
        except Exception as e:
            raise RuntimeError(f"调用 Coze 智能体失败: {str(e)}")
    
    def chat(
        self,
        question: str,
        additional_messages: Optional[List[Message]] = None,
        return_full_content: bool = True
    ) -> Dict[str, Any]:
        """
        非流式调用智能体（同步等待完整响应）
        
        Args:
            question: 用户问题（如 SQL 生成需求）
            additional_messages: 额外的消息列表（可选）
            return_full_content: 是否返回完整内容（默认 True）
        
        Returns:
            包含完整响应内容和 token 使用量的字典
        """
        full_content = ""
        token_usage = None
        
        for event in self.chat_stream(
            question=question,
            additional_messages=additional_messages,
            print_stream=False
        ):
            if event['event'] == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                full_content += event['data']
            elif event['event'] == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                token_usage = event['data'].get('token_usage')
        
        return {
            'content': full_content,
            'token_usage': token_usage
        }
    
    def generate_sql(
        self,
        requirement: str,
        context: Optional[str] = None,
        stream: bool = True
    ) -> str:
        """
        生成 SQL 语句（便捷方法）
        
        Args:
            requirement: SQL 生成需求描述
            context: 上下文信息（如表结构、业务规则等，可选）
            stream: 是否使用流式输出（默认 True）
        
        Returns:
            生成的 SQL 语句
        """
        # 构建完整的问题
        question = f"请帮我生成 StarRocks SQL 语句。\n\n需求：{requirement}"
        if context:
            question += f"\n\n上下文信息：\n{context}"
        
        question += "\n\n请确保 SQL 符合 StarRocks 3.3.19 语法规范。"
        
        if stream:
            # 流式输出
            full_content = ""
            for event in self.chat_stream(question=question, print_stream=True):
                if event['event'] == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                    full_content += event['data']
                elif event['event'] == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                    pass  # 已完成
            return full_content
        else:
            # 非流式
            result = self.chat(question=question)
            print(result['content'])
            return result['content']


# ===================== 便捷函数 =====================

def get_agent(
    bot_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> StarRocksAgent:
    """
    获取 StarRocks 数智开发助手实例（便捷函数）
    
    Args:
        bot_id: Bot ID（可选，优先使用环境变量 COZE_BOT_ID）
        user_id: 用户 ID（可选，优先使用环境变量 COZE_USER_ID）
    
    Returns:
        StarRocksAgent 实例
    """
    return StarRocksAgent(bot_id=bot_id, user_id=user_id)


def generate_sql_quick(requirement: str, context: Optional[str] = None) -> str:
    """
    快速生成 SQL（便捷函数）
    
    Args:
        requirement: SQL 生成需求描述
        context: 上下文信息（可选）
    
    Returns:
        生成的 SQL 语句
    """
    agent = get_agent()
    return agent.generate_sql(requirement=requirement, context=context, stream=True)


# ===================== 示例用法 =====================

if __name__ == "__main__":
    """
    使用示例：
    
    1. 设置环境变量：
       export COZE_KEY="your_token_here"
       export COZE_BOT_ID="7582049558638297098"
       export COZE_USER_ID="your_user_id"  # 可选
    
    2. 基本使用：
       from tools.coze_agent import get_agent
       
       agent = get_agent()
       sql = agent.generate_sql("查询订单表中最近30天的销售数据")
    
    3. 流式调用：
       agent = get_agent()
       for event in agent.chat_stream("帮我写一个查询语句"):
           if event['event'] == ChatEventType.CONVERSATION_MESSAGE_DELTA:
               print(event['data'], end="")
    
    4. 快速生成：
       from tools.coze_agent import generate_sql_quick
       sql = generate_sql_quick("查询客户表的所有字段")
    """
    import sys
    
    # 检查环境变量（与 COZE_TOKEN / COZE_HUNTER_BOT_ID 兼容）
    if not (os.getenv('COZE_KEY') or os.getenv('COZE_TOKEN')):
        print("错误: 请设置环境变量 COZE_KEY 或 COZE_TOKEN")
        sys.exit(1)

    if not (os.getenv('COZE_BOT_ID') or os.getenv('COZE_HUNTER_BOT_ID')):
        print("错误: 请设置环境变量 COZE_BOT_ID 或 COZE_HUNTER_BOT_ID")
        print("提示: 可以从 Coze 平台网页链接中获取 Bot ID")
        sys.exit(1)
    
    # 示例：生成 SQL
    print("=" * 60)
    print("StarRocks 数智开发助手 - 测试")
    print("=" * 60)
    
    try:
        agent = get_agent()
        print("\n正在调用智能体生成 SQL...\n")
        
        requirement = "查询订单表中最近30天的销售数据，按日期和产品分组统计销售额"
        context = "表名: dws_sd_order_performance_df, 日期字段: order_date, 金额字段: order_amount"
        
        sql = agent.generate_sql(requirement=requirement, context=context)
        
        print("\n" + "=" * 60)
        print("生成的 SQL:")
        print("=" * 60)
        print(sql)
        
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
