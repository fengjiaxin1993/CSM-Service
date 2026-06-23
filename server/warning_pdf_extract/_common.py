"""
预警单提取 - 公共工具模块

提供：
  1. 文本处理工具函数
  2. 关键字同义词字典
  3. CVE 编号提取
  4. 预警等级转换
  5. 表格工具（水印去除、列索引查找）
"""

import re

# ==================== 文本处理工具 ====================


def contain_key(text, keyword):
    """检查文本中是否包含指定关键词（正则匹配）"""
    result_match = re.search(keyword, text)
    if result_match:
        return True
    else:
        return False


def get_middle_text(text, start_text, end_text):
    """提取两个标记文本之间的内容"""
    start_index = text.find(start_text) + len(start_text)
    if end_text != "":
        end_index = text.find(end_text)
        if start_index != -1 and end_index != -1:
            middle_text = text[start_index:end_index]
            return middle_text
        else:
            return ""
    else:
        if start_index != -1:
            middle_text = text[start_index:-1]
            return middle_text
        else:
            return ""


def text_strip(text):
    """去除首尾空白、空格和换行符（紧凑模式）"""
    text = text.strip()
    text = text.replace(" ", "")
    text = text.replace("\n", "")
    return text


def text_clean(text):
    """去除首尾空白、空格，换行符替换为空格（保留可读性）"""
    text = text.strip()
    text = text.replace(" ", "")
    text = text.replace("\n", " ")
    return text


# ==================== 关键字同义词字典 ====================

chinese_key_values_dict = {
    "预警名称": {"预警名称", "风险名称"},
    "预警编号": {"预警编号", "编号"},
    "预警等级": {"预警等级", "预警级别"},
    "风险描述": {"风险描述"},
    "影响范围": {"影响范围"},
    "排查方式": {"排查方式"},
    "修复方式": {"处置方式", "修复方式"},
    "工作要求": {"工作要求"}
}


def get_normalize_match_dict(origin_dic) -> dict:
    """
    将 {标准key: {同义词集合}} 反转为 {同义词: 标准key}
    用于文本归一化时将各种同义词统一为标准 key。
    """
    dic = {}
    for k, vs in origin_dic.items():
        for v in vs:
            dic[v] = k
    return dic


chinese_value_key_dict = get_normalize_match_dict(chinese_key_values_dict)


# ==================== 预警等级转换 ====================

def get_warning_level_int(war: str) -> int:
    """
    将中文预警等级转为整数。
    紧急=1, 重要=2, 一般=3, 其他=0
    """
    if war == "紧急":
        return 1
    elif war == "重要":
        return 2
    elif war == "一般":
        return 3
    else:
        return 0

# 漏洞级别
def get_cve_level_int(war: str) -> int:
    """
    将中文预警等级转为整数。
    低危=1, 中危=2, 高危=3, 超危=4, 其他=0
    """
    if war == "低危":
        return 1
    elif war == "中危":
        return 2
    elif war == "高危":
        return 3
    elif war == "超危":
        return 4
    else:
        return 0


# ==================== CVE 编号提取 ====================

# 支持的编号格式：CVE-2024-21733 / SGVD202510003
def extract_cve_code(txt: str) -> str:
    """从文本中提取 CVE 和 SGVD 格式的漏洞编号，逗号分隔返回"""
    cve_pattern = re.compile(r'CVE-\d{4}-\d+')
    sgvd_pattern = re.compile(r'SGVD\d{4}\d+')

    cve_list = cve_pattern.findall(txt)
    sgvd_list = sgvd_pattern.findall(txt)
    cve_list.extend(sgvd_list)
    return ",".join(cve_list)


# ==================== 表格工具 ====================

def remove_water(text, water_set: set):
    """去除文本中的水印字符"""
    if len(text) > 2:
        for water in water_set:
            for ch in water:
                text = text.replace(ch, "")
        return text_clean(text)
    return text


def get_target_idx(header: list, target: str):
    """在表头列表中查找目标列的索引，未找到返回 -1"""
    for idx, head in enumerate(header):
        if target in head:
            return idx
    return -1
