import json
from typing import Optional, List, Dict, Any, AsyncGenerator, TypedDict, Literal, Union
from agent.utils import llm_util
from agent.utils.nacos_val import get_system_config_from_nacos
from asgi_correlation_id import correlation_id
import uuid, time
from agent.utils.dde_logger import statis_log
from agent.utils.dde_logger import dde_logger as logger

# 定义请求模式类型
RequestMode = Literal["stream", "invoke"]


class LLMRequest(TypedDict, total=False):
    """LLM请求参数对象"""
    service_url: str
    chat_content: str
    system: Optional[str]
    history: Optional[List[List[str]]]
    back_service_urls: Optional[List[str]]
    auto_use_system_back_service: bool
    rid: Optional[str]
    # 允许额外的参数
    extra_params: Dict[str, Any]


class LLMClient:
    def __init__(self):
        system_config = get_system_config_from_nacos()
        self.llm_supported_params = system_config["llm_config"]["llm_supported_params"]
        self.system_back_service = system_config["llm_config"]["system_back_service"]

    @staticmethod
    def get_llm_property(service_url: str) -> Dict[str, Any]:
        return llm_util.get_llm_config(service_url)

    async def llm_stream(
            self,
            request: LLMRequest,
            request_increase_mode: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用LLM服务 - 使用请求对象方式"""
        async for response in self._call_llm_service(
                mode="stream",
                request_increase_mode=request_increase_mode,
                **request
        ):
            yield response

    async def llm_invoke(
            self,
            request: LLMRequest
    ) -> Dict[str, Any]:
        """同步调用LLM服务 - 使用请求对象方式"""
        responses = [
            response async for response in self._call_llm_service(
                mode="invoke",
                **request
            )
        ]
        return responses[-1] if responses else {"content": "", "reasoning_content": "", "think_finished": True}

    async def _call_llm_service(
            self,
            mode: RequestMode,
            service_url: str,
            chat_content: str,
            system: Optional[str] = None,
            history: Optional[List[List[str]]] = None,
            back_service_urls: Optional[List[str]] = None,
            auto_use_system_back_service: bool = False,
            rid: Optional[str] = None,
            request_increase_mode: bool = True,
            **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """内部方法：调用LLM服务，支持重试逻辑"""
        stream = mode == "stream"

        all_urls = self._build_service_urls(service_url, back_service_urls, auto_use_system_back_service)
        errors = []
        if not rid:
            rid = correlation_id.get()
            if not rid:
                rid = "agent_" + str(uuid.uuid4())
        messages = llm_util.build_messages(system, history, chat_content)
        message_str = json.dumps(messages)
        first_valid_chunk_received = False

        for url in all_urls:
            try:
                logger.info(f"尝试连接服务URL: {url}")
                llm_config = llm_util.get_llm_config(url)
                client = llm_util.create_client(llm_config)
                params = llm_config.get("param", {})
                params.update(kwargs.get("extra_params", {}))
                trace_info = {"rid": rid, "requestId": rid}
                filtered_params = self._filter_supported_params(params)
                params.update(trace_info)
                model = llm_config["model"]
                if "max_completion_tokens" in params:
                    params["max_tokens"] = params["max_completion_tokens"]

                if stream:
                    t1 = time.time()

                    # 内部异步生成器处理流式响应
                    async def process_stream():
                        nonlocal first_valid_chunk_received
                        stream_response = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            stream=True,
                            extra_body=params
                        )

                        async for _item in llm_util.handle_stream_output(stream_response, request_increase_mode):
                            # 检查内容有效性
                            _is_valid = bool(_item.get("content")) or bool(_item.get("reasoning_content"))

                            # 只有在成功yield且内容有效后才标记首个有效chunk已接收
                            yield _item
                            if not first_valid_chunk_received and _is_valid:
                                first_valid_chunk_received = True
                                print(f"首个有效chunk已从{url}获取，不再尝试备用模型")

                    first_token_time = 0
                    try:
                        is_ft = True
                        async for item in process_stream():
                            if is_ft:
                                first_token_time = int((time.time() - t1) * 1000)
                                is_ft = False
                            yield item

                        # 如果完整处理了所有chunk，记录成功日志并返回
                        if first_valid_chunk_received:
                            elapsed_time_ms = int((time.time() - t1) * 1000)
                            statis_log("normal", "stream_api", "default", "llm_client", "stream_" + url, "success",
                                       elapsed_time_ms, first_token_time, url, rid, model, params, message_str, len(message_str))
                            return

                    except Exception as e:
                        if first_valid_chunk_received:
                            statis_log("normal", "stream_api", "default", "llm_client", "stream_" + url, "exception", e, "first valid chunk already received,and received exception, will not use backup llm service",
                                       url, all_urls, rid, model, params, message_str, len(message_str))
                            return
                        else:
                            # 首个有效chunk未接收，视为该URL失败
                            statis_log("normal", "stream_api", "default", "llm_client", "stream_" + url, "exception", e, "no chunk received, will use backup llm service",
                                       url, all_urls, rid, model, params, message_str, len(message_str))
                            raise

                else:
                    # 非流式处理保持不变
                    t1 = time.time()
                    response = client.chat.completions.create(
                        model=llm_config["model"],
                        messages=messages,
                        stream=False,
                        extra_body={"rid": rid},
                        **filtered_params
                    )
                    elapsed_time_ms = int((time.time() - t1) * 1000)
                    if response.choices:
                        message = response.choices[0].message
                        content = message.content or ""
                        reasoning_content = getattr(message, "reasoning_content", "") or ""
                        is_valid = bool(content) or bool(reasoning_content)

                        yield {
                            "content": content,
                            "reasoning_content": reasoning_content,
                            "think_finished": True
                        }

                        if is_valid:
                            statis_log("normal", "common_api", "default", "llm_client", "invoke_" + url, "success", elapsed_time_ms, url, rid, model, params, message_str, len(message_str))
                            return
                        else:
                            statis_log("normal", "common_api", "default", "llm_client", "invoke_" + url, "fail", "response.choices empty", url, rid, model, params, message_str, len(message_str))
                    else:
                        yield {
                            "content": "",
                            "reasoning_content": "",
                            "think_finished": True
                        }
                        statis_log("normal", "common_api", "default", "llm_client", "invoke_" + url, "fail", "response.choices empty", url, rid, model, params, message_str, len(message_str))
                    return

            except Exception as e:
                if stream:
                    statis_log("normal", "stream_api", "default", "llm_client", "stream_" + url, "exception", e, url, rid, message_str, len(message_str))
                else:
                    statis_log("normal", "common_api", "default", "llm_client", "invoke_" + url, "exception", e, url, rid, message_str, len(message_str))
                error_msg = f"服务URL {url} 调用失败: {str(e)}"
                logger.error(f"call llm exception, rid={rid}, url={url}, {error_msg}", exc_info=True)
                errors.append(error_msg)

        logger.error(f"call llm final fail, {errors}, rid={rid}", exc_info=True)
        raise Exception(f"所有服务URL调用失败: {errors}, rid={rid}")

    def _build_service_urls(
            self,
            primary_url: str,
            back_urls: Optional[List[str]],
            use_system_back: bool
    ) -> List[str]:
        """构建完整的服务URL列表，包括备用服务"""
        urls = [primary_url] + (back_urls or [])
        if use_system_back:
            if isinstance(self.system_back_service, list):
                urls.extend(self.system_back_service)
            else:
                urls.append(self.system_back_service)
        return urls

    def _filter_supported_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """过滤掉LLM服务不支持的参数"""
        filtered = {k: v for k, v in params.items() if k in self.llm_supported_params}
        unsupported = {k: v for k, v in params.items() if k not in self.llm_supported_params}

        if unsupported:
            print(f"忽略不支持的参数: {unsupported}")

        return filtered


# 提供模块级API接口，保持向后兼容性
_client = LLMClient()
get_llm_property = _client.get_llm_property
llm_stream = _client.llm_stream
llm_invoke = _client.llm_invoke
