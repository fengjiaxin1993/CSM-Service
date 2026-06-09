import logging
import os
import tempfile
import shutil

# 通常情况下不需要更改以下内容

# 日志格式
LOG_FORMAT = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format=LOG_FORMAT)


# 临时文件目录，主要用于文件对话
BASE_TEMP_DIR = os.path.join(tempfile.gettempdir(), "upload_files")
try:
    shutil.rmtree(BASE_TEMP_DIR)
except Exception:
    pass
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AppConfig:
    """应用全局配置单例。

    由 startup.py 在启动时从 settings.yaml 加载并填充，各子模块直接读取内存对象，
    兼容打包成二进制后配置文件不存在的场景。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._data = {}
            self._initialized = True

    def load(self, config_dict: dict):
        """从字典加载配置（由 startup.py 调用）"""
        self._data = config_dict

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key: str):
        return self._data[key]

    def __contains__(self, key: str):
        return key in self._data


# 全局配置实例
app_config = AppConfig()
