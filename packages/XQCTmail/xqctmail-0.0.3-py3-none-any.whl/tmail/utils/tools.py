"""
作者：Xiaoqiang
微信公众号：XiaoqiangClub
创建时间：2025/6/8 13:27
文件描述：工具
文件路径：src/tmail/utils/tools.py
"""
import os
import json
import psutil
import logging
import tempfile
import requests
from loguru import logger
from typing import Optional, Union, Literal


def setup_logger(
        log_file: Optional[str] = None,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
        rotation: Union[int, str] = "10 MB",
        retention: Union[int, str] = "7 days",
        format_str: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}.{name}:{line} - {message}",
        colorize: bool = True,
        enqueue: bool = True,
        serialize: bool = False,
) -> logging.Logger:
    """
    配置 Loguru 日志系统，支持多种定制化设置。


    :param log_file: 日志文件路径（如果为 None，则仅输出到控制台）
    :param level: 日志级别
    :param rotation: 日志文件轮换策略（可以是文件大小或时间间隔）
    :param retention: 日志保留策略（可以是天数或时间字符串）
    :param format_str: 自定义日志格式
    :param colorize: 是否启用彩色日志输出（仅控制台）
    :param enqueue: 是否启用队列模式（用于多线程/多进程安全）
    :param serialize: 是否将日志消息序列化为 JSON 格式（用于日志聚合）
    """

    # 移除默认的日志处理器
    logger.remove()

    # 添加控制台日志输出
    logger.add(
        sink=lambda msg: print(msg, end=''),
        level=level,
        format=format_str,
        colorize=colorize,
        enqueue=enqueue,
        serialize=serialize
    )

    # 如果指定了日志文件路径，则添加文件日志输出
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        logger.add(
            sink=log_file,
            level=level,
            format=format_str,
            rotation=rotation,
            retention=retention,
            enqueue=enqueue,
            serialize=serialize
        )

    # 返回配置好的 logger 对象
    return logger


def log_message(
        msg: str,
        level: Literal["debug", "info", "warning", "error", "critical"] = "info",
        logger: Optional[logging.Logger] = None,
        log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"
) -> None:
    """
    日志输出：优先使用 logger 对象的 level 方法，否则使用 print

    :param msg: 要输出的信息
    :param level: 当前信息的日志等级（debug, info, warning, error, critical）
    :param logger: 可选的 logging.Logger 实例
    :param log_level: 最小输出等级（仅当 level >= log_level 时才输出）
    """
    # 支持的日志等级映射（用于比较优先级）
    level_priority = {
        "debug": 0,
        "info": 1,
        "warning": 2,
        "error": 3,
        "critical": 4,
    }

    # 标准化等级名称
    level = level.lower()
    log_level = log_level.lower()

    # 判断是否满足输出等级要求
    if level_priority.get(level, 1) < level_priority.get(log_level, 1):
        return

    # 如果有 logger，使用 getattr 动态调用对应等级的方法
    if logger is not None:
        getattr(logger, level, logger.info)(msg)
    else:
        # 没有 logger 时，直接 print
        print(f"[{level.upper()}] {msg}")


def kill_process(pid: Union[int, psutil.Process], timeout: float = 5.0) -> bool:
    """
    终止指定进程（支持温和终止和强制杀死）。

    :param pid: 要终止的进程 PID 或 psutil.Process 对象
    :param timeout: 等待进程正常退出的时间（秒），超时后将强制杀死
    :return: 若成功终止返回 True，失败返回 False
    """
    process: Union[psutil.Process, None] = None  # 预先声明，避免 IDE 警告

    try:
        process = pid if isinstance(pid, psutil.Process) else psutil.Process(pid)
        print(f"🔄 尝试终止进程：PID={process.pid}")
        process.terminate()  # 温和终止
        process.wait(timeout=timeout)
        print(f"✅ 进程 {process.pid} 已正常退出。")
        return True
    except psutil.NoSuchProcess:
        print(f"❌ 进程不存在，PID={pid}")
        return False
    except psutil.TimeoutExpired:
        print(f"⚠️ 进程 {pid} 未在 {timeout} 秒内退出，准备强制杀死...")
        if process is not None:
            try:
                process.kill()  # 强制终止
                process.wait(timeout=3)
                print(f"💥 进程 {process.pid} 已被强制杀死。")
                return True
            except Exception as e:
                print(f"❌ 强制杀死进程失败，错误信息：{e}")
                return False
        else:
            print("❌ 错误：未获取到进程对象，无法强制终止。")
            return False
    except Exception as e:
        print(f"❌ 终止进程时出错，错误信息：{e}")
        return False


def is_windows() -> bool:
    """
    判断当前操作系统是否为Windows
    :return: 是Windows返回True，否则返回False
    """
    return os.name == 'nt'


def get_default_cache_path(file_name: str = None) -> str:
    """
    获取默认缓存文件路径，自动适配不同操作系统的临时目录
    :param file_name: 缓存文件名，默认为 tmail_cache.json
    :return: 缓存文件绝对路径
    """
    file_name = file_name or "tmail_cache.json"
    return os.path.join(tempfile.gettempdir(), file_name)


def save_cache(data: dict, cache_path: Optional[str] = None) -> None:
    """
    保存缓存数据到文件
    :param data: 要保存的数据字典
    :param cache_path: 缓存文件路径，默认使用系统临时目录
    """
    if cache_path is None:
        cache_path = get_default_cache_path()
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_cache(cache_path: Optional[str] = None) -> Optional[dict]:
    """
    从缓存文件读取数据
    :param cache_path: 缓存文件路径，默认使用系统临时目录
    :return: 读取到的数据字典，若不存在或出错返回 None
    """
    if cache_path is None:
        cache_path = get_default_cache_path()
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def clear_cache(cache_path: Optional[str] = None) -> None:
    """
    清空缓存文件内容
    :param cache_path: 缓存文件路径，默认使用系统临时目录
    """
    if cache_path is None:
        cache_path = get_default_cache_path()
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except Exception:
            pass


def user_authentication(token: str, api_url: Optional[str] = None) -> bool:
    """
    向 服务器 接口发送 POST 请求以验证验证码。
    :param token: 验证码字符串
    :param api_url: 接口地址
    """
    api_url = api_url or "http://217.142.234.32/auth"
    try:
        response = requests.post(api_url, json={"token": token})
        response.raise_for_status()  # 检查请求是否成功
        return response.json().get("result", False)
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return False
