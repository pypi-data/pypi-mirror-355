from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def create_driver(browser_path, driver_path, incognito=False, headless=False):
    try:
        ser = Service(executable_path=driver_path)
        # 指定 ChromeDriver 的路径

        # 指定浏览器的可执行文件路径
        options = webdriver.ChromeOptions()
        options.binary_location = browser_path

        # 设置窗口大小
        options.add_argument('window-size=1920,1080')
        # 去掉‘chrome正受到自动测试软件控制’的提示
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 禁用“保存密码”弹出窗口
        options.add_experimental_option("prefs", {"credentials_enable_service": False,
                                                  "profile.password_manager_enabled": False})
        # 防止打印一些无用的日志
        options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        # 解决selenium无法访问部分https的问题
        options.add_argument('--ignore-certificate-errors')
        # 允许忽略localhost上的TLS/SSL错误
        options.add_argument('--allow-insecure-localhost')
        # 设置无痕模式
        if incognito:
            options.add_argument('--incognito')
        # 设置无头模式
        if headless:
            options.add_argument('--headless')
        # 解决卡顿
        # options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=ser, options=options)
        # 删除所有cookies
        driver.delete_all_cookies()
        return driver
    except Exception as e:
        raise RuntimeError("初始化驱动失败,%s" % e)
