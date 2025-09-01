import pymupdf.table

from server.tools.base import is_contain, clean, area_percent


# 处理方法
# 1. 先根据cell_bbox 确定 几行几列，根据x0坐标的数量确定列数，根据y0坐标的数量确定行数
# 2. 有些单元格合并了，需要 确定哪个个bbox 是合并的，共享一个表格内容
# 3. 根据block信息，定位block在哪个cell中, 将文字信息按照block从上往下加入到cell文本中

class CellInfo:
    def __init__(self, bbox):
        self.bbox = bbox
        self.content_list = []

    def fill_content(self, content):
        self.content_list.append(clean(content))

    def get_content(self):
        return "".join(self.content_list)



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
    def __init__(self, table: pymupdf.table.Table):
        # ====1==== 获取表格的基本信息
        self.table = table
        # 行列基本信息
        self.row_count = self.table.row_count  # 行数
        self.col_count = self.table.col_count  # 列数
        # 表格总体bbox坐标
        self.table_bbox = self.table.bbox
        # 划分表格的信息
        self.rows = self.table.rows

        # ====2==== 初始化表格内容
        self.matrix = get_matrix(self.rows, self.row_count, self.col_count)

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
                    text_perc = area_percent(text_bbox, cellInfo.bbox)
                    if text_perc > max_perc:
                        target_i = i
                        target_j = j
        return target_i,target_j

    def __fill_cell(self, text_bbox, text):  # 根据text_bbox找到在表格的位置，将内容填充
        x_idx, y_idx = self.__find_xy_index(text_bbox)
        self.matrix[x_idx][y_idx].fill_content(text)

    def fill_info(self, blocks):
        for block in blocks:
            type_info = block["type"]
            block_bbox = block['bbox']
            if type_info != 0:  # 非文字block
                continue
            if not is_contain(self.table_bbox, block_bbox, thresold=0): # 不在表格block中的文字舍弃
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

    def get_table(self):
        table = [['' for _ in range(self.col_count)] for _ in range(self.row_count)]
        for i in range(self.row_count):
            for j in range(self.col_count):
                cellInfo = self.matrix[i][j]
                if cellInfo:
                    table[i][j] = cellInfo.get_content()
        return table