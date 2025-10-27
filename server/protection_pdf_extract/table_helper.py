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


# 通过blocks判断是否含有倾斜文字水印
def contain_mark(blocks):
    for block in blocks:
        type_info = block["type"]
        if type_info != 0:  # 非文字block
            continue
        lines = block['lines']
        for line in lines:
            dir = line["dir"]
            if dir[0] != 1.0 or dir[1] != 0.0:  # 去除倾斜方向的文字
                return True
    return False


# 获取table数据，以列表的形式
def get_table_data(table: pymupdf.table.Table, mark_flag: bool, blocks: list):
    table_info = TableInfo(table, mark_flag, blocks)
    return table_info.get_table()


class TableHelper:
    def __init__(self, pdf_path, start_page, end_page, start_chapter, end_chapter):
        self.pdf_path = pdf_path
        self.snap_tolerance = 6  # 先设置为4吧,目前看能较好处理 # 这个到时候需要不断判断,动态调整, 这个后续使用默认的
        self.start_page = start_page
        self.end_page = end_page  # 需要确定end_page是否包含表格，包含的表格是否和之前表格相同
        self.start_content = start_chapter
        self.end_content = end_chapter

        try:
            self.doc = pymupdf.open(self.pdf_path)
            self.mark_flag = self.__contain_mark()
            first_table = self.__get_first_table()
            first_table_data = get_table_data(first_table, self.mark_flag, self.__get_blocks(self.start_page))
            self.header_list = first_table_data[0]
            self.column_num = len(self.header_list)
            self.data_list = []
            self.__handle_first_table_data(first_table_data)
            self.__handle_pages()
            self.__handle_last_page()
            self.merge_table = self.__merge_info()
        finally:
            self.doc.close()

    def __contain_mark(self):  # 判断是否包含水印
        page = self.__get_page(self.start_page)
        blocks = page.get_text("dict")['blocks']
        return contain_mark(blocks)

    def __get_blocks(self, page_num):
        page = self.__get_page(page_num)
        blocks = page.get_text("dict")['blocks']
        return blocks

    def __get_tables(self, page):
        page = self.doc.load_page(page - 1)
        # tables = page.find_tables(join_tolerance=10, snap_tolerance=self.snap_tolerance)
        tables = page.find_tables()
        return tables.tables

    def __get_page(self, page):
        return self.doc.load_page(page - 1)

    def __get_page_bbox(self, page):
        page = self.__get_page(page)
        return page.rect

    # 确定范围截取内容
    def __get_tables_by_bbox(self, page: int, bbox: (float, float, float, float)):
        page = self.doc.load_page(page - 1)
        # tables = page.find_tables(clip=bbox, join_tolerance=5, snap_tolerance=self.snap_tolerance)
        tables = page.find_tables(clip=bbox)
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
            table_data = get_table_data(table, self.mark_flag, self.__get_blocks(self.end_page))
            table_data = table_data[1:]
            for line_list in table_data:
                clean_list(line_list)
                self.data_list.append(line_list)

    def __handle_pages(self):
        for page in range(self.start_page + 1, self.end_page):
            tables = self.__get_tables(page)
            if len(tables) == 0:
                break
            else:
                table = tables[0]
                table_data = get_table_data(table, self.mark_flag, self.__get_blocks(page))
                table_data = table_data[1:]
                for line_list in table_data:
                    self.data_list.append(line_list)

    # 根据每一行信息，合并跨页表格(需要判断跨页的表格)
    def __merge_info(self) -> list[list[str]]:
        res = []
        for line_list in self.data_list:
            if len(res) == 0:
                res.append(line_list)
            else:
                # 最后一列
                risk_level = line_list[-1]
                if risk_level:  # 有风险等级，说明是一行数据
                    if check_all_fill(line_list):  # 每列都有信息
                        res.append(line_list)
                    else:  # 有的列没有信息
                        for col_idx in range(self.column_num):
                            if not line_list[col_idx]:
                                line_list[col_idx] = res[-1][col_idx]
                        res.append(line_list)
                else:  # 没有风险等级，说明需要和上一行合并
                    for col_idx in range(0, self.column_num - 1):
                        txt = line_list[col_idx]
                        if txt:
                            res[-1][col_idx] += txt
        return res


if __name__ == "__main__":

    #
    pdf_path = r"D:\github\CSM-Service\file\09\银阳电站电力监控子系统_测评报告（中卫第四十光伏电站）.pdf"
    start_page = 169
    end_page = 180
    start_content = '安全问题风险分析'
    end_content = '等级测评结论'

    th = TableHelper(pdf_path, start_page, end_page, start_content, end_content)
    print(th.header_list)
    data_list = th.merge_table
    for line in data_list:
        print(line)
