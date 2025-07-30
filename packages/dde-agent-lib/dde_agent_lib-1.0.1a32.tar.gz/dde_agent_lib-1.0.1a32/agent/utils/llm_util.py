from typing import Optional, Dict, Any, List
from openai import OpenAI
from agent.utils.nacos_val import get_system_config_from_nacos


def build_messages(
        system: Optional[str],
        history: Optional[List[List[str]]],
        chat_content: str
) -> List[Dict[str, str]]:
    """构建符合OpenAI格式的消息列表"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})

    if history:
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})

    messages.append({"role": "user", "content": chat_content})
    return messages


def create_client(llm_config: Dict[str, Any]) -> OpenAI:
    """创建OpenAI客户端实例"""
    return OpenAI(
        api_key=llm_config["api_key"],
        base_url=llm_config["url"]
    )


async def handle_stream_output(stream, request_increase_mode: bool):
    current_content = []
    current_reasoning = []

    for chunk in stream:
        is_thinking = True
        content = getattr(chunk.choices[0].delta, 'content', '') or ''
        reasoning_content = getattr(chunk.choices[0].delta, 'reasoning_content', '') or ''
        #当开始有content输出时，认为think结束
        if is_thinking and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
            is_thinking = False
        if request_increase_mode:
            yield {
                "content": content,
                "reasoning_content": reasoning_content,
                "think_finished": not is_thinking
            }
        else:
            current_content.append(content)
            current_reasoning.append(reasoning_content)
            yield {
                "content": ''.join(current_content),
                "reasoning_content": ''.join(current_reasoning),
                "think_finished": not is_thinking
            }


def get_llm_config(service_url: str) -> Dict[str, Any]:
    """获取LLM服务配置，支持服务标签和URL匹配"""
    system_config = get_system_config_from_nacos()
    service_type_configs = system_config["llm_config"]["service_config"]
    default_config = system_config["llm_config"]["default_service_config"]

    result_config = default_config.copy()
    tag = "default"

    # 解析带标签的服务URL
    if "::" in service_url:
        parts = service_url.split("::")
        if len(parts) == 2:
            result_config["url"] = parts[0]
            tag = parts[1]
        else:
            raise ValueError(f"无效的带标签服务URL格式: {service_url}")
    else:
        result_config["url"] = service_url

    # 查找匹配的服务类型配置
    for config in service_type_configs:
        for url_match in config["url_match"]:
            if url_match in service_url and tag == config["tag"]:
                result_config.update({
                    k: v for k, v in config.items()
                    if k in ["model", "api_key", "think_able", "param", "feature"] and v is not None
                })
                break

    return result_config