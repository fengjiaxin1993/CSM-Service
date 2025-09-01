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


def get_warning_level_int(war: str) -> int:
    if war == "紧急":
        return 1
    elif war == "重要":
        return 2
    elif war == "一般":
        return 3
    else:
        return 0


class WarningHelper:
    def __init__(self, path: str):
        self.path = path
        self.chinese_key_values_dict = chinese_key_values_dict  # key 对应 多个values词典
        self.chinese_value_key_dict = self.__get_normalize_match_dict()  # 找到value 对应的标准key
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
                            direction = line["dir"]  # 获取文字方向向量
                            if direction[0] != 1.0 or direction[1] != 0.0:  # 去除倾斜方向的文字
                                continue
                            self.span_list.extend(spans)
        self.text = self.get_text()

    def __get_normalize_match_dict(self) -> dict:
        dic = {}
        for k, vs in self.chinese_key_values_dict.items():
            for v in vs:
                dic[v] = k
        return dic

    def get_text(self):
        text_list = []
        ignore_flag = False  # 包含漏洞信息如下
        for span in self.span_list:
            text = span['text']
            text = text_strip(text)
            if contain_key(text, "漏洞信息如下"):
                ignore_flag = True
                continue
            elif contain_key(text, "影响范围"):
                ignore_flag = False
                text_list.append(text)
            if contain_key(text, "联系人"):
                ignore_flag = True
            else:
                if not ignore_flag:
                    nor_text = self.normalize_text(text)
                    text_list.append(nor_text)
        return "\n".join(text_list)

    def normalize_text(self, text):  # 对文本归一化
        for name, standard in self.chinese_value_key_dict.items():
            if contain_key(text, name):
                text = text.replace(name, standard)
        return text

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

    def __extract_desc(self):  # 提取 风险描述
        start_content = "风险描述\n"
        end_content = "影响范围\n"
        return text_strip(get_middle_text(self.text, start_content, end_content))

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

    def extract_info(self) -> dict:
        dic = {}
        dic["name"] = self.__extract_name()
        dic["code"] = self.__extract_code()
        dic["level"] = get_warning_level_int(self.__extract_level())
        dic["desc"] = self.__extract_desc()
        dic["influence"] = self.__extract_influence()
        dic["check"] = self.__extract_check()
        dic["repair"] = self.__extract_repair()
        dic["requirement"] = self.__extract_requirement()
        return dic


if __name__ == "__main__":
    # path1 ok
    path1 = r"D:\code\extractFromPdf\yujing\预警-WAYJ202502003L2.pdf"
    # path2 ok
    path2 = r"D:\code\extractFromPdf\yujing\预警-WAYJ202503006L3.pdf"
    # path3 ok
    path3 = r"D:\code\extractFromPdf\yujing\预警-WAYJ202505009L3.pdf"
    # path4 ok
    path4 = r"D:\code\extractFromPdf\yujing\预警-WAYJ202505010L3.pdf"
    # path5 ok
    path5 = r"D:\code\extractFromPdf\yujing\WAYJ202507013L2银河麒麟、达梦等国产操作系统和数据库漏洞预警.pdf"
    # path6 ok
    path6 = r"D:\code\extractFromPdf\yujing\WAYJ202506011L221银河麒麟、统信、中科方德操作系统和虚谷数据库漏洞预警.pdf"
    wh = WarningHelper(path6)
    print(wh.text)
    dic = wh.extract_info()
    print(dic)
