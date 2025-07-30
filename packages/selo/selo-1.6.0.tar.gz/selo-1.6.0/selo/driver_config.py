from rfc3986.misc import NON_PCT_ENCODED
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

class DriverConfig:
    def __init__(self):
        self.browser_path = None
        self.driver_path = None
        self.ser = None
        self.options = None
        self.driver = None
    def driver_options(self):
        """
        初始化 ChromeOptions 并添加常用配置
        """
        self.options = webdriver.ChromeOptions()
        # 去掉‘chrome正受到自动测试软件控制’的提示
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 禁用“保存密码”弹出窗口
        self.options.add_experimental_option("prefs", {"credentials_enable_service": False,
                                                  "profile.password_manager_enabled": False})
        # 防止打印一些无用的日志
        self.options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        # 解决selenium无法访问部分https的问题
        self.options.add_argument('--ignore-certificate-errors')
        # 允许忽略localhost上的TLS/SSL错误
        self.options.add_argument('--allow-insecure-localhost')
        # 解决卡顿
        # options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

    def set_browser_path(self, browser_path):
        """
        设置浏览器路径
        """
        self.browser_path = browser_path
        if self.options is None:
            self.driver_options()
        self.options.binary_location = browser_path

    def set_driver_path(self, driver_path):
        """
        设置驱动路径
        """
        self.driver_path = driver_path
        self.ser = Service(executable_path=driver_path)

    def set_window_size(self, width=1920, height=1080, fullscreen=False):
        """
        设置窗口大小
        """
        if self.options is None:
            self.driver_options()
        if fullscreen:
            self.options.add_argument('--start-fullscreen')
        else:
            self.options.add_argument(f'window-size={width},{height}')

    def enable_incognito(self):
        """
        设置无痕模式
        """
        if self.options is None:
            self.driver_options()
        self.options.add_argument('--incognito')

    def enable_headless(self):
        """
        设置无头模式
        """
        if self.options is None:
            self.driver_options()
        self.options.add_argument('--headless')

    def add_argument(self, arg):
        """
        动态添加参数
        """
        if self.options is None:
            self.driver_options()
        self.options.add_argument(arg)

    def create_driver(self):
        """
        创建浏览器驱动
        """
        if self.options is None:
            self.driver_options()
        if self.ser is None:
            if not self.driver_path:
                raise ValueError("未设置驱动路径，请先调用 set_driver_path()")
            self.ser = Service(executable_path=self.driver_path)
        try:
            self.driver = webdriver.Chrome(service=self.ser, options=self.options)
            self.driver.delete_all_cookies()
            return self.driver
        except Exception as e:
            raise RuntimeError(f"创建 Chrome 驱动失败: {e}")

    def get_driver(self):
        """
        获取已创建的 driver 实例
        """
        if not self.driver:
            raise RuntimeError("Driver 尚未创建，请先调用 create_driver()")
        return self.driver
# 示例:
# config = DriverConfig()
# config.set_browser_path("C:/Program Files/Google/Chrome/Application/chrome.exe")
# config.set_driver_path("C:/path/to/chromedriver.exe")
# config.driver_options()  # 可省略，内部调用会自动初始化
# config.set_window_size(1280, 720)
# config.enable_incognito()
# config.enable_headless()  # 可选
# driver = config.create_driver()
