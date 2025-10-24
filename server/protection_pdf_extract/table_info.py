from server.tools.base import is_contain, area_percent
import pymupdf.table
from server.tools.base import clean


class CellInfo:
    def __init__(self, bbox):
        self.__bbox = bbox
        self.__content_list = []

    def fill_content(self, content):
        self.__content_list.append(clean(content))

    def get_bbox(self):
        return self.__bbox

    def get_content(self):
        return "".join(self.__content_list)


# pymupdf 是这样解析 合并单元格的，只在最小坐标的单元格有cell，并且cell的bbox为合并后的大小，其他为None
def get_matrix(rows: list[pymupdf.table.TableRow], row_count: int, col_count: int):
    matrix = [[None for _ in range(col_count)] for _ in range(row_count)]
    for i in range(row_count):
        row = rows[i]
        for j in range(col_count):
            cell = row.cells[j]
            if cell is None:
                continue
            else:
                matrix[i][j] = CellInfo(cell)
    return matrix


# 存储TableInfo的详细信息
class TableInfo:
    def __init__(self, table: pymupdf.table.Table, mark_flag: bool, blocks: list):
        # ====1==== 获取表格的基本信息
        self.mark_flag = mark_flag
        self.table = table
        self.table_data = table.extract()
        # 行列基本信息
        self.row_count = self.table.row_count  # 行数
        self.col_count = self.table.col_count  # 列数
        # 表格总体bbox坐标
        self.table_bbox = self.table.bbox
        # 划分表格的信息
        self.rows = self.table.rows
        # blocks信息
        self.blocks = blocks

    def __find_xy_index(self, text_bbox):  # 找出text_bbox在matrix的哪个单元格中 # 这个要优化，用最大面积的方式解决
        target_i = -1
        target_j = -1
        max_perc = 0
        for i in range(self.row_count):
            for j in range(self.col_count):
                cellInfo = self.matrix[i][j]
                if cellInfo is None:
                    continue
                else:
                    text_perc = area_percent(text_bbox, cellInfo.get_bbox())
                    if text_perc > max_perc:
                        target_i = i
                        target_j = j
                        max_perc = text_perc
        return target_i, target_j

    def __fill_cell(self, text_bbox, text):  # 根据text_bbox找到在表格的位置，将内容填充
        x_idx, y_idx = self.__find_xy_index(text_bbox)
        self.matrix[x_idx][y_idx].fill_content(text)

    def __fill_info(self):
        for block in self.blocks:
            type_info = block["type"]
            block_bbox = block['bbox']
            if type_info != 0:  # 非文字block
                continue
            if not is_contain(self.table_bbox, block_bbox, thresold=0):  # 不在表格block中的文字舍弃
                continue
            lines = block['lines']
            for line in lines:
                spans = line["spans"]
                dir = line["dir"]
                if dir[0] != 1.0 or dir[1] != 0.0:  # 去除倾斜方向的文字
                    continue
                for span in spans:
                    span_text = span["text"]
                    span_bbox = span["bbox"]
                    self.__fill_cell(span_bbox, span_text)

    # 没有水印，直接通过第三方库获取数据
    def __get_unmark_table_data(self):
        table = [['' for _ in range(self.col_count)] for _ in range(self.row_count)]
        for i in range(self.row_count):
            for j in range(self.col_count):
                text = self.table_data[i][j]
                if text is not None:
                    text = clean(text)
                    table[i][j] = text
        return table

    # 有水印，通过block，判断bbox进行填充
    def __get_mark_table_data(self):
        self.matrix = get_matrix(self.rows, self.row_count, self.col_count)
        self.__fill_info()
        table = [['' for _ in range(self.col_count)] for _ in range(self.row_count)]
        for i in range(self.row_count):
            for j in range(self.col_count):
                cellInfo = self.matrix[i][j]
                if cellInfo:
                    table[i][j] = cellInfo.get_content()
        return table

    def get_table(self):
        if self.mark_flag:
            return self.__get_mark_table_data()
        else:
            return self.__get_unmark_table_data()
