import requests


class HttpRequest:
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url
        self.token = token
        self.headers = {}

        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
            self.headers["Content-Type"] = "application/json"

    def set_token(self, token):
        """动态更新 token"""
        self.token = token
        self.headers["Authorization"] = f"Bearer {self.token}"

    def get(self, url, params=None, headers=None):
        """
        发送 GET 请求
        :param url: 请求路径
        :param params: 请求参数 dict
        :param headers: 自定义 headers（会覆盖默认）
        :return: 状态码、响应对象
        """
        full_url = self._build_url(url)
        req_headers = headers if headers else self.headers
        try:
            response = requests.get(full_url, params=params, headers=req_headers)
            response.raise_for_status()
            return response.status_code,response.json()
        except requests.exceptions.RequestException as e:
            return None

    def post(self, url, data=None, json=None, params=None, headers=None):
        """
        发送 POST 请求
        :param url: 请求路径（相对路径或完整 URL）
        :param data: 表单数据（dict）
        :param json: JSON 数据（dict）
        :param params: URL 参数（dict）
        :param headers: 自定义 headers（会覆盖默认）
        :return: 状态码、响应对象
        """
        full_url = self._build_url(url)
        req_headers = headers if headers else self.headers
        try:
            response = requests.post(full_url, data=data, json=json, params=params, headers=req_headers)
            response.raise_for_status()
            return response.status_code, response.json()
        except requests.exceptions.RequestException as e:
            return None

    def _build_url(self, url):
        """拼接 base_url 和子路径"""
        if url.startswith(("http://", "https://")):
            return url
        elif self.base_url:
            return f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        else:
            return url