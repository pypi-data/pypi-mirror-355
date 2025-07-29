"""
作者：Xiaoqiang
微信公众号：XiaoqiangClub
创建时间：2025/6/8 07:50
文件描述：临时邮箱接收验证码
文件路径：scr/tmail/tmail.py
"""
from .tmail import TMail
from .utils import errors, tools

__all__ = ["TMail"]
VERSION = "0.0.3"

def main():
    from .tmail import TMail
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        prog="tmail",
        description="tmail - 临时邮箱自动化工具，支持交互式体验。",
        add_help=False
    )
    parser.add_argument("-v", "--version", action="store_true", help="显示版本信息")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    args = parser.parse_args()
    if args.version:
        print(f"Tmail 版本：{VERSION}")
        sys.exit(0)
    if args.help:
        print("""
tmail - 临时邮箱自动化工具

用法：
  tmail           启动交互式临时邮箱体验
  tmail -v        显示版本信息
  tmail -h        显示帮助信息

说明：
  该工具支持自动获取、切换、监听临时邮箱，适合验证码接收、自动化测试等场景。
  直接运行 tmail 即可进入交互模式，按提示操作。
        """)
        sys.exit(0)
    # 启动交互模式
    tmail = TMail()
    tmail.run()
