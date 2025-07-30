import requests
import json  # 用于调试打印
import logging  # 为日志记录器添加
from typing import Optional, Any, Tuple, List, Dict, TypeVar, Type
from pydantic import ValidationError
from pyrate_limiter import Limiter, BucketFullException, Rate, Duration, InMemoryBucket


from .exceptions import QuakeAPIException, QuakeAuthException, QuakeRateLimitException, QuakeInvalidRequestException, QuakeServerException
from .models import (
    UserInfoResponse, FilterableFieldsResponse,
    ServiceSearchResponse, ServiceScrollResponse, ServiceAggregationResponse,
    HostSearchResponse, HostScrollResponse, HostAggregationResponse,
    SimilarIconResponse, QuakeResponse,
    RealtimeSearchQuery, ScrollSearchQuery, AggregationQuery, FaviconSimilarityQuery
)

# 定义用于 _request 方法的类型变量
T = TypeVar('T', bound=QuakeResponse)

class QuakeClient:
    """
    Quake API 的 Python 客户端，使用 Pydantic 进行数据验证。
    """
    BASE_URL = "https://quake.360.net/api/v3"

    def __init__(self, api_key: str, timeout: int = 30, rate_limiter: Optional[Limiter] = None, logger: Optional[logging.Logger] = None):
        """
        初始化 QuakeClient。

        :param api_key: 你的 Quake API 密钥。
        :param timeout: 请求超时时间（秒）。
        :param rate_limiter: 一个可选的 pyrate-limiter Limiter 实例，用于客户端速率限制。
        :param logger: 一个可选的 logging.Logger 实例。
        """
        if not api_key:
            raise ValueError("API 密钥不能为空。")
        self.api_key = api_key
        self.timeout = timeout
        
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger("QuakeClient")
            if not self.logger.handlers:  # 如果已经配置，避免添加多个处理器
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.WARNING)  # 如果用户未配置，则默认为 WARNING

        if rate_limiter is None:
            # 如果没有提供速率限制器，则创建一个默认的：每3秒1个请求
            default_rates = [Rate(1, Duration.SECOND * 3)]
            default_bucket = InMemoryBucket(default_rates)
            # 配置 max_delay 以便 try_acquire 可以阻塞等待
            self.rate_limiter = Limiter(default_bucket, max_delay=5000)  # 调整为5秒以适应更长的间隔
        else:
            self.rate_limiter = rate_limiter
            
        self._session = requests.Session()
        self._session.headers.update({
            "X-QuakeToken": self.api_key,
            "Content-Type": "application/json"
        })

    def _handle_api_error(self, error_data: dict, http_status_code: int):
        """根据 API 错误码辅助引发特定异常。"""
        code = error_data.get("code")
        message = error_data.get("message", "未知的 API 错误")

        if code in ["u3004", "u3011"]:  # 特定认证错误
            raise QuakeAuthException(message, code, http_status_code)
        elif code in ["u3005", "q3005"]:  # 速率限制错误
            raise QuakeRateLimitException(message, code, http_status_code)
        elif code in ["u3007", "u3009", "u3010", "u3015", "u3017", "q2001", "q3015", "t6003"]:  # 无效请求错误
            raise QuakeInvalidRequestException(message, code, http_status_code)
        # 如果 Quake 为服务器错误等定义了其他特定的错误代码，请在此处添加。
        # 目前，任何其他非零代码都是通用的 QuakeAPIException。
        raise QuakeAPIException(f"API 错误 {code}: {message}", code, http_status_code)


    def _request(self, method: str, endpoint: str, response_model: Type[T], params: Optional[dict] = None, json_data: Optional[dict] = None) -> T:
        """
        向 Quake API 发出 HTTP 请求并解析响应。

        :param method: HTTP 方法 (GET, POST)。
        :param endpoint: API 端点路径。
        :param response_model: 用于解析响应的 Pydantic 模型。
        :param params: GET 请求的 URL 参数。
        :param json_data: POST 请求的 JSON 主体 (以字典形式)。
        :return: 解析后的 Pydantic 模型响应。
        :raises QuakeAPIException: 如果 API 返回错误或响应格式不正确。
        """
        if self.rate_limiter:
            # 如果 Limiter 配置了 max_delay，此调用将阻塞并等待，直到可以获取到项目（1个请求）。
            # 对被速率限制的项目使用一个通用名称 "quake_api_call"。
            try:
                self.rate_limiter.try_acquire("quake_api_call", 1)
            except BucketFullException as e:
                # 如果 max_delay 未设置或设置得太短，可能会发生这种情况。
                # 将其重新引发为 QuakeRateLimitException，因为客户端期望此类型。
                # 原始异常 'e' 包含有关命中的速率的 meta_info。
                raise QuakeRateLimitException(
                    f"客户端速率限制已超出: {e.meta_info.get('error', 'Bucket full')}", 
                    api_code="CLIENT_RATE_LIMIT",  # 客户端限制的自定义代码
                    response_status_code=None  # 不是 HTTP 错误
                ) from e
            # 如果超过了 max_delay，也可能引发 LimiterDelayException。
            # 目前，让它传播或在用户未处理时由通用的 QuakeAPIException 捕获。

        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self._session.request(method, url, params=params, json=json_data, timeout=self.timeout)
            response.raise_for_status()  # 对错误的响应 (4xx or 5xx) 引发 HTTPError
        except requests.HTTPError as e:
            try:
                error_data = e.response.json()
                self._handle_api_error(error_data, e.response.status_code)
            except (requests.JSONDecodeError, ValueError, KeyError):  # 如果错误响应不是 JSON 或没有预期的键
                if e.response.status_code == 401:
                    raise QuakeAuthException(
                        f"认证失败: {e.response.status_code} - {e.response.text}",
                        api_code=None,  # 如果 JSON 解析失败，则没有 API 代码
                        response_status_code=e.response.status_code
                    )
                else:
                    raise QuakeAPIException(
                        f"HTTP 错误: {e.response.status_code} - {e.response.text}",
                        api_code=None,  # 如果 JSON 解析失败，则没有 API 代码
                        response_status_code=e.response.status_code
                    )
        except requests.RequestException as e:  # 捕获其他请求异常，如 ConnectionError
            raise QuakeAPIException(f"请求失败: {e}")

        try:
            response_json = response.json()
        except ValueError:  # JSONDecodeError 继承自 ValueError
            raise QuakeAPIException(f"解码 JSON 响应失败: {response.text}", response_status_code=response.status_code)
        
        # 如果日志记录器级别为 DEBUG，则记录原始数据
        if self.logger.isEnabledFor(logging.DEBUG) and response_model is ServiceSearchResponse and 'data' in response_json:
            try:
                self.logger.debug(
                    "ServiceSearchResponse 的原始 API 响应数据:\n%s",
                    json.dumps(response_json['data'], indent=2, ensure_ascii=False)
                )
            except Exception as e:
                self.logger.debug("无法 json.dumps 原始 API 响应数据: %s。错误: %s", response_json.get('data'), e)


        # 使用提供的 Pydantic 模型验证和解析成功的响应
        try:
            parsed_response = response_model.model_validate(response_json)
        except ValidationError as e:
            raise QuakeAPIException(f"验证 API 响应失败: {e}。原始响应: {response_json}", response_status_code=response.status_code)

        # 检查成功解析的响应中由 'code' 字段指示的 API 级别错误
        if parsed_response.code != 0:
            self._handle_api_error({"code": parsed_response.code, "message": parsed_response.message}, response.status_code)
            # 上面的代码会引发异常，所以这部分更多是出于逻辑上的完整性
            raise QuakeAPIException(f"API 错误 {parsed_response.code}: {parsed_response.message}", parsed_response.code, response.status_code)

        return parsed_response

    def get_user_info(self) -> UserInfoResponse:
        """
        检索当前用户的信息。
        端点: /user/info
        方法: GET

        :return: UserInfoResponse Pydantic 模型。
        """
        return self._request("GET", "/user/info", response_model=UserInfoResponse)

    def get_service_filterable_fields(self) -> FilterableFieldsResponse:
        """
        检索服务数据的可筛选字段。
        端点: /filterable/field/quake_service
        方法: GET

        :return: FilterableFieldsResponse Pydantic 模型。
        """
        return self._request("GET", "/filterable/field/quake_service", response_model=FilterableFieldsResponse)

    def search_service_data(self, query_params: RealtimeSearchQuery) -> ServiceSearchResponse:
        """
        对服务数据执行实时搜索。
        端点: /search/quake_service
        方法: POST

        :param query_params: 包含查询详情的 RealtimeSearchQuery Pydantic 模型。
        :return: ServiceSearchResponse Pydantic 模型。
        """
        return self._request("POST", "/search/quake_service", response_model=ServiceSearchResponse, json_data=query_params.model_dump(exclude_none=True))

    def scroll_service_data(self, query_params: ScrollSearchQuery) -> ServiceScrollResponse:
        """
        对服务数据执行滚动（深度分页）搜索。
        端点: /scroll/quake_service
        方法: POST

        :param query_params: ScrollSearchQuery Pydantic 模型。
        :return: ServiceScrollResponse Pydantic 模型。
        """
        return self._request("POST", "/scroll/quake_service", response_model=ServiceScrollResponse, json_data=query_params.model_dump(exclude_none=True))

    def get_service_aggregation_fields(self) -> FilterableFieldsResponse:
        """
        检索服务聚合数据的可筛选字段。
        端点: /aggregation/quake_service (GET 用于字段)
        方法: GET

        :return: FilterableFieldsResponse Pydantic 模型。
        """
        return self._request("GET", "/aggregation/quake_service", response_model=FilterableFieldsResponse)

    def aggregate_service_data(self, query_params: AggregationQuery) -> ServiceAggregationResponse:
        """
        对服务数据执行聚合查询。
        端点: /aggregation/quake_service (POST 用于查询)
        方法: POST

        :param query_params: AggregationQuery Pydantic 模型。
        :return: ServiceAggregationResponse Pydantic 模型。
        """
        return self._request("POST", "/aggregation/quake_service", response_model=ServiceAggregationResponse, json_data=query_params.model_dump(exclude_none=True))

    def get_host_filterable_fields(self) -> FilterableFieldsResponse:
        """
        检索主机数据的可筛选字段。
        端点: /filterable/field/quake_host
        方法: GET

        :return: FilterableFieldsResponse Pydantic 模型。
        """
        return self._request("GET", "/filterable/field/quake_host", response_model=FilterableFieldsResponse)

    def search_host_data(self, query_params: RealtimeSearchQuery) -> HostSearchResponse:
        """
        对主机数据执行实时搜索。
        端点: /search/quake_host
        方法: POST

        :param query_params: RealtimeSearchQuery Pydantic 模型。
        :return: HostSearchResponse Pydantic 模型。
        """
        # 注意：主机搜索的文档化参数中没有 'latest' 或 'shortcuts'
        # RealtimeSearchQuery 将它们作为可选参数包含，如果为 None，model_dump 会排除它们
        host_query_data = query_params.model_dump(exclude_none=True)
        host_query_data.pop('latest', None)
        host_query_data.pop('shortcuts', None)
        return self._request("POST", "/search/quake_host", response_model=HostSearchResponse, json_data=host_query_data)

    def scroll_host_data(self, query_params: ScrollSearchQuery) -> HostScrollResponse:
        """
        对主机数据执行滚动（深度分页）搜索。
        端点: /scroll/quake_host
        方法: POST

        :param query_params: ScrollSearchQuery Pydantic 模型。
        :return: HostScrollResponse Pydantic 模型。
        """
        # 注意：主机滚动的文档化参数中没有 'latest'
        host_query_data = query_params.model_dump(exclude_none=True)
        host_query_data.pop('latest', None)
        return self._request("POST", "/scroll/quake_host", response_model=HostScrollResponse, json_data=host_query_data)

    def get_host_aggregation_fields(self) -> FilterableFieldsResponse:
        """
        检索主机聚合数据的可筛选字段。
        端点: /aggregation/quake_host (GET 用于字段)
        方法: GET

        :return: FilterableFieldsResponse Pydantic 模型。
        """
        return self._request("GET", "/aggregation/quake_host", response_model=FilterableFieldsResponse)

    def aggregate_host_data(self, query_params: AggregationQuery) -> HostAggregationResponse:
        """
        对主机数据执行聚合查询。
        端点: /aggregation/quake_host (POST 用于查询)
        方法: POST

        :param query_params: AggregationQuery Pydantic 模型。
        :return: HostAggregationResponse Pydantic 模型。
        """
        # 注意：主机聚合的文档化参数中没有 'latest'
        host_query_data = query_params.model_dump(exclude_none=True)
        host_query_data.pop('latest', None)
        return self._request("POST", "/aggregation/quake_host", response_model=HostAggregationResponse, json_data=host_query_data)

    def query_similar_icons(self, query_params: FaviconSimilarityQuery) -> SimilarIconResponse:
        """
        执行 favicon 相似性搜索。
        端点: /query/similar_icon/aggregation
        方法: POST

        :param query_params: FaviconSimilarityQuery Pydantic 模型。
        :return: SimilarIconResponse Pydantic 模型。
        """
        return self._request("POST", "/query/similar_icon/aggregation", response_model=SimilarIconResponse, json_data=query_params.model_dump(exclude_none=True))

    def close(self):
        """关闭底层的 requests 会话。"""
        if self._session:
            self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
