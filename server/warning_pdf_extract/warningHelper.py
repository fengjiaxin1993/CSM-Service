"""
预警单信息提取 - 版本路由入口

通过 WarningHelper 类提供统一的对外接口（同名），内部根据 settings.yaml 中的
warning_extract_version 配置自动路由到 v1 或 v2 实现。

部署时只需修改 settings.yaml:
    warning_extract_version: "v1"   # 使用 v1 版本
    warning_extract_version: "v2"   # 使用 v2 版本

使用方式（接口名称始终保持一致）:
    wh = WarningHelper(path)
    result = wh.extract_info()
"""

import yaml
import os

from config.basic_config import BASE_DIR
from server.warning_pdf_extract.v1 import WarningHelper as WarningHelperV1
from server.warning_pdf_extract.v2 import WarningHelper as WarningHelperV2


# 版本注册表：配置值 -> 提取器类
_EXTRACTOR_MAP = {
    "v1": WarningHelperV1,
    "v2": WarningHelperV2,
}


def _get_version_from_config() -> str:
    """从 settings.yaml 读取版本配置，默认返回 v1"""
    try:
        config_path = os.path.join(
            BASE_DIR,
            "settings.yaml"
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        version = data.get("warning_extract_version", "v1")
        if version not in _EXTRACTOR_MAP:
            print(f"[WARN] 未知版本配置: {version}，回退到 v1。可选: {list(_EXTRACTOR_MAP.keys())}")
            return "v1"
        return version
    except Exception as e:
        print(f"[WARN] 读取 warning_extract_version 配置失败: {e}，回退到 v1")
        return "v1"


def get_active_version() -> str:
    """获取当前激活的提取器版本"""
    return _get_version_from_config()


class WarningHelper:
    """
    预警单信息提取的统一入口。

    内部根据 settings.yaml 中的 warning_extract_version 配置自动路由，
    对外接口名称始终为 WarningHelper，保持完全一致。
    """

    def __init__(self, path: str):
        version = _get_version_from_config()
        extractor_cls = _EXTRACTOR_MAP[version]
        self._extractor = extractor_cls(path)
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    def extract_info(self) -> dict:
        """提取预警单信息"""
        return self._extractor.extract_info()

    # 如果 v2 有 extract_risk_table 而 v1 没有，做兼容处理
    def extract_risk_table(self):
        if hasattr(self._extractor, 'extract_risk_table'):
            return self._extractor.extract_risk_table()
        return []


if __name__ == "__main__":
    print(f"当前激活版本: {get_active_version()}")
    # path1 = r"C:\Users\Administrator\Desktop\预警单示例\1 个漏洞.pdf"
    # wh = WarningHelper(path1)
    # dic = wh.extract_info()
    # for k, v in dic.items():
    #     print(f"{k}: {v}")
