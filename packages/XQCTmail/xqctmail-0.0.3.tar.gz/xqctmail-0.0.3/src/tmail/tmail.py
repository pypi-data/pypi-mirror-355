"""
作者：Xiaoqiang
微信公众号：XiaoqiangClub
创建时间：2025/6/8 07:50
文件描述：临时邮箱
文件路径：src/tmail/tmail.py
"""

from tmail.utils.tools import *

if is_windows():
    import winsound

import time
import random
import psutil
from tmail.utils.errors import *
from typing import List, Optional, Literal
from AutoChrome import AutoChrome, ChromiumOptionsType, TabType


class TMail:
    USER_AGENT = [
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        # Edge on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
    ]

    def __init__(self,
                 addr_or_opts: ChromiumOptionsType = None,
                 auto_port: bool = True,
                 headless: bool = True,
                 proxy: Optional[dict] = None,
                 try_attach: bool = True,
                 cache_path: Optional[str] = None,
                 log_file: Optional[str] = None,
                 log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "CRITICAL",
                 log_rotation: str = "10 MB",
                 log_retention: str = "7 days",
                 not_print_welcome: bool = False,
                 **kwargs):
        """
        临时邮箱
        :param addr_or_opts: 浏览器的端口、地址或设置好的 ChromiumOptions 对象
        :param auto_port: 是否自动分配端口，默认True。addr_or_opts为None时生效!
        :param headless: 是否启用无头模式
        :param proxy: 代理
        :param try_attach: 是否尝试接管原浏览器
        :param cache_path: 缓存文件路径，默认系统临时目录
        :param log_file: 日志文件路径，默认仅控制台
        :param log_level: 日志等级，默认不会显示任何日志
        :param log_rotation: 日志轮换策略
        :param log_retention: 日志保留策略
        :param not_print_welcome: 是否不打印欢迎信息，默认False
        :param kwargs: 其它参数
        """
        if not not_print_welcome:
            print(f"🚀 欢迎使用由微信公众号：XiaoqiangClub 编写的 Tmail 临时邮箱工具，工具仅用于学习测试，请合法使用！")

        self.email_tab = None
        self.cache_path = cache_path or get_default_cache_path()
        self.headless = headless
        self._cache_info = None
        self.log = setup_logger(log_file=log_file, level=log_level, rotation=log_rotation, retention=log_retention)
        self.user_agent = random.choice(self.USER_AGENT)
        self.start_url = "https://22.do/zh"
        self.g_url = "https://22.do/zh/fake-gmail-generator"

        # 尝试读取缓存
        cache = load_cache(self.cache_path)
        self._cache_info = cache
        if cache:
            browser_addr = cache.get("address", addr_or_opts)
            browser_pid = cache.get("pid")

            ac = self._try_attach_browser(browser_addr, browser_pid, auto_port, proxy, try_attach,
                                          **kwargs) if try_attach else None
            if ac:
                self.ac = ac
            else:
                # 判断进程是否还在，是则强制关闭
                try:
                    if browser_pid is not None:
                        try:
                            p = psutil.Process(browser_pid)
                            if p.is_running():
                                kill_process(browser_pid)
                                clear_cache(self.cache_path)
                                self.log.info("🔄 原浏览器已关闭，重新启动...")
                        except AttachError:
                            self.log.warning(f"⚠️ 无法找到 PID 为 {browser_pid} 的进程，可能已被关闭。")
                    else:
                        self.log.warning("⚠️ browser_pid 未设置，跳过进程清理步骤。")
                except Exception as e:
                    self.log.error(f"❌ 处理浏览器进程时发生未知错误: {e}")
                self.ac = AutoChrome(addr_or_opts=addr_or_opts, headless=self.headless, win_size="max", proxy=proxy,
                                     auto_port=auto_port, auto_handle_alert=True, auto_download_chromium=True,
                                     console_log_level="CRITICAL", incognito=True, not_print_welcome=True,
                                     user_agent=self.user_agent, log_debug_format=False, **kwargs)
        else:
            self.ac = AutoChrome(addr_or_opts=addr_or_opts, headless=self.headless, win_size="max", proxy=proxy,
                                 auto_port=auto_port, auto_handle_alert=True, auto_download_chromium=True,
                                 console_log_level="CRITICAL", incognito=True, not_print_welcome=True,
                                 log_debug_format=False, user_agent=self.user_agent, **kwargs)

        # 启动后保存缓存
        try:
            address = getattr(self.ac, "address", None)
            pid = getattr(self.ac, "process_id", None)
            cache_data = {"address": address, "pid": pid}
            self.log.debug(f"🔄 保存缓存：{cache_data}")
            save_cache(cache_data, self.cache_path)
        except AttachError:
            pass

        self.close = self.finish

    def _try_attach_browser(self, browser_addr, browser_pid,
                            auto_port, proxy, try_attach, **kwargs) -> Optional[AutoChrome]:
        """
        判断并尝试接管缓存中的浏览器进程，返回AutoChrome对象或None
        """
        can_attach = False
        if browser_pid:
            try:
                p = psutil.Process(browser_pid)
                name = p.name().lower()
                cmdline = ' '.join(p.cmdline()).lower()
                if (name.startswith("chrome") or name.startswith("chromium") or name.startswith(
                        "msedge") or "chrome" in cmdline or "chromium" in cmdline or "msedge" in cmdline):
                    if p.is_running():
                        can_attach = True
                    else:
                        self.log.info("🔄 缓存进程已退出，无法接管。")
                else:
                    self.log.info(f"⚠️ 缓存进程不是浏览器({name})，不接管。")
                    clear_cache(self.cache_path)
                    browser_pid = None
            except Exception as e:
                self.log.info(f"⚠️ 检查缓存进程失败：{e}")
                clear_cache(self.cache_path)
                browser_pid = None
        if try_attach and can_attach:
            try:
                ac = AutoChrome(addr_or_opts=browser_addr, headless=self.headless, win_size="max", proxy=proxy,
                                auto_port=False, user_agent=self.user_agent,
                                auto_handle_alert=True, auto_download_browser=True, console_log_level="CRITICAL",
                                incognito=True, not_print_welcome=True, log_debug_format=False, **kwargs)
                self.log.debug(f"🔄 接管原浏览器成功：{ac.address} {ac.process_id}")
                return ac
            except Exception as e:
                self.log.error(f"❌ 接管原浏览器失败：{e}")
                if browser_pid:
                    kill_process(browser_pid)
                clear_cache(self.cache_path)
                return None
        return None

    def refresh_tab(self, tab: TabType = None, ignore_cache: bool = True) -> None:
        """
        刷新页面
        :param tab: 浏览器标签页，默认为当前标签页
        :param ignore_cache: 是否忽略缓存
        :return: None
        """
        tab = tab or self.ac.latest_tab
        self.log.info("🔄 刷新页面...")
        tab.refresh(ignore_cache)

    def current_email(self) -> Optional[str]:
        """当前邮箱地址"""
        try:
            if self.is_entered_email:
                return self.ac.ele_for_action("x:/html/body/section/div/div[1]/div[1]/div/p[2]", timeout=30).text
            else:
                email_name = self.ac.ele_for_action("#mail-input", timeout=30)
                email_domain = self.ac.ele_for_action("#mail-choices", timeout=30).next('t:div', timeout=30)
                if email_name and email_domain:
                    email = email_name.value + email_domain.text
                    self.log.debug(f"📧 当前邮箱：{email}")
                    return email
        except Exception as e:
            self.log.error(f"❌ 获取邮箱失败：{e}")
        return None

    def set_email(self, only_gmail: bool = False) -> Optional[str]:
        """
        设置邮箱
        :param only_gmail: 是否仅获取谷歌邮箱，默认获取所有邮箱，注意：谷歌邮箱数量有限，请勿频繁切换，且包含 @gmail.com @googlemail.com
        :return:
        """
        tab = self.email_tab or self.ac.latest_tab
        if only_gmail:
            self.log.info("🔄 开始获取谷歌邮箱...")
            if tab.url != self.g_url:
                tab.get(self.g_url)
        else:
            self.log.info("🔄 开始切换邮箱...")
            if tab.url != self.start_url:
                tab.get(self.g_url)

        for _ in range(3):
            start_email = self.current_email()
            self.log.debug(f"🔄 开始切换邮箱：{start_email}")
            self.refresh_tab()
            self.ac.wait(1)
            end_email = self.current_email()
            if start_email != end_email:
                self.log.info(f"🔄 邮箱已切换为：{end_email}")
                self.email_tab = self.ac.latest_tab
                # 关闭其他窗口
                self.ac.close_other_tabs(self.email_tab)
                return end_email
            self.ac.wait(1)
            self.log.debug("🚨 邮箱未切换，即将重试...")

        self.log.error("❌ 切换邮箱失败，请稍后再试...")
        return None

    @property
    def is_entered_email(self) -> bool:
        """判断是否已进入邮箱"""
        return self.ac.wait_ele_displayed('#delay', timeout=2)

    def delay_to_24(self) -> bool:
        """将邮箱的有效期延迟到24小时"""
        if not self.is_entered_email:
            self.log.error("❌ 请先进入邮箱！")
            return False

        try:
            _, _, success = self.ac.click_ele('#delay', verify_text_disappear="23 小时 59 分钟", retry_times=3)
            self.log.info(f"✅ 邮箱有效期已延迟到24小时：{success}")
            return success
        except Exception as e:
            self.log.error(f"❌ 延迟邮箱有效期失败：{e}")
        return False

    def refresh_email(self) -> bool:
        """刷新邮箱"""
        if not self.is_entered_email:
            self.log.error("❌ 请先进入邮箱！")
            return False

        try:
            self.ac.click_ele('#refresh')
            return True
        except Exception as e:
            self.log.error(f"❌ 刷新邮箱失败：{e}")
        return False

    def get_expire_time(self) -> Optional[str]:
        """获取邮箱有效期"""
        self.log.info("🔄 获取邮箱有效期...")
        try:
            if not self.is_entered_email:
                self.log.error("❌ 请先进入邮箱！")
                return None
            expire_time = self.ac.ele_for_action('#timeframe').text
            self.log.info(f"✅ 邮箱有效期：{expire_time}")
            return expire_time
        except Exception as e:
            self.log.error(f"❌ 获取邮箱有效期失败：{e}")
        return None

    def enter_email(self) -> bool:
        """进入邮箱"""
        self.log.info("🔄 进入邮箱...")
        try:
            _, _, is_entered = self.ac.click_ele('#into-mailbox', verify_text_disappear="随机生成", retry_times=3)
            if is_entered:
                self.log.info("✅ 进入邮箱成功")
                return True
        except Exception as e:
            self.log.error(f"❌ 进入邮箱失败：{e}")
        self.log.error("❌ 进入邮箱失败，请稍后再试...")
        return False

    def __close_tab(self, tab: TabType = None):
        """
        关闭标签页
        :param tab:  标签页
        :return:
        """
        tab = tab or self.ac.latest_tab
        try:
            tab.close()
        except Exception as e:
            self.log.error(f"❌ 关闭标签页报错：{e}")

    def __get_email_detail(self, url: str, retry_times: int = 1) -> Optional[dict]:
        """
        获取邮件详情
        :param url:
        :param retry_times: 重试次数
        :return: 邮件详情字典，包含 title, sender, date, content
        """
        for _ in range(retry_times + 1):
            self.log.info(f"🔄 正在获取邮件详情：{url}")
            tab = self.ac.new_tab(url)

            try:
                email_div = tab.ele('.email-detail rounded shadow-lg').eles('t:div')
                if not email_div:
                    self.log.error("❌ 获取邮件失败，请稍后再试...")
                    return None
                title = email_div[0].ele('t:span', index=2).text
                self.log.info(f"邮件标题：{title}")
                sender = email_div[1].ele('t:span', index=2).text
                sender = sender.split("<")[-1].strip(">'")
                self.log.info(f"邮件发送者：{sender}")
                date = email_div[2].ele('t:span', index=2).text
                self.log.info(f"邮件发送时间：{date}")
                content = email_div[3].get_frame('x:div[@class="content-iframe"]/iframe').ele('.elementToProof').text
                self.log.info(f"邮件内容：{content}")

                self.__close_tab(tab)
                return {
                    "title": title,
                    "sender": sender,
                    "date": date,
                    "content": content
                }
            except Exception as e:
                self.log.error(f"❌ 获取邮件失败：{e}")

            self.__close_tab(tab)
            self.ac.wait(1)

        return None

    def __get_email_list(self, latest_email: bool = False, retry_times: int = 2) -> Optional[List[str]]:
        """
        获取邮件列表
        :param latest_email: 是否只获取最新的邮件，默认为获取所有邮件
        :param retry_times: 重试次数
        :return: 包含邮件详情页面地址的列表
        """
        for _ in range(retry_times + 1):
            self.log.info("🔄 获取邮件列表...")
            self.refresh_email()
            try:
                email_list = self.ac.ele_for_action('#email-list-wrap').children("t:div")
                self.log.info(f"📭 邮件列表：{email_list}")
                if not email_list:
                    self.log.error("❌ 邮件列表为空...")
                    return None

                if latest_email:
                    email = email_list[-1].ele('t:div')
                    email_url = "https://22.do/zh/content/" + email.attr('onclick').split("; viewEml('")[-1].strip("')")
                    self.log.info(f"✅ 获取到最新邮件：{email_url}")
                    return [email_url]
                else:
                    url_list = []
                    for email in email_list:
                        email = email.ele('t:div')
                        url_list.append(
                            "https://22.do/zh/content/" + email.attr('onclick').split("; viewEml('")[
                                -1].strip("')"))

                    self.log.info(f"✅ 获取到邮件：{url_list}")
                    return url_list

            except Exception as e:
                self.log.error(f"❌ 获取邮件列表失败：{e}")
            self.ac.wait(1)
        return None

    def read_email(self, latest_email: bool = True,
                   wait_email_count: int = 0,
                   loop: bool = False,
                   loop_interval: int = 10,
                   play_sound: bool = False,
                   auto_clean: bool = False) -> Optional[List[dict]]:
        """
        读取邮件，默认情况下只查看一次邮箱并读取最新一封邮件
        :param latest_email: 是否只获取最新的一封邮件
        :param wait_email_count: 循环监听等待新邮件的数量
        :param loop: 是否循环监听获取最新的邮件
        :param loop_interval: 循环获取间隔
        :param play_sound: 是否在有新邮件时播放提示音
        :param auto_clean: 读取结束后是否自动关闭并清理缓存，清理后将无法接管！
        :return: 返回邮件详情列表
        """
        if not self.is_entered_email:
            self.log.info("📥 未进入邮箱，自动尝试进入邮箱...")
            if not self.enter_email():
                self.log.error("❌ 自动进入邮箱失败，无法读取邮件！")
                raise NoEmailError()

        try:
            if loop or wait_email_count > 0:
                self.log.info(f"🔍 正在监听 {self.current_email()}，请勿关闭程序...")
                if loop:
                    print(f"🔍 正在监听 {self.current_email()}，请勿关闭程序...")
                current_emails = None
                spinner = ['|', '/', '-', '\\']
                spin_idx = 0
                refresh_email = 0
                wait_email = []
                while True:
                    if wait_email_count > 0 and wait_email_count == len(wait_email):
                        self.log.info(f"✅ 已获取到 {wait_email_count} 条新邮件，停止监听...")
                        return wait_email
                    refresh_email += 1
                    if loop_interval * refresh_email / 60 > 60:
                        refresh_email = 0
                        self.delay_to_24()
                    if loop:
                        print(f"\r⏳ 正在获取邮件列表...", end="", flush=True)
                    email_urls = self.__get_email_list(latest_email=latest_email)
                    if not email_urls or email_urls == current_emails:
                        wait_time = 0
                        step = 0.2
                        while wait_time < loop_interval:
                            if loop:
                                print(f"\r⏳ 没有新邮件，继续监听... {spinner[spin_idx % len(spinner)]}", end="",
                                      flush=True)
                            spin_idx += 1
                            time.sleep(step)
                            wait_time += step
                        continue
                    current_emails = email_urls
                    if loop:
                        print("\r📨 收到新邮件！正在读取，请稍后...", end="", flush=True)
                    if play_sound and is_windows() and loop:
                        self.__play_notification_sound()
                    email_detail = self.__get_email_detail(email_urls[0])
                    if email_detail:
                        if wait_email_count > 0:
                            wait_email.append(email_detail)
                            if len(wait_email) >= wait_email_count:
                                self.log.info(f"✅ 已获取到 {len(wait_email)} 条新邮件，请查看！")
                            else:
                                self.log.info(f"⏳ 已收到 {len(wait_email)}/{wait_email_count} 条新邮件，继续监听...")
                        if loop:
                            formatted_email = f"\r \n📧 标题: {email_detail['title']}\n" \
                                              f"👤 发送者: {email_detail['sender']}\n" \
                                              f"📅 时间: {email_detail['date']}\n" \
                                              f"📜 内容: {email_detail['content']}"
                            print(formatted_email)
                    wait_time = 0
                    step = 0.2
                    while wait_time < loop_interval:
                        if loop:
                            print(f"\r⏳ 等待下一轮检测... {spinner[spin_idx % len(spinner)]}", end="", flush=True)
                        spin_idx += 1
                        time.sleep(step)
                        wait_time += step
            else:
                email_urls = self.__get_email_list(latest_email=latest_email)
                if not email_urls:
                    self.log.info("📭 邮箱还没有收到邮件...")
                    print("📭 邮箱还没有收到邮件...")
                    return None
                else:
                    if latest_email:
                        return [self.__get_email_detail(email_urls[0])]
                    else:
                        emails = []
                        for email_url in email_urls:
                            emails.append(self.__get_email_detail(email_url))
                            self.ac.wait(1)
                        return emails
        except Exception as e:
            self.log.error(f"❌ 获取邮件失败：{e}")
            return None
        finally:
            if auto_clean:
                self.finish()

    def __play_notification_sound(self):
        """播放提示音，仅Windows下有效"""
        if not is_windows():
            return
        try:
            winsound.Beep(2500, 500)  # 播放一个2500Hz的蜂鸣声，持续500毫秒
        except Exception as e:
            self.log.warning(f"提示音播放失败：{e}")

    def finish(self):
        """结束程序"""
        try:
            self.ac.quit(force=True, del_data=True)
            clear_cache(self.cache_path)
        except Exception as e:
            self.log.error(f"❌ 退出失败：{e}")

    def run(self):
        """
        交互式设置邮箱、进入邮箱并读取邮件。
        用户可在命令行界面选择邮箱类型、是否只用Gmail、是否循环监听、声音提醒等。
        第三步支持循环切换邮箱，直到用户确认。
        """
        print("========= 欢迎使用 Tmail 临时邮箱工具！ =========")
        print("1. 选择邮箱类型（默认临时邮箱）")
        print("2. 是否只用Gmail邮箱？(y/n, 默认n)")
        print("3. 是否循环监听新邮件？(y/n, 默认n)")
        print("4. 是否有新邮件时声音提醒？(y/n, 默认n)")
        print("5. 监听新邮件数量（0为不限，默认0）")
        print("6. 监听间隔秒数（默认10）")
        print("============================================")
        only_gmail = input("是否只用Gmail邮箱？(y/n, 默认n): ").strip().lower() == 'y'
        loop = input("是否循环监听新邮件？(y/n, 默认n): ").strip().lower() == 'y'
        play_sound = input("有新邮件时声音提醒？(y/n, 默认n): ").strip().lower() == 'y'
        try:
            wait_email_count = int(input("监听新邮件数量（0为不限，默认0）: ").strip() or '0')
        except InteractiveError:
            wait_email_count = 0
        try:
            loop_interval = int(input("监听间隔秒数（默认10）: ").strip() or '10')
        except InteractiveError:
            loop_interval = 10
        print("\n🔄 正在设置邮箱...")
        # 循环切换邮箱，直到用户确认
        while True:
            email = self.set_email(only_gmail=only_gmail)
            if not email:
                print("❌ 邮箱设置失败，请稍后再试！")
                return
            print(f"✅ 当前邮箱：{email}")
            ans = input("是否使用该邮箱？(y确认/n切换其它邮箱，默认y): ").strip().lower()
            if ans == '' or ans == 'y':
                break
        print("🔄 正在进入邮箱...")
        if not self.enter_email():
            print("❌ 进入邮箱失败，退出！")
            return
        print("✅ 已进入邮箱，开始接收邮件...\n")
        self.read_email(latest_email=not only_gmail, wait_email_count=wait_email_count, loop=loop,
                        loop_interval=loop_interval, play_sound=play_sound)
        # 是否清理缓存
        clean = input("🧹 程序即将关闭！是否清理缓存？(y/n, 默认n): ").strip().lower() == 'y'
        if clean:
            self.log.info("🧹 清理中...")
            self.finish()
