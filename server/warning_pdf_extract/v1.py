"""
====================================================================
预警单信息提取 - V1 版本（扁平输出）
====================================================================

版本定位：适用于简单预警单，无漏洞表格的场景。
输出结构为扁平字典，所有字段在顶层。

核心差异（与 V2 对比）：
  - 不使用表格提取（无 risk_table）
  - PDF 解析简单：with pymupdf.open() 一次性打开，忽略倾斜文字
  - 输出字段直接在顶层：desc, check, repair, requirement, cve_code
  - 无水印处理逻辑

输出结构:
    {
        "name": "xxx",         # 预警名称
        "code": "xxx",         # 预警编号
        "level": 1,            # 预警等级（1紧急/2重要/3一般）
        "desc": "xxx",         # 风险描述
        "influence": "xxx",    # 影响范围
        "check": "xxx",        # 排查方式
        "repair": "xxx",       # 修复方式
        "requirement": "xxx",  # 工作要求
        "cve_code": "xxx"      # CVE/SGVD编号
    }
====================================================================
"""

import pymupdf
from server.warning_pdf_extract._common import (
    contain_key, get_middle_text, text_strip, text_clean,
    chinese_key_values_dict, chinese_value_key_dict,
    get_warning_level_int, extract_cve_code
)


class WarningHelper:
    """
    V1 版本：扁平结构输出，适用于简单预警单。

    不提取 PDF 表格，所有信息从纯文本中通过关键词定位提取。
    """

    def __init__(self, path: str):
        self.path = path
        self.chinese_key_values_dict = chinese_key_values_dict
        self.chinese_value_key_dict = self._build_normalize_dict()
        self.span_list = []
        with pymupdf.open(path) as doc:
            for page_idx in range(doc.page_count):
                page = doc.load_page(page_idx)
                blocks = page.get_text("dict")['blocks']
                for idx, block in enumerate(blocks):
                    type_int = block['type']
                    if type_int == 0:  # 只保留文本信息
                        lines = block["lines"]
                        for line in lines:
                            spans = line['spans']
                            direction = line["dir"]
                            if direction[0] != 1.0 or direction[1] != 0.0:  # 跳过倾斜文字
                                continue
                            self.span_list.extend(spans)
        self.text = self._get_text()

    # -------------------- 文本处理 --------------------

    def _build_normalize_dict(self) -> dict:
        """构建 {同义词: 标准key} 映射表"""
        dic = {}
        for k, vs in self.chinese_key_values_dict.items():
            for v in vs:
                dic[v] = k
        return dic

    def _get_text(self):
        """从 span 列表中提取并归一化文本，遇到"联系人"停止"""
        text_list = []
        for span in self.span_list:
            text = span['text']
            text = text_strip(text)
            if contain_key(text, "联系人"):
                break
            else:
                nor_text = self._normalize_text(text)
                text_list.append(nor_text)
        return "\n".join(text_list)

    def _normalize_text(self, text):
        """将文本中的同义词替换为标准 key"""
        for name, standard in self.chinese_value_key_dict.items():
            if contain_key(text, name):
                text = text.replace(name, standard)
        return text

    # -------------------- 字段提取 --------------------

    def _extract_level(self):
        """提取预警等级"""
        return text_strip(get_middle_text(self.text, "预警等级：", "预警编号"))

    def _extract_code(self):
        """提取预警编号"""
        return text_strip(get_middle_text(self.text, "预警编号：", "预警名称"))

    def _extract_name(self):
        """提取风险名称"""
        return text_strip(get_middle_text(self.text, "预警名称：", "通知范围"))

    def _extract_cve_code(self):
        """从风险描述中提取 CVE/SGVD 编号"""
        risk_desc = get_middle_text(self.text, "风险描述\n", "影响范围\n")
        return extract_cve_code(risk_desc)

    def _extract_desc(self):
        """提取风险描述（若包含"漏洞信息如下"则截断）"""
        risk_desc = get_middle_text(self.text, "风险描述\n", "影响范围\n")
        if contain_key(risk_desc, "漏洞信息如下"):
            risk_desc = get_middle_text(risk_desc, "风险描述\n", "漏洞信息如下")
        return text_strip(risk_desc)

    def _extract_influence(self):
        """提取影响范围"""
        return text_clean(get_middle_text(self.text, "影响范围\n", "排查方式\n"))

    def _extract_check(self):
        """提取排查方式"""
        return text_strip(get_middle_text(self.text, "排查方式\n", "修复方式\n"))

    def _extract_repair(self):
        """提取修复方式"""
        return text_strip(get_middle_text(self.text, "修复方式\n", "工作要求\n"))

    def _extract_requirement(self):
        """提取工作要求"""
        return text_strip(get_middle_text(self.text, "工作要求\n", ""))

    # -------------------- 对外接口 --------------------

    def extract_info(self) -> dict:
        """提取预警单信息，返回扁平结构字典"""
        dic = {}
        dic["name"] = self._extract_name()
        dic["code"] = self._extract_code()
        dic["level"] = get_warning_level_int(self._extract_level())
        dic["desc"] = self._extract_desc()
        dic["influence"] = self._extract_influence()
        dic["check"] = self._extract_check()
        dic["repair"] = self._extract_repair()
        dic["requirement"] = self._extract_requirement()
        dic["cve_code"] = self._extract_cve_code()
        return dic


if __name__ == "__main__":
    # 测试路径（仅示例）
    path1 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202502003L2.pdf"
    path11 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202505010L3.pdf"
    wh = WarningHelper(path11)
    dic = wh.extract_info()
    for k, v in dic.items():
        print(f"{k}: {v}")
