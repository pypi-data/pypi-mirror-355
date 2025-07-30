import argparse
import platform
import os

from tqsdk_zq.init import init_cmd
from tqsdk_zq.web import web_cmd
from tqsdk_zq.start import start_cmd
from tqsdk_zq import config


def main():
    if platform.system() != "Windows":
        assert os.getuid() != 0, "请勿使用 root 用户运行"
    parser = argparse.ArgumentParser(prog="tqsdk-zq")
    subparsers = parser.add_subparsers(help="Subcommands", required=True)

    init_parser = subparsers.add_parser("init", help="初始化配置信息")
    init_parser.add_argument("--kq-name", help="快期账号")
    init_parser.add_argument("--kq-password", help="快期账号密码")
    init_parser.add_argument("--web-port", help=f"Web 控制台端口号 (默认: {config.DEFAULT_WEB_PORT})")
    init_parser.set_defaults(func=init_cmd)

    web_parser = subparsers.add_parser("web", help="打开 web 控制台")
    web_parser.set_defaults(func=web_cmd)

    start_parser = subparsers.add_parser("start", help="启动控制台进程")
    start_parser.set_defaults(func=start_cmd)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
