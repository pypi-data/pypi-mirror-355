from time import strftime, localtime
import os
import traceback
from unicodedata import east_asian_width


class Logger:
    """日志记录器"""

    def __init__(self, log_dir="logs", log_prefix="app", enable_console=True, enable_file=True):
        """初始化日志记录器"""
        self.LOG_COLORS = {
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'purple': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'RESET': '\033[0m'
        }

        self.LOG_COLOR_MAP = {
            '!': self.LOG_COLORS['yellow'],
            '*': '',
            '+': self.LOG_COLORS['blue'],
            '-': '',
            'x': self.LOG_COLORS['red'],
            '@': '',
            '#': '',
            'RESET': self.LOG_COLORS['RESET']
        }

        self.LOG_DIR = log_dir
        self.LOG_NAME = f'./{log_dir}/{log_prefix}-{strftime("%Y%m%d%H%M%S", localtime())}.log'
        self.enable_console = enable_console
        self.enable_file = enable_file
        self._init_log_dir()

    def _init_log_dir(self):
        """确保日志目录存在"""
        if self.enable_file:
            os.makedirs(self.LOG_DIR, exist_ok=True)

    @staticmethod
    def _custom_strip(s):
        """移除字符串中的特殊空白字符"""
        chars_to_remove = [
            '\u0020', '\u3000', '\u0003',
            '\u0009', '\u000A', '\u000D',
            '\u000B', '\u000C'
        ]
        return s.strip(''.join(chars_to_remove))

    @staticmethod
    def _string_width(s):
        """计算字符串的显示宽度（考虑全角字符）"""
        width = 0
        for char in s:
            width += 2 if east_asian_width(char) in 'FWA' else 1
        return width

    def send_log(self, log_type, log_message, color="auto"):
        """记录日志到控制台和/或文件"""
        log_message = self._custom_strip(str(log_message))
        log_time = f"[{strftime('%Y-%m-%d %H:%M:%S', localtime())}]"
        log_content = ""

        color_code = self.LOG_COLOR_MAP.get(log_type, '') if color == "auto" else self.LOG_COLORS.get(color.lower(), '')
        reset_code = self.LOG_COLORS['RESET']

        if "\n" in log_message:
            lines = log_message.split("\n")
            for i, line in enumerate(lines):
                prefix = f"{log_time} [{log_type}]" if i == 0 else f"{' ' * self._string_width(log_time)} [{log_type}]"
                log_content += f"{prefix} {line}\n"
        else:
            log_content = f"{log_time} [{log_type}] {log_message}\n"

        if self.enable_file:
            with open(self.LOG_NAME, 'a', encoding='utf-8') as f:
                f.write(log_content)

        if self.enable_console:
            print(f"{color_code}{log_content.rstrip()}{reset_code}")

    @staticmethod
    def traceback_info():
        """获取当前异常的堆栈跟踪信息"""
        return traceback.format_exc()
