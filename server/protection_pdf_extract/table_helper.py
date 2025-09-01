# 从指定页码范围内 提取安全问题风险分析表，识别跨页表格
import pymupdf
from server.tools.base import sort_block, contain_key, clean
from server.protection_pdf_extract.table_info import TableInfo


# 安全通用要求这一行是多列合并，需要删除
# 安全通用在表头下面
def need_drop(line_list) -> bool:
    length = len(line_list)
    empty_num = 0
    str_flag = False
    for line in line_list:
        if line == '':
            empty_num += 1
        elif contain_key(line, '安全通用要求'):
            str_flag = True
    if empty_num == length - 1 and str_flag:
        return True
    return False


def clean_list(arr: list[str]):
    length = len(arr)
    for i in range(length):
        if arr[i] is None:
            arr[i] = ""
        else:
            arr[i] = clean(arr[i])


# 判断一行多列是否都有信息
def check_all_fill(line_list) -> bool:
    for txt in line_list:
        if not txt:
            return False
    return True


# page_bbox是整页的x0,y0,x1,y1坐标
# text_bbox是文本段的x0,y0,x1,y1坐标
# 该函数是获取text_bbox下面的所有区域
def get_below_bbox(page_bbox, text_bbox):
    page_x0, page_y0, page_x1, page_y1 = page_bbox
    text_x0, text_y0, text_x1, text_y1 = text_bbox
    return page_x0, text_y1, page_x1, page_y1


# page_bbox是整页的x0,y0,x1,y1坐标
# text_bbox是文本段的x0,y0,x1,y1坐标
# 该函数是获取text_bbox上面的所有区域
def get_upper_bbox(page_bbox, text_bbox):
    page_x0, page_y0, page_x1, page_y1 = page_bbox
    text_x0, text_y0, text_x1, text_y1 = text_bbox
    return page_x0, page_y0, page_x1, text_y0


class TableHelper:
    def __init__(self, pdf_path, start_page, end_page, start_chapter, end_chapter):
        self.pdf_path = pdf_path
        self.snap_tolerance = 6  # 先设置为6吧,目前看能较好处理 # 这个到时候需要不断判断,动态调整
        self.start_page = start_page
        self.end_page = end_page  # 需要确定end_page是否包含表格，包含的表格是否和之前表格相同
        self.start_content = start_chapter
        self.end_content = end_chapter
        try:
            self.doc = pymupdf.open(self.pdf_path)
            first_table = self.__get_first_table()
            first_table_data = self.__get_table_data(first_table, self.start_page)
            self.header_list = first_table_data[0]
            self.column_num = len(self.header_list)
            self.data_list = []
            self.__handle_first_table_data(first_table_data)
            self.__handle_pages()
            self.__handle_last_page()
            self.merge_table = self.__merge_info()
        finally:
            self.doc.close()

    def __get_table_data(self, table: pymupdf.table.Table, page_num: int):
        page = self.__get_page(page_num)
        blocks = page.get_text("dict")['blocks']
        table_info = TableInfo(table)
        table_info.fill_info(blocks)
        return table_info.get_table()

    def __get_tables(self, page):
        page = self.doc.load_page(page - 1)
        tables = page.find_tables(join_tolerance=10, snap_tolerance=self.snap_tolerance)
        return tables.tables

    def __get_page(self, page):
        return self.doc.load_page(page - 1)

    def __get_page_bbox(self, page):
        page = self.__get_page(page)
        return page.rect

    # 确定范围截取内容
    def __get_tables_by_bbox(self, page: int, bbox: (float, float, float, float)):
        page = self.doc.load_page(page - 1)
        tables = page.find_tables(clip=bbox, join_tolerance=10, snap_tolerance=self.snap_tolerance)
        return tables.tables

    # 获取包含text内容的bbox四元组信息
    # 按照位置从上往下开始寻找
    def __get_bbox(self, page_num: int, key: str) -> (float, float, float, float):
        page = self.__get_page(page_num)
        blocks = page.get_text("blocks")
        # 进行排序，从上到下排序
        sorted_lst = sort_block(blocks)
        for x0, y0, x1, y1, text, _, _ in sorted_lst:
            if contain_key(text, key):
                return x0, y0, x1, y1

    # 获取第一个表格
    def __get_first_table(self):
        # stage1, 获取 安全问题风险分析 下面的bbox
        text_bbox = self.__get_bbox(self.start_page, self.start_content)
        page_bbox = self.__get_page_bbox(self.start_page)
        target_bbox = get_below_bbox(page_bbox, text_bbox)
        # stage2 确定是否有表格,如果没有表格，那么从下一页提取
        tables = self.__get_tables_by_bbox(self.start_page, target_bbox)
        if len(tables) == 0:  # 表明首页没有表格
            self.start_page += 1
            tables = self.__get_tables(self.start_page)
        # tables是一个列表，只取第一个。
        table = tables[0]
        return table

    # 需要查看是否有安全通用要求
    def __handle_first_table_data(self, first_table_data):
        table = first_table_data[1:]
        for index, line_list in enumerate(table):
            if index == 0 and need_drop(line_list):  # 多个单元格合并
                continue
            else:
                self.data_list.append(line_list)

    # 处理最后一页。最后一页 测评上面有表格就提取内容，没表格就忽略
    def __handle_last_page(self):
        # stage1, 获取 等保测评 上面的bbox
        text_bbox = self.__get_bbox(self.end_page, self.end_content)
        page_bbox = self.__get_page_bbox(self.end_page)
        target_bbox = get_upper_bbox(page_bbox, text_bbox)
        # stage2 确定是否有表格,如果没有表格,结束
        tables = self.__get_tables_by_bbox(self.end_page, target_bbox)
        if len(tables) != 0:
            table = tables[0]
            table_data = self.__get_table_data(table, self.end_page)
            table_data = table_data[1:]
            for line_list in table_data:
                clean_list(line_list)
                self.data_list.append(line_list)

    def __handle_pages(self):
        for page in range(self.start_page + 1, self.end_page):
            tables = self.__get_tables(page)
            table = tables[0]
            table_data = self.__get_table_data(table, page)
            table_data = table_data[1:]
            for line_list in table_data:
                self.data_list.append(line_list)

    # 根据每一行信息，合并跨页表格
    def __merge_info(self) -> list[list[str]]:
        res = []
        for line_list in self.data_list:
            if len(res) == 0:
                res.append(line_list)
            else:
                # 第一列
                num = line_list[0]
                if num:  # None 或者 '' 有问题编号
                    if check_all_fill(line_list):  # 每列都有信息
                        res.append(line_list)
                    else:  # 有的列没有信息
                        for col_idx in range(self.column_num):
                            if not line_list[col_idx]:
                                line_list[col_idx] = res[-1][col_idx]
                        res.append(line_list)
                else:  # None 或者 '' 没有问题编号
                    for col_idx in range(1, self.column_num):
                        txt = line_list[col_idx]
                        if txt:
                            res[-1][col_idx] += txt
        return res


if __name__ == "__main__":
    # # ok
    # pdf_path = "../files/DB-2003-0034_国网天津市电力公司滨海供电分公司调度自动化系统_测评报告.pdf"
    # start_page = 144
    # end_page = 175
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ok
    # pdf_path = "../files/5-1网络安全等级保护测评报告调度管理.pdf"
    # start_page = 91
    # end_page = 93
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ok
    # pdf_path = "../files/青龙山第二储能电站电力监控系统等级测评报告.pdf"
    # start_page = 95
    # end_page = 109
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ok
    # pdf_path = "../files/吴忠第五十光伏电站电力监控系统等级保护测评.pdf"
    # start_page = 146
    # end_page = 182
    # start_content = '安全问题风险分析'
    # end_content = '总体评价'

    # ok
    # pdf_path = "../files/国网银川供电公司银川智能电网调度控制系统等级测评报告-2024-Z.pdf"
    # start_page = 161
    # end_page = 168
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ok
    # pdf_path = "../files/国能宁东新能源有限公司330千伏曙光变电力监控系统（S2A3）网络安全等级保护测评报告.pdf"
    # start_page = 103
    # end_page = 113
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ok
    # pdf_path = "../files/5-1网络安全等级保护测评报告-实时监控.pdf"
    # start_page = 178
    # end_page = 188
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ------------- 测试带水印的两个文件效果
    # ok
    # pdf_path = "../files/mark/等级测评报告-宁夏翔腾电源科技有限公司-江汉第二储能电站电力监控系统.pdf"
    # start_page = 97
    # end_page = 108
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ok
    # pdf_path = "../files/mark/盖章版_等保_宁夏超高压-新一代集控站设备监控系统-终.pdf"
    # start_page = 115
    # end_page = 125
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ok
    # pdf_path = "../files/mark/DB-2405-0051_国网天津市电力公司国网天津市电力公司智能电网调度技术支持系统实时监控与预警系统主备一体系统_测评报告.pdf"
    # start_page = 128
    # end_page = 146
    # start_content = '安全问题风险分析'
    # end_content = '等级测评结论'

    # ok
    pdf_path = r"D:\code\CSM-Service\files\mark\DB-2405-0051_国网天津市电力公司国网天津市电力公司智能电网调度技术支持系统实时监控与预警系统主备一体系统_测评报告.pdf"
    start_page = 72
    end_page = 73
    start_content = '安全问题风险分析'
    end_content = '等级测评结论'

    th = TableHelper(pdf_path, start_page, end_page, start_content, end_content)
    print(th.header_list)
    data_list = th.merge_table
    for line in data_list:
        print(line)
