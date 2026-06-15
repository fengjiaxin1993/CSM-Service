"""
预警单信息提取 - 统一入口

在 v1 扁平输出的基础上，集成了 v2 的表格提取能力。

使用方式:
    wh = WarningHelper(path)
    result = wh.extract_info()              # v1 兼容：返回扁平结构
    risk_table = wh.extract_risk_table()    # v2 能力：返回漏洞表格
"""

import pymupdf
from server.warning_pdf_extract._common import (
    contain_key, get_middle_text, text_strip, text_clean,
    chinese_key_values_dict, chinese_value_key_dict,
    get_warning_level_int, extract_cve_code,
    remove_water, get_target_idx
)


class WarningHelper:
    """
    预警单信息提取的统一实现。

    输出结构 (extract_info):
    {
        "name": "xxx",         # 预警名称
        "code": "xxx",         # 预警编号
        "level": 1,            # 预警等级（1紧急/2重要/3一般）
        "desc": "xxx",         # 风险描述
        "influence": "xxx",    # 影响范围
        "check": "xxx",        # 排查方式
        "repair": "xxx",       # 修复方式
        "requirement": "xxx",  # 工作要求
        "cve_code": "xxx",     # CVE/SGVD编号
        "risk_table": [...]    # 漏洞表格（从 PDF 表格提取，无表格时退化为单条记录）
    }
    """

    def __init__(self, path: str):
        self.path = path
        self.chinese_key_values_dict = chinese_key_values_dict
        self.chinese_value_key_dict = chinese_value_key_dict
        self.span_list = []
        self.risk_table_data = []        # 表格提取结果
        self.water_text_set = set()      # 水印文字集合
        try:
            self.doc = pymupdf.open(path)
            for page_idx in range(self.doc.page_count):
                page = self.doc.load_page(page_idx)
                blocks = page.get_text("dict")['blocks']
                for idx, block in enumerate(blocks):
                    type_int = block['type']
                    if type_int == 0:  # 只保留文本信息
                        lines = block["lines"]
                        for line in lines:
                            spans = line['spans']
                            direction = line["dir"]
                            if direction[0] != 1.0 or direction[1] != 0.0:  # 倾斜文字 → 水印
                                for span in spans:
                                    text = span['text']
                                    self.water_text_set.add(text)
                                continue
                            self.span_list.extend(spans)
            self.text = self._get_text()
            self.water_mark_flag = len(self.water_text_set) > 0
            self._extract_risk_table()  # 尝试提取表格
        finally:
            self.doc.close()
            self.doc = None

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

    # -------------------- 表格提取 --------------------

    def _get_keyword_bbox(self, page_idx: int, keyword: str):
        """在指定页中查找包含 keyword 的文本块，返回其 bbox (x0, y0, x1, y1)"""
        page = self.doc.load_page(page_idx)
        blocks = page.get_text("blocks")
        sorted_lst = sorted(blocks, key=lambda x: x[1])  # 按 y0 从上到下排序
        for x0, y0, x1, y1, text, _, _ in sorted_lst:
            if contain_key(text, keyword):
                return (x0, y0, x1, y1)
        return None

    def _extract_risk_table(self):
        """
        使用 find_tables() 提取"风险描述"下方到"影响范围"上方之间的表格数据。
        判断逻辑：表格 bbox 与两个关键词之间的 y 区间有交集即纳入。
        """
        risk_y = None
        risk_page = -1
        influence_y = None
        influence_page = -1

        for page_idx in range(self.doc.page_count):
            if risk_y is None:
                bbox = self._get_keyword_bbox(page_idx, "风险描述")
                if bbox:
                    risk_y = bbox[1]
                    risk_page = page_idx
            if influence_y is None:
                bbox = self._get_keyword_bbox(page_idx, "影响范围")
                if bbox:
                    influence_y = bbox[1]
                    influence_page = page_idx
            if risk_y is not None and influence_y is not None:
                break

        if risk_y is None or influence_y is None:
            return

        all_page_rows = []  # [(page_idx, [[cell...], ...])]

        for page_idx in range(risk_page, influence_page + 1):
            page = self.doc.load_page(page_idx)
            page_rect = page.rect

            # 确定本页两个关键词之间的 y 区间
            if risk_page == influence_page:
                y0, y1 = risk_y, influence_y
            elif page_idx == risk_page:
                y0, y1 = risk_y, page_rect.y1
            elif page_idx == influence_page:
                y0, y1 = page_rect.y0, influence_y
            else:
                y0, y1 = page_rect.y0, page_rect.y1

            find_result = page.find_tables()
            if hasattr(find_result, 'tables'):
                tables = find_result.tables
            else:
                tables = find_result

            for table in tables:
                t_bbox = table.bbox
                if t_bbox[1] >= y0 and t_bbox[3] <= y1:
                    rows = table.extract()
                    if rows:
                        # 去水印
                        if self.water_text_set:
                            rows = [[remove_water(str(t), self.water_text_set) for t in row] for row in rows]
                        all_page_rows.append((page_idx, rows))

        if not all_page_rows:
            return

        table_data = self._merge_cross_page_tables(all_page_rows)
        self.risk_table_data = self._convert_table(table_data)

    def _merge_cross_page_tables(self, all_page_rows):
        """
        合并跨页表格。
        - 只有跨页（page_idx 不同）且列数相同时才合并
        - 合并时跳过重复表头
        """
        if len(all_page_rows) <= 1:
            return all_page_rows[0][1] if all_page_rows else []

        prev_page, prev_rows = all_page_rows[0]
        merged = list(prev_rows)

        for i in range(1, len(all_page_rows)):
            curr_page, curr_rows = all_page_rows[i]

            if not prev_rows or not curr_rows:
                prev_page, prev_rows = curr_page, curr_rows
                continue

            prev_last_cols = len(prev_rows[-1])
            curr_first_cols = len(curr_rows[0])

            if curr_page != prev_page and prev_last_cols == curr_first_cols:
                start = 0
                if curr_rows[0] == prev_rows[0]:  # 跳过重复表头
                    start = 1
                merged.extend(curr_rows[start:])
            else:
                merged.extend(curr_rows)

            prev_page, prev_rows = curr_page, curr_rows

        return merged

    def extract_risk_table(self) -> list:
        """返回漏洞表格数据（字典列表）"""
        return self.risk_table_data

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

    # -------------------- 表格转换 --------------------

    def _convert_table(self, table_data: list[list[str]]) -> list:
        """将二维表格数据转为字典列表"""
        code_idx = get_target_idx(table_data[0], "编号")
        name_idx = get_target_idx(table_data[0], "名称")

        res_dic_list = []
        for row in table_data[1:]:
            dic = {
                "name": row[name_idx],
                "code": row[code_idx],
                "desc": self._extract_desc(),
                "influence": self._extract_influence(),
                "check": self._extract_check(),
                "repair": self._extract_repair(),
                "requirement": self._extract_requirement()
            }
            res_dic_list.append(dic)
        return res_dic_list

    # -------------------- 对外接口 --------------------

    def extract_info(self) -> dict:
        """
        提取预警单信息，返回扁平结构字典（保留 v1 所有字段）。

        新增 risk_table 字段：有表格时返回表格数据，无表格时退化为单条记录。
        """
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

        if len(self.risk_table_data) > 0:
            dic["risk_table"] = self.risk_table_data
        else:
            # 无表格时退化为单条记录
            dic["risk_table"] = [{
                "name": dic["name"][:-2] if len(dic["name"]) > 2 else dic["name"],
                "code": extract_cve_code(dic["name"]),
                "desc": dic["desc"],
                "influence": dic["influence"],
                "check": dic["check"],
                "repair": dic["repair"],
                "requirement": dic["requirement"]
            }]
        return dic


if __name__ == "__main__":
    path1 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202505010L3.pdf"
    wh = WarningHelper(path1)
    dic = wh.extract_info()
    for k, v in dic.items():
        print(f"{k}: {v}")
