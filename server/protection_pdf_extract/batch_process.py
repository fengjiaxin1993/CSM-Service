from server.protection_pdf_extract.extract_api import output_standard, extract_safe_split_table
import os


def single_process(pdf_path: str) -> set[tuple[str, int]]:
    """
        将文件保存到临时目录.
        找到安全问题风险分析的表格，解决跨页问题，提取出原始表格后，对表格列（关联资产）进行划分，形成更详细的表格,json格式返回
        """
    table_list = extract_safe_split_table(pdf_path)
    res = output_standard(table_list)
    res_set = set()
    for dic in res:
        res_set.add((dic['content'], dic['securityType']))
    return res_set


def batch_process(path_list: list) -> set[tuple[str, int]]:
    res_set = set()
    for path in path_list:
        try:
            res = single_process(path)
            res_set.update(res)
        except Exception:
            pass

    return res_set


def traverse_files(dir_path):
    path_list = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            path_list.append(file_path)
    return path_list


def handle(dir, output_path):
    path_list = traverse_files(dir)
    res_list = batch_process(path_list)
    with open(output_path, "w", encoding="utf-8") as w:
        w.write("text\tlabel\n")
        for text, label in res_list:
            w.write(text + "\t" + str(label) + "\n")


if __name__ == "__main__":
    dir_path = r"D:\工作\科东\智能安全研发分部\CSM\csm本地安装\表格提取csm服务\等保测评所有文件"
    output_path = r"D:\github\bert-tiny-train\data\dbcp.csv"
    handle(dir_path, output_path)
