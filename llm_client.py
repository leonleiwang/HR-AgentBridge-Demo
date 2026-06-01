import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# 架构说明：本文件负责 Qwen/DashScope 的 LLM 接入，是“LLM fallback”链路的一部分。
# LLM 接入：使用 OpenAI-compatible API 调用 Qwen，让 HR 数字员工能理解自然语言并生成结构化结果。
# 安全边界：系统提示词明确禁止最终录用、淘汰、发 offer、改薪资、改档案、改权限等高风险动作。
# fallback：如果没有 API Key、网络失败、额度失败或模型异常，返回 None，让 app.py 回退本地 HR Skill。
# 待接入点：真实企业知识库可在调用 LLM 前先做 RAG 检索，把员工手册、FAQ、招聘制度作为上下文传入。

load_dotenv()

LLM_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")


# LLM fallback：调用 Qwen 生成 HR 数字员工结果；失败时返回 None，由主服务回退到本地 Skill。
def call_qwen_hr_agent(task_type: str, user_input: str, risk_level: str = "normal") -> Optional[str]:
    """
    Call Qwen through the DashScope OpenAI-compatible API.
    Return None when configuration is missing or the call fails so the app can fallback locally.
    """
    if not LLM_API_KEY or not LLM_BASE_URL:
        return None

    try:
        client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
        )

        system_prompt = """
你是企业 HR 数字员工，服务于人力数字化场景。
你可以辅助完成简历初筛、入职流程清单、制度问答、邮件草稿和审批待办生成。

重要边界：
1. 你不能做最终录用或淘汰决定，只能提供辅助分析。
2. 你不能发送正式 offer。
3. 你不能修改薪资、合同、员工档案或权限。
4. 高风险动作必须标记为“requires HR confirmation”。
5. 输出必须结构化、简洁、可执行。
6. 如果信息不足，要列出需要补充的信息。
7. 涉及隐私、薪酬、劳动关系、医疗相关内容时，要保守回答并提示人工确认。
"""

        user_prompt = f"""
任务类型：{task_type}
风险等级：{risk_level}
用户输入：{user_input}

请输出中文 Markdown，包含：
1. 任务识别
2. 处理结果
3. 关键依据
4. 风险点
5. 下一步建议
6. 需要人工确认的事项
"""

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()},
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content
    except Exception as exc:
        print(f"[LLM Call Failed] {exc}")
        return None
