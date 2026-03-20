import os

from server.protection_pdf_extract.extract_api import extract_safe_table, output_standard, empty_return_dic, \
    output_is_valid


def extract_table(pdf_path: str):
    try:
        table_list = extract_safe_table(pdf_path)
        res = output_standard(table_list)
        return res
    except Exception as e:
        return [empty_return_dic]

# empty_return_dic = {
#     "content": "",
#     "riskLevel": 0,
#     "securityType": 0,
#     "evaluationObject": ""
# }

def list_file(dir_path: str):
    file_list = os.listdir(dir_path)
    return file_list


if __name__ == "__main__":
    dir_path = r"D:\工作\科东\智能安全研发分部\CSM\csm本地安装\表格提取csm服务\等保测评所有文件"
    file_list = list_file(dir_path)
    total_num = len(file_list)
    error_num = 0
    for file in file_list:
        pdf_path = os.path.join(dir_path, file)
        res = extract_table(pdf_path)
        valid_flag = output_is_valid(res)
        if not valid_flag:
            error_num += 1

        print(f"{file}, success: {valid_flag}" )
        print(res)
        print("==============================")
    print(f"total_num: {total_num}, error_num: {error_num}")


# 中卫第四十七光伏电站电力监控系统_测评报告.pdf 这个文件有问题