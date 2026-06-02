# 预警单信息提取

import pymupdf
import re

"""
预警单块信息如下

1.预警等级/预警级别
2.预警编号/编号
3.预警名称/风险名称
4.通知范围
5.抄送
6.风险描述  （下面一大段话）
7.影响范围
8.排查方式
9.处置方式/修复方式
10.工作要求
11.联系人

预警级别、编号、风险名称、通知范围、抄送 都是 key:value格式
其余的是 段落描述

需要提取的内容如下
预警名称 name
预警编号 code
预警等级 level
风险描述 desc
影响范围 influence
排查方式 check
修复方式 repair
工作要求 requirement

"""


def contain_key(text, keyword):
    result_match = re.search(keyword, text)
    if result_match:
        return True
    else:
        return False


def get_middle_text(text, start_text, end_text):
    # 找到开始文本和结束文本的位置
    start_index = text.find(start_text) + len(start_text)
    if end_text != "":
        end_index = text.find(end_text)
        # 提取中间内容
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
    text = text.strip()
    text = text.replace(" ", "")
    text = text.replace("\n", "")
    return text


def text_clean(text):
    text = text.strip()
    text = text.replace(" ", "")
    text = text.replace("\n", " ")
    return text


# 关键字同义词字典
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
    dic = {}
    for k, vs in origin_dic.items():
        for v in vs:
            dic[v] = k
    return dic


chinese_value_key_dict = get_normalize_match_dict(chinese_key_values_dict)


def get_warning_level_int(war: str) -> int:
    if war == "紧急":
        return 1
    elif war == "重要":
        return 2
    elif war == "一般":
        return 3
    else:
        return 0


# CVE-2024-21733 / SGVD202510003
# cve编号格式如上
def extract_cve_code(txt: str) -> str:
    cve_pattern = re.compile(r'CVE-\d{4}-\d+')  # 匹配CVE格式
    sgvd_pattern = re.compile(r'SGVD\d{4}\d+')  # 匹配SGVD格式

    # 提取匹配结果
    cve_list = cve_pattern.findall(txt)
    sgvd_list = sgvd_pattern.findall(txt)
    cve_list.extend(sgvd_list)
    return ",".join(cve_list)


def remove_water(text, water_set: set):
    if text:
        for water in water_set:
            for ch in water:
                text = text.replace(ch, "")
        return text_clean(text)
    return text


# 第一行是head, 之后一一对应

def get_target_idx(header:list, target:str):
    for idx, head in enumerate(header):
        if target in head:
            return idx
    return -1

empty_dic = {
    "name": "",
    "code": "",
    "level": 0,
    "influence": "",
    "risk_table": [{"name": "", "code": "", "desc": "", "influence": "", "check": "", "repair": "", "requirement": ""}]
}




class WarningHelper:
    def __init__(self, path: str):
        self.path = path
        self.chinese_key_values_dict = chinese_key_values_dict  # key 对应 多个values词典
        self.chinese_value_key_dict = chinese_value_key_dict  # 找到value 对应的标准key
        self.span_list = []
        self.risk_table_data = []  # 风险描述与影响范围之间的表格数据
        self.water_text_set = set()
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
                            direction = line["dir"]  # 获取文字方向向量
                            if direction[0] != 1.0 or direction[1] != 0.0:  # 去除倾斜方向的文字
                                for span in spans:  # 记录倾斜文字水印
                                    text = span['text']
                                    self.water_text_set.add(text)
                                continue
                            self.span_list.extend(spans)
            self.text = self.get_text()
            # 在 doc 打开期间完成表格提取
            self.water_mark_flag = len(self.water_text_set) > 0
            self._extract_risk_table()
        finally:
            self.doc.close()
            self.doc = None

    def __get_normalize_match_dict(self) -> dict:
        dic = {}
        for k, vs in self.chinese_key_values_dict.items():
            for v in vs:
                dic[v] = k
        return dic

    def get_text(self):
        text_list = []
        for span in self.span_list:
            text = span['text']
            text = text_strip(text)
            if contain_key(text, "联系人"):
                break
            else:
                nor_text = self.normalize_text(text)
                text_list.append(nor_text)
        return "\n".join(text_list)

    def normalize_text(self, text):  # 对文本归一化
        for name, standard in self.chinese_value_key_dict.items():
            if contain_key(text, name):
                text = text.replace(name, standard)
        return text

    # ==================== 表格提取相关方法 ====================

    def _get_keyword_bbox(self, page_idx: int, keyword: str):
        """在指定页中查找包含 keyword 的第一个文本元素，返回其 bbox (x0, y0, x1, y1)，未找到返回 None。
        优先搜索文本块，若找不到则在表格中搜索。
        """
        page = self.doc.load_page(page_idx)

        # 方法1：搜索文本块（按 y0 从上到下排序）
        blocks = page.get_text("blocks")
        sorted_lst = sorted(blocks, key=lambda x: x[1])  # 按 y0（上边界）排序
        for x0, y0, x1, y1, text, _, _ in sorted_lst:
            if contain_key(text, keyword):
                return (x0, y0, x1, y1)
        return None

    def _extract_risk_table(self):
        """
        使用 find_tables() 提取"风险描述"下方到"影响范围"上方之间的表格数据。
        判断逻辑：表格 bbox 与两个关键词之间的 y 区间有交集即纳入。
        """
        risk_y = None  # "风险描述"关键词的顶部 y 坐标
        risk_page = -1
        influence_y = None  # "影响范围"关键词的顶部 y 坐标
        influence_page = -1

        for page_idx in range(self.doc.page_count):
            if risk_y is None:
                bbox = self._get_keyword_bbox(page_idx, "风险描述")
                if bbox:
                    risk_y = bbox[1]  # 关键词块的顶部
                    risk_page = page_idx
            if influence_y is None:
                bbox = self._get_keyword_bbox(page_idx, "影响范围")
                if bbox:
                    influence_y = bbox[1]  # 关键词块的顶部
                    influence_page = page_idx
            if risk_y is not None and influence_y is not None:
                break

        if risk_y is None or influence_y is None:
            print("[WARN] 未找到'风险描述'或'影响范围'，跳过表格提取")
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

            # === 核心：用 find_tables() 找表格 ===
            find_result = page.find_tables()
            if hasattr(find_result, 'tables'):
                tables = find_result.tables
            else:
                tables = find_result

            for table in tables:
                t_bbox = table.bbox  # (x0, y0, x1, y1)
                # 表格与关键词区间有交集
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
        self.risk_table_data = self.convert_table(table_data)

    def _merge_cross_page_tables(self, all_page_rows):
        """
        合并跨页表格。
        all_page_rows: list of (page_idx, rows)
        - 只有跨页（page_idx 不同）且列数相同时才合并（同页多张表独立保留）
        - 合并时跳过重复表头（当前表头与上一张表头相同则去重）
        """
        if len(all_page_rows) <= 1:
            return all_page_rows[0][1] if all_page_rows else []

        # 第一张表的全部行作为起点
        prev_page, prev_rows = all_page_rows[0]
        merged = list(prev_rows)

        for i in range(1, len(all_page_rows)):
            curr_page, curr_rows = all_page_rows[i]

            if not prev_rows or not curr_rows:
                prev_page, prev_rows = curr_page, curr_rows
                continue

            prev_last_cols = len(prev_rows[-1])
            curr_first_cols = len(curr_rows[0])

            # 只有不同页且列数一致才当作同一张表跨页
            if curr_page != prev_page and prev_last_cols == curr_first_cols:
                start = 0
                # 当前表头与上一张表头相同 → 跳过重复表头
                if curr_rows[0] == prev_rows[0]:
                    start = 1
                merged.extend(curr_rows[start:])
            else:
                merged.extend(curr_rows)

            prev_page, prev_rows = curr_page, curr_rows

        return merged

    def extract_risk_table(self) -> list[list[str]]:
        """返回 风险描述 与 影响范围 之间的表格数据"""
        return self.risk_table_data

    # ==================== 表格提取相关方法结束 ====================

    def __extract_level(self):  # 提取 预警等级
        start_content = "预警等级："
        end_content = "预警编号"
        return text_strip(get_middle_text(self.text, start_content, end_content))

    def __extract_code(self):  # 提取 预警编号
        start_content = "预警编号："
        end_content = "预警名称"
        return text_strip(get_middle_text(self.text, start_content, end_content))

    def __extract_name(self):  # 提取 风险名称
        start_content = "预警名称："
        end_content = "通知范围"
        return text_strip(get_middle_text(self.text, start_content, end_content))

    def __extract_cve_code(self):  # 提取 风险描述
        start_content = "风险描述\n"
        end_content = "影响范围\n"
        risk_desc = get_middle_text(self.text, start_content, end_content)
        return extract_cve_code(risk_desc)

    def __extract_desc(self):  # 提取 风险描述
        start_content = "风险描述\n"
        end_content = "影响范围\n"
        risk_desc = get_middle_text(self.text, start_content, end_content)
        # 如果包含
        if contain_key(risk_desc, "漏洞信息如下"):
            risk_desc = get_middle_text(risk_desc, start_content, "漏洞信息如下")
        return text_strip(risk_desc)

    def __extract_influence(self):  # 提取 影响范围
        start_content = "影响范围\n"
        end_content = "排查方式\n"
        return text_clean(get_middle_text(self.text, start_content, end_content))

    def __extract_check(self):  # 提取 排查方式
        start_content = "排查方式\n"
        end_content = "修复方式\n"
        return text_strip(get_middle_text(self.text, start_content, end_content))

    def __extract_repair(self):  # 提取 修复方式
        start_content = "修复方式\n"
        end_content = "工作要求\n"
        return text_strip(get_middle_text(self.text, start_content, end_content))

    def __extract_requirement(self):  # 提取 工作要求
        start_content = "工作要求\n"
        end_content = ""
        return text_strip(get_middle_text(self.text, start_content, end_content))

    def convert_table(self,table_data: list[list[str]]) -> list:
        code_idx = get_target_idx(table_data[0], "编号")
        name_idx = get_target_idx(table_data[0], "名称")

        res_dic_list = []
        for row in table_data[1:]:
            dic = {
                "name": row[name_idx],
                "code": row[code_idx],
                "desc": self.__extract_desc(),
                "influence":self.__extract_influence(),
                "check":self.__extract_check(),
                "repair":self.__extract_repair(),
                "requirement":self.__extract_requirement()
            }
            res_dic_list.append(dic)
        return res_dic_list

    def extract_info(self) -> dict:
        dic = {}
        dic["name"] = self.__extract_name()
        dic["code"] = self.__extract_code()
        dic["level"] = get_warning_level_int(self.__extract_level())
        dic["influence"] = self.__extract_influence()
        if len(self.risk_table_data) > 0:
            dic["risk_table"] = self.risk_table_data
        else:
            dic["risk_table"] = [{
                "name": dic["name"][:-2],
                "code": extract_cve_code(dic["name"]),
                "desc": self.__extract_desc(),
                "influence": self.__extract_influence(),
                "check": self.__extract_check(),
                "repair": self.__extract_repair(),
                "requirement": self.__extract_requirement()
            }]
        return dic


if __name__ == "__main__":
    # path1 ok
    path1 = r"C:\Users\Administrator\Desktop\预警单示例\1 个漏洞.pdf"
    # # path2 ok
    # path2 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202503006L3.pdf"
    # # path3 ok
    # path3 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202505009L3.pdf"
    # # path4 ok
    # path4 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202505010L3.pdf"
    # # path5 ok
    # path5 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\WAYJ202507013L2银河麒麟、达梦等国产操作系统和数据库漏洞预警.pdf"
    # # path6 ok
    # path6 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\WAYJ202506011L221银河麒麟、统信、中科方德操作系统和虚谷数据库漏洞预警.pdf"
    # # ok
    # path7 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\WAYJ202512018L1.pdf"
    # # ok
    # path8 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202502003L2.pdf"
    # # ok
    # path9 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202503006L3.pdf"
    # # ok
    # path10 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202505009L3.pdf"
    # # ok
    # path11 = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\文件识别\预警单\预警-WAYJ202505010L3.pdf"
    wh = WarningHelper(path1)
    dic = wh.extract_info()
    for k, v in dic.items():
        print(f"{k}: {v}")
