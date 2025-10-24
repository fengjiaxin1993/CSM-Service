import os
from fastapi import UploadFile, File
from server.tools.base import split_line, shorten_filename
from server.protection_pdf_extract.outline_helper import OutlineHelper
from server.protection_pdf_extract.table_helper import TableHelper
from config.basic_config import BASE_TEMP_DIR
import logging

logger = logging.getLogger(__name__)


# 从目录中找出 安全问题风险分析 这一章节和下一章节对应的页码
def get_outline_info(
        pdf_path: str,
        start_chapter: str = '安全问题风险分析') -> dict:
    oh = OutlineHelper(pdf_path=pdf_path, keyword=start_chapter)
    return {"start_page": oh.start_page,
            "end_page": oh.end_page,
            "start_chapter": oh.start_content,
            "end_chapter": oh.end_content}


# 抽取表格,返回表格，第一行是表头
def extract_table(
        pdf_path: str,
        start_page: int,
        end_page: int,
        start_chapter: str,
        end_chapter: str) -> list[list[str]]:
    th = TableHelper(pdf_path, start_page, end_page, start_chapter, end_chapter)
    table_list = [th.header_list]
    for line in th.merge_table:
        table_list.append(line)
    return table_list


# 将提取的表格修改后，逐项提出，将关联资产划分
def split_table(
        table_list: list[list[str]],
        split_char_list: list = list['、', '，'],
        key: str = '关联资产') -> list[list[str]]:
    header_list = table_list[0]
    data_list = table_list[1:]
    split_data_list = split_line(header_list, data_list, split_char_list, key)
    res_table_list = [header_list]
    for line in split_data_list:
        res_table_list.append(line)
    return res_table_list


def extract_safe_table(pdf_path: str) -> list[list[str]]:
    oh = OutlineHelper(pdf_path=pdf_path)
    if oh.is_valid():
        return extract_table(pdf_path, oh.start_page, oh.end_page, oh.start_chapter, oh.end_chapter)
    else:
        return empty_table_list


def extract_safe_split_table(pdf_path: str) -> list[list[str]]:
    table_list = extract_safe_table(pdf_path)
    if len(table_list) > 1:
        split_key = '关联资产'
        split_char_list = ['、', '，', ',']
        return split_table(table_list, split_char_list, split_key)
    else:
        return table_list


def upload_extract_safe_table(
        file: UploadFile = File(..., description="上传文件"),
) -> list[dict]:
    """
    将文件保存到临时目录.
    找到安全问题风险分析的表格，解决跨页问题，提取出原始表格。
    """
    try:

        file_content = file.file.read()  # 读取上传文件的内容
        short_filename = shorten_filename(file.filename)
        new_file_path = os.path.join(BASE_TEMP_DIR, short_filename)
        with open(new_file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"{file.filename} 文件保存成功!")
        table_list = extract_safe_table(new_file_path)
        res = output_standard(table_list)
        return res
    except Exception as e:
        msg = f"{file.filename} 文件解析失败，报错信息为: {e}"
        logger.error(msg)
        return [empty_return_dic]


def upload_extract_safe_split_table(
        file: UploadFile = File(..., description="上传文件"),
) -> list[dict]:
    """
        将文件保存到临时目录.
        找到安全问题风险分析的表格，解决跨页问题，提取出原始表格后，对表格列（关联资产）进行划分，形成更详细的表格,json格式返回
        """
    try:

        file_content = file.file.read()  # 读取上传文件的内容
        short_filename = shorten_filename(file.filename)
        new_file_path = os.path.join(BASE_TEMP_DIR, short_filename)
        with open(new_file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"【{short_filename}】 文件保存成功!")
        table_list = extract_safe_split_table(new_file_path)
        res = output_standard(table_list)
        return res
    except Exception as e:
        msg = f"解析{file.filename} 失败，报错信息为: {e}"
        logger.error(msg)
        return [empty_return_dic]


def remove_digit_str(str):
    return ''.join([i for i in str if not i.isdigit()])


standard_column_names = ["问题描述", "风险等级", "安全类型", "关联资产"]
match_dict = {
    "content": ["安全问题", "问题描述"],
    "riskLevel": ["风险等级"],
    "securityType": ["安全类", "安全类型"],
    "evaluationObject": ["关联资产"]
}
empty_return_dic = {
    "content": "",
    "riskLevel": 0,
    "securityType": 0,
    "evaluationObject": ""
}

empty_table_list = [[]]

# 安全类型 对应的编码
securityType_dic = {
    "安全通信网络": 1,
    "安全区域边界": 2,
    "安全计算环境": 3,
    "安全管理中心": 4,
    "安全运维管理": 5,
    "安全物理环境": 6,
    "安全管理制度": 7,
    "安全管理机构": 8,
    "安全管理人员": 9,
    "安全建设管理": 10
}

#风险等级 对应的编码
riskType_dic = {
    "高": 1001,
    "中": 1002,
    "低": 1003
}


def get_risk_code(risk_info: str) -> int:
    return riskType_dic.get(risk_info, 0)


def get_securityType_code(security_info: str) -> int:
    return securityType_dic.get(security_info, 0)


def column_match(column_name):
    column_name = remove_digit_str(column_name)
    for k, vlist in match_dict.items():
        if column_name in vlist:
            return k
    return ""


# 一行数据转换成{}格式
def line2dic(header_list: list[str], data_list: list[str]) -> dict:
    dic = {}
    for idx, column in enumerate(header_list):
        standard_name = column_match(column)
        if standard_name != "":
            data = data_list[idx]
            if standard_name == "riskLevel":
                dic[standard_name] = get_risk_code(data)
            elif standard_name == "securityType":
                dic[standard_name] = get_securityType_code(data)
            else:
                dic[standard_name] = data
    return dic


def output_standard(table_list: list[list[str]]) -> list[dict]:
    if len(table_list) <= 1:
        return [empty_return_dic]
    else:
        res = []
        header_list = table_list[0]
        for data_list in table_list[1:]:
            res.append(line2dic(header_list, data_list))
        return res


def name_standard(dic: dict) -> dict:
    res_dic = {}
    for col, v in dic.items():
        standard_col = column_match(col)
        if standard_col != "":
            res_dic[standard_col] = v
    return res_dic


def unmark_test():
    # ok
    pdf_path1 = r"D:\code\CSM-Service\files\unmark\5-1网络安全等级保护测评报告-实时监控.pdf"

    # ok
    pdf_path2 = r"D:\code\CSM-Service\files\unmark\5-1网络安全等级保护测评报告调度管理.pdf"

    # ok
    pdf_path3 = r"D:\code\CSM-Service\files\unmark\7-1 DB-2308-0028_天津市滨海新区金开新能源科技有限公司金开新能锦湖轮胎18MW分布式光伏电站监控_测评报告.pdf"

    # ok
    pdf_path4 = r"D:\code\CSM-Service\files\unmark\7-1 DB-2401-0023_天津悦通达新能源科技有限公司110KV悦通达风电场电力监控系统_测评报告.pdf"

    # ok
    pdf_path5 = r"D:\code\CSM-Service\files\unmark\DB-2003-0034_国网天津市电力公司滨海供电分公司调度自动化系统_测评报告.pdf"

    # ok
    pdf_path6 = r"D:\code\CSM-Service\files\unmark\刘岗庄网络安全等级保护测评报告-.pdf"

    # ok
    pdf_path7 = r"D:\code\CSM-Service\files\unmark\吴忠第五十光伏电站电力监控系统等级保护测评.pdf"

    # ok
    pdf_path8 = r"D:\code\CSM-Service\files\unmark\国网银川供电公司银川智能电网调度控制系统等级测评报告-2024-Z.pdf"

    # ok
    pdf_path9 = r"D:\code\CSM-Service\files\unmark\国能宁东新能源有限公司330千伏曙光变电力监控系统（S2A3）网络安全等级保护测评报告.pdf"

    # ok
    pdf_path10 = r"D:\code\CSM-Service\files\unmark\青龙山第二储能电站电力监控系统等级测评报告.pdf"

    table_list = extract_safe_split_table(pdf_path10)
    res = output_standard(table_list)
    print(res)


def mark_test():
    # ok
    pdf_path1 = r"D:\code\CSM-Service\files\mark\DB-2405-0051_国网天津市电力公司国网天津市电力公司智能电网调度技术支持系统实时监控与预警系统主备一体系统_测评报告.pdf"

    # ok
    pdf_path2 = r"D:\code\CSM-Service\
    files\mark\DB-2405-0051_国网天津市电力公司国网天津市电力公司智能电网调度技术支持系统调度计划与安全校核系统_测评报告.pdf"

    # ok
    pdf_path3 = r"D:\code\CSM-Service\files\mark\盖章版_等保_宁夏超高压-新一代集控站设备监控系统-终.pdf"

    # ok
    pdf_path4 = r"D:\code\CSM-Service\files\mark\等级测评报告-宁夏翔腾电源科技有限公司-江汉第二储能电站电力监控系统.pdf"

    table_list = extract_safe_split_table(pdf_path2)
    res = output_standard(table_list)
    print(res)


# 解决问题1
def new_test1():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\01\SA-MI07-HT24031-CP24705_张易第一风电场电力监控系统_测评报告.pdf"

    # ok
    pdf_path2 = r"D:\github\CSM-Service\file\01\中卫第六十一光伏电站电力监控系统_测评报告 .pdf"

    # ok
    pdf_path3 = r"D:\github\CSM-Service\file\01\中宁县欣文新能源有限公司-中卫第六十四光伏电站电力监控系统等级测评报告.pdf"

    # ok
    pdf_path4 = r"D:\github\CSM-Service\file\01\中宁第六十光伏电站测评报告终版2024.pdf"

    # ok
    pdf_path5 = r"D:\github\CSM-Service\file\01\吴忠市瑞储科技有限公司-泉眼第三储能电站电力监控系统-等级测评报告.pdf"

    table_list = extract_safe_split_table(pdf_path5)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题2
def new_test2():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\02\中卫第四十七光伏电站电力监控系统_测评报告.pdf"

    table_list = extract_safe_split_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题3
def new_test3():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\03\向阳第一储能电站电力监控系统测评报告(盖章版) .pdf"

    # ok
    pdf_path2 = r"D:\github\CSM-Service\file\03\吴忠第五十光伏电站电力监控系统等级保护测评 (1).pdf"

    # ok
    pdf_path3 = r"D:\github\CSM-Service\file\03\星能第四风电场电力监控系统测评报告.pdf"

    # ok
    pdf_path4 = r"D:\github\CSM-Service\file\03\杨家窑第三风电场监控系统等保测评报告.pdf"

    # ok
    pdf_path5 = r"D:\github\CSM-Service\file\03\杨家窑第二风光电场电力监控系统等保测评报告.pdf"

    # ok
    pdf_path6 = r"D:\github\CSM-Service\file\03\电力监控系统测评报告-嘉泽第一风电场.pdf"

    # ok
    pdf_path7 = r"D:\github\CSM-Service\file\03\T2024072303250001_国家电投集团宁夏能源铝业中卫新能源有限公司_国电投框架-宁夏-铝电公司中卫新能源香山第六风电场及沙梁110kV变电站监控系统第三级信息系统等级保护测评报告-出口复核-二次邮寄-1-V69298 (1).pdf"


    table_list = extract_safe_split_table(pdf_path7)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)



# 解决问题4
def new_test4():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\04\XMBH2025050924+6001523 绿塬第一储能电站电力控制系统v1.0(3) (1).pdf"

    table_list = extract_safe_split_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题6
def new_test6():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\06\中铝宁夏能源集团马莲台发电分公司NCS变电站（S3A2）网络控制系统网络安全等级保护测评报告 - 盖章.pdf"

    table_list = extract_safe_split_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)

# 解决问题8
def new_test8():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\08\银川第四光伏电站电力监控系统测评报告(2024).pdf"

    table_list = extract_safe_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)

# 解决问题9
def new_test9():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\09\银阳电站电力监控子系统_测评报告（中卫第四十光伏电站）.pdf"

    table_list = extract_safe_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)

if __name__ == '__main__':
    new_test1()
