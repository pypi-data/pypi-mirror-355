import time

from selenium.common import WebDriverException, TimeoutException, ElementNotVisibleException, \
    StaleElementReferenceException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selo import Db

class Browser:
    def __init__(self, driver,db):
        self.driver = driver
        self.db = db


    def ele_get(self, locator_expr, timeout=30, must_be_visible=False):
        """
        获取元素
        :param locator_expr: 元素定位表达式
        :param timeout: 超时，默认30s
        :param must_be_visible: 是否必须可见
        :return:
        """
        # 开始时间
        start_ms = time.time() * 1000
        # 设置的结束时间
        stop_ms = start_ms + (timeout * 1000)
        for i in range(int(timeout * 10)):
            # 查找元素
            try:
                element = self.driver.find_element(By.XPATH, value=locator_expr)
                # 如果元素不是必须可见的,就直接返回元素
                if not must_be_visible:
                    self.db.log_success(step_name=f"获取元素",log=f"获取元素成功")
                    return element
                # 如果元素必须是可见的,则需要先判断元素是否可见
                else:
                    if element.is_displayed():
                        self.db.log_success(step_name=f"获取元素",log=f"获取元素成功")
                        return element
                    else:
                        raise Exception()
            except Exception:
                now_ms = time.time() * 1000
                if now_ms >= stop_ms:
                    break
            time.sleep(0.1)
        self.db.log_fail(step_name=f"获取元素",log=f"获取元素失败", error_message=f"元素没有出现,定位表达式:%s" % locator_expr)
        raise ElementNotVisibleException('元素定位失败,定位表达式:%s' % locator_expr)

    def open(self, url, expected_title=None, locator_expr=None, timeout=10):
        """
        打开指定的网页，并进行验证。

        :param url: 要打开的网页地址。
        :param expected_title: 预期的页面标题（可选）。
        :param locator_expr: 定位表达式（可选）
        :param timeout: 等待预期条件满足的最大时间（秒，默认10秒）。
        """
        try:
            self.driver.get(url)

            # 检查URL是否正确加载
            if not self.driver.current_url.startswith(url):
                self.db.log_fail(step_name=f"打开网页",log=f"打开网页失败", error_message=f"URL加载失败")
                raise ValueError(f"Failed to load page {url}. Loaded URL is {self.driver.current_url}")

            # 如果提供了预期的页面标题，则等待直到标题匹配
            if expected_title:
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: driver.title and expected_title in driver.title
                )

            # 如果提供了预期的元素，则等待该元素出现
            if locator_expr:
                self.ele_get(locator_expr, timeout=timeout, must_be_visible=True)

        except (WebDriverException, TimeoutException) as e:
            self.db.log_fail(step_name=f"打开网页",log=f"打开网页失败", error_message=f"{e}")
            raise Exception("url超时,%s" % e)

    def ele_disappear(self, locator_expr, timeout=30):
        """
        等待页面元素消失
        :param locator_expr: 定位表达式
        :param timeout: 超时时间
        :return:
        """
        if locator_expr:
            # 开始时间
            start_ms = time.time() * 1000
            # 设置结束时间
            stop_ms = start_ms + (timeout * 1000)
            for i in range(int(timeout * 1000)):
                try:
                    element = self.driver.find_element(By.XPATH, value=locator_expr)
                    if element.is_displayed():
                        self.db.log_success(step_name=f"等待元素消失",log=f"等待元素消失成功")
                        return element
                except Exception:
                    now_ms = time.time() * 1000
                    if now_ms >= stop_ms:
                        break
                    time.sleep(0.1)
                    pass
            self.db.log_fail(step_name=f"等待元素消失",log=f"等待元素消失失败", error_message=f"元素没有消失,定位表达式:%s" % locator_expr)
            raise Exception('元素没有消失,定位表达式:%s' % locator_expr)

    def ele_appear(self, locator_expr, timeout=30):
        """
        等待元素出现
        :param locator_expr:
        :param timeout:
        :return:
        """
        if locator_expr:
            # 开始时间
            start_ms = time.time() * 1000
            # 设置结束时间
            stop_ms = start_ms + (timeout * 1000)
            for i in range(int(timeout * 10)):
                try:
                    element = self.driver.find_element(By.XPATH, locator_expr)
                    if element.is_displayed():
                        self.db.log_success(step_name=f"等待元素出现",log=f"等待元素出现成功")
                        return element
                except Exception:
                    now_ms = time.time() * 1000
                    if now_ms >= stop_ms:
                        break
                    time.sleep(0.1)
                    pass
            self.db.log_fail(step_name=f"等待元素出现",log=f"等待元素出现失败", error_message=f"元素没有出现,定位表达式:%s" % locator_expr)
            raise ElementNotVisibleException('元素没有出现,定位表达式:%s' % locator_expr)

    def wait_for_ready_state_complete(self, timeout=30):
        """
        等待页面完全加载完成
        :param timeout: 超时
        :return:
        """
        # 设置开始时间
        start_ms = time.time() * 1000
        # 设置结束时间
        stop_ms = start_ms + (timeout * 1000)
        for i in range(int(timeout * 1000)):
            try:
                # 获取页面状态
                ready_state = self.driver.execute_script("return document.readyState")
            except WebDriverException:
                # 如果有driver的错误,执行js会失败,就直接跳过
                time.sleep(0.03)
                return True
            # 如果页面元素全部加载完成,返回True
            if ready_state == 'complete':
                time.sleep(0.01)
                return True
            else:
                now_ms = time.time() * 1000
                # 如果超时就break
                if now_ms >= stop_ms:
                    break
                time.sleep(0.1)
        self.db.log_fail(step_name=f"等待页面加载完成",log=f"等待页面加载完成失败", error_message=f"页面没有完全加载完成")
        raise Exception('页面元素未在%s秒内完全加载' % timeout)

    def ele_fill_value(self, locator_expr, fill_value, timeout=30):
        """
        元素填值
        :param locator_expr: 定位表达式
        :param fill_value:填入的值
        :param timeout: 超时时间
        :return:
        """
        # 元素出现
        element = self.ele_appear(locator_expr, timeout)
        try:
            # 先清除元素中的原有值
            element.clear()
        except StaleElementReferenceException:
            # 页面元素没有刷新出来
            self.wait_for_ready_state_complete(timeout)
            time.sleep(0.06)
            element = self.ele_appear(locator_expr, timeout)
            try:
                element.clear()
            except Exception as e:
                raise Exception('元素清空内容失败' % e)
        except Exception as e:

            raise Exception('元素清空内容失败' % e)
        # 填入的值转换成字符串
        if type(fill_value) is int or type(fill_value) is float:
            fill_value = str(fill_value)
        try:
            # 填入的值不是以\n结尾
            if not fill_value.endswith('\n'):
                element.send_keys(fill_value)
                self.wait_for_ready_state_complete(timeout)
            else:
                fill_value = fill_value[:-1]
                element.send_keys(fill_value)
                element.send_keys(Keys.RETURN)
                self.wait_for_ready_state_complete(timeout)
        except StaleElementReferenceException:
            self.wait_for_ready_state_complete(timeout)
            time.sleep(0.05)
            element = self.ele_appear(locator_expr, timeout)
            element.clear()
            if not fill_value.endswith('\n'):
                element.send_keys(fill_value)
                self.wait_for_ready_state_complete(timeout)
            else:
                fill_value = fill_value[:-1]
                element.send_keys(fill_value)
                element.send_keys(Keys.RETURN)
                self.wait_for_ready_state_complete(timeout)
        except Exception:
            self.db.log_fail(step_name=f"元素填值", log=f"元素填值失败", error_message=f"元素填值失败")
            raise Exception('元素填值失败')

    def ele_click(self, locator_expr, locator_expr_appear=None, locator_expr_disappear=None, timeout=30):
        """
        元素点击
        :param locator_expr:定位表达式
        :param locator_expr_appear:等待元素出现的定位表达式
        :param locator_expr_disappear:等待元素消失的定位表达式
        :param timeout: 超时时间
        :return:
        """
        # 元素要可见
        element = self.ele_appear(locator_expr, timeout)
        try:
            # 点击元素
            element.click()
        except StaleElementReferenceException:
            self.wait_for_ready_state_complete(timeout)
            time.sleep(0.06)
            element = self.ele_appear(locator_expr, timeout)
            element.click()
        except Exception as e:
            self.db.log_fail(step_name=f"元素点击", log=f"元素点击失败", error_message=f"元素点击失败")
            raise Exception('页面出现异常:%s,元素不可点击' % e)
        try:
            # 点击元素后的元素出现或消失
            if locator_expr_appear:
                self.ele_appear(locator_expr_appear, timeout)
            if locator_expr_disappear:
                self.ele_disappear(locator_expr_disappear, timeout)
        except Exception:
            pass

    def switch_last_handle(self):
        """
        句柄切换到最新的窗口
        :return:
        """
        window_handles = self.driver.window_handles
        self.driver.switch_to.window(window_handles[-1])
        # Todo 根据页面元素判断是否切换成功

    def switch_handle_until_element_appears(self, locator_expr,  timeout):
        """
        句柄切换,找到元素所在窗口
        :return:
        """
        window_handles = self.driver.window_handles
        for handle in window_handles:
            try:
                self.ele_appear(locator_expr, timeout)
                self.driver.switch_to.window(handle)
                self.db.log_success(step_name=f"句柄切换", log=f"句柄切换成功", error_message=f"句柄切换成功")
                return True
            except Exception:
                pass
        self.db.log_fail(step_name=f"句柄切换", log=f"句柄切换失败", error_message=f"没有找到元素所在的窗口")
        raise Exception('没有找到元素所在的窗口')

    def switch_iframe(self, locator_iframe_expr, timeout):
        """
        进入iframe
        :param locator_iframe_expr: 定位iframe的表达式
        :param timeout: 超时
        :return:
        """
        iframe = self.ele_get(locator_iframe_expr, timeout)
        self.driver.switch_to.frame(iframe)
        # Todo 根据页面元素判断是否切换成功
        self.db.log_success("iframe切换", log=f"iframe切换成功", error_message=f"iframe切换成功")

    def switch_iframe_to_content(self):
        """
        跳出iframe
        :return:
        """
        self.driver.switch_to.parent_frame()
        self.db.log_success("iframe跳出", log=f"iframe跳出成功", error_message=f"iframe跳出成功")

    def scroll_left_right(self, class_name, deviation):
        """
        操作滚动条向左/右移动
        :param class_name: 滚动条的class name
        :param deviation:偏移。0代表最左
        :return:
        """
        down_scroll_js = 'document.getElementsByClassName("%s")[0].scrollLeft=%s' % (class_name, deviation)
        # Todo 根据页面元素判断是否执行成功
        self.db.log_success("滚动条向左/右移动", log=f"滚动条向左/右移动成功", error_message=f"滚动条向左/右移动成功")
        return self.driver.execute_script(down_scroll_js)

    def get_ele_attribute(self, locator_expr, attribute, timeout):
        """
        获取属性值
        :param locator_expr: 定位表达式
        :param attribute: 属性
        :param timeout: 超时
        :return:
        """
        try:
            ele = self.ele_get(locator_expr, timeout, must_be_visible=True)
            if ele.get_attribute(attribute) != "":
                self.db.log_success(step_name=f"获取属性值", log=f"获取属性值成功", error_message=f"获取属性值成功")
                return ele.get_attribute(attribute)
        except Exception as e:
            self.db.log_fail(step_name=f"获取属性值", log=f"获取属性值失败", error_message=f"获取属性值失败")
            raise Exception("获取元素属性失败,%s" % e)

    def element_right_click(self, locator_expr, timeout):
        """
        元素右键点击
        :param locator_expr:定位表达式
        :param timeout: 超时
        :return:
        """
        # 元素要可见
        element = self.ele_appear(locator_expr, timeout)
        try:
            # 右击元素
            ActionChains(self.driver).context_click(element).perform()
            self.db.log_success(step_name=f"元素右击", log=f"元素右击成功", error_message=f"元素右击成功")
            return True
        except StaleElementReferenceException:
            self.wait_for_ready_state_complete(timeout)
            time.sleep(0.06)
            element = self.ele_appear(locator_expr, timeout)
            ActionChains(self.driver).context_click(element).perform()
        except Exception as e:
            self.db.log_fail(step_name=f"元素右击", log=f"元素右击失败", error_message=f"元素右击失败 {e}")
            raise Exception('页面出现异常:%s,元素不可右击' % e)

    def drag_and_drop_element(self, locator_expr_drag, locator_expr_drop, timeout):
        """
        拖拽元素
        :param locator_expr_drag:拖拽的元素
        :param locator_expr_drop:拖拽到的元素
        :param timeout: 超时
        :return:
        """
        element_drag = self.ele_appear(locator_expr_drag, timeout)
        element_drop = self.ele_appear(locator_expr_drop, timeout)
        try:
            ActionChains(self.driver).drag_and_drop(element_drag, element_drop).perform()
            self.db.log_success(step_name=f"拖拽元素", log=f"拖拽元素成功", error_message=f"拖拽元素成功")
            return True
        except StaleElementReferenceException:
            self.wait_for_ready_state_complete(timeout)
            time.sleep(0.06)
            ActionChains(self.driver).drag_and_drop(element_drag, element_drop).perform()
        # Todo 根据页面元素判断是否执行成功


    def map_change(self, timeout):
        """
        地图切换
        :param timeout: 超时
        :return:
        """
        script = """
        var targetNode = document.getElementById('map'); // 替换为你的地图容器ID
        var config = { attributes: true, childList: true, subtree: true };

        var callback = function(mutationsList, observer) {
            for(var mutation of mutationsList) {
                if (mutation.type === 'childList') {
                    console.log('地图内容发生变化');
                    window.mapChanged = true;
                }
            }
        };

        var observer = new MutationObserver(callback);
        observer.observe(targetNode, config);

        window.mapChanged = false;
        """
        for i in range(timeout):
            if self.map_change(timeout):
                self.driver.execute_script(script)
                changed = self.driver.execute_script("return window.mapChanged;")
                if changed:
                    # 重置标志位以便后续监听
                    self.driver.execute_script("window.mapChanged = false;")
                    self.db.log_success(step_name=f"地图切换", log=f"地图切换成功", error_message=f"地图切换成功")
                    return True
                time.sleep(1)
        return False
    def quit(self):
        # 关闭浏览器
        self.driver.quit()
