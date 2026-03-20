# 从指定页码范围内 提取安全问题风险分析表，识别跨页表格
import fitz
import numpy as np
import pymupdf
from server.protection_pdf_extract.table_helper import get_below_bbox
from server.protection_pdf_extract.table_utils import get_upper_bbox, check_all_fill
from server.tools.base import sort_block, contain_key
from rapidocr import RapidOCR
from wired_table_rec.main import WiredTableInput
from wired_table_rec import WiredTableRecognition
from server.tools.ocr_helper import html_to_table
# 表格由于结构化识别，总是出现问题，因此采用ocr的方法，解决表格识别问题
import warnings
import logging
# 1. 屏蔽所有警告（含你那条 FutureWarning）
warnings.filterwarnings("ignore")

# 2. 屏蔽所有日志
logging.basicConfig(level=logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

# 关键库静音
# logging.getLogger("rapidocr").disabled = True
# logging.getLogger("wired_table_rec").disabled = True


# 安全通用要求这一行是多列合并，需要删除
# 安全通用在表头下面
def need_drop(line_list) -> bool:
    for line in line_list:
        if line:
            if contain_key(line, '安全通用要求'):
                return True
    return False


def list_equal(list1, list2):
    if len(list1) != len(list2):
        return False
    for i in range(len(list1)):
        if list1[i] != list2[i]:
            return False
    return True


class OcrTableHelper:
    def __init__(self, pdf_path, start_page, end_page, start_chapter, end_chapter):
        self.dpi = 200  # 分辨率
        self.pdf_path = pdf_path
        self.start_page = start_page
        self.end_page = end_page  # 1.需要确定end_page是否包含表格，2.包含的表格是否和之前表格相同,最后一页可能有2个表格
        self.start_chapter = start_chapter
        self.end_chapter = end_chapter
        self.ocr_engine = RapidOCR(params={"Global.log_level": "critical"})
        self.wired_input = WiredTableInput()
        self.table_engine = WiredTableRecognition(self.wired_input)

        try:
            self.doc = pymupdf.open(self.pdf_path)
            first_table_data = self.__get_first_table()
            self.header_list = first_table_data[0]
            self.column_num = len(self.header_list)
            self.data_list = []
            self.__handle_first_table_data(first_table_data)
            self.__handle_pages()
            self.__handle_last_page()
            self.merge_table = self.__merge_info()
        finally:
            self.doc.close()

    def __to_img_array(self, page_num, bbox=None):
        page = self.__get_page(page_num)
        if bbox is not None:
            # 支持元组或fitz.Rect
            if isinstance(bbox, (tuple, list)):
                clip_rect = fitz.Rect(bbox)
            else:
                clip_rect = bbox

            # 验证bbox是否在页面范围内
            page_rect = page.rect
            if not page_rect.contains(clip_rect):
                # 裁剪到页面范围内
                clip_rect = clip_rect & page_rect

            pix = page.get_pixmap(dpi=self.dpi, clip=clip_rect)
        else:
            pix = page.get_pixmap(dpi=self.dpi)
        # 直接转换为numpy数组，不保存文件
        # pix.samples 是 RGB 格式的字节数据
        img_array = np.frombuffer(pix.samples, dtype=np.uint8)
        img_array = img_array.reshape(pix.height, pix.width, 3)  # RGB三通道
        return img_array

    def __img2table(self, img_array):
        # 1. OCR识别（直接传入numpy数组）
        rapid_ocr_output = self.ocr_engine(img_array, return_word_box=True)
        ocr_result = list(
            zip(rapid_ocr_output.boxes, rapid_ocr_output.txts, rapid_ocr_output.scores)
        )
        # 2. 表格识别（直接传入numpy数组）
        table_results = self.table_engine(img_array, ocr_result=ocr_result)
        html = table_results.pred_html
        # 3. HTML转表格
        table = html_to_table(html)
        return table

    def __get_page(self, page):
        return self.doc.load_page(page - 1)

    def __get_blocks(self, page_num):
        page = self.__get_page(page_num)
        blocks = page.get_text("dict")['blocks']
        return blocks

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

    def __get_page_bbox(self, page):
        page = self.__get_page(page)
        return page.rect

    # 获取第一个表格
    def __get_first_table(self):
        # 1, 获取 安全问题风险分析 下面的bbox
        text_bbox = self.__get_bbox(self.start_page, self.start_chapter)
        page_bbox = self.__get_page_bbox(self.start_page)
        target_bbox = get_below_bbox(page_bbox, text_bbox)

        # 2 识别指定区域表格
        table_img = self.__to_img_array(self.start_page, target_bbox)
        table = self.__img2table(table_img)

        if len(table) == 0:  # 表明首页没有表格
            self.start_page += 1
            table = self.__img2table(self.__to_img_array(self.start_page))
        return table

    # 需要查看是否有安全通用要求
    def __handle_first_table_data(self, first_table_data):
        table = first_table_data[1:]
        for index, line_list in enumerate(table):
            if index == 0 and need_drop(line_list):  # 安全通用要求 删除
                continue
            else:
                self.data_list.append(line_list)

    # 处理最后一页。最后一页 测评上面有表格就提取内容，没表格就忽略
    def __handle_last_page(self):
        # stage1, 获取 等保测评 上面的bbox
        text_bbox = self.__get_bbox(self.end_page, self.end_chapter)
        page_bbox = self.__get_page_bbox(self.end_page)
        target_bbox = get_upper_bbox(page_bbox, text_bbox)
        # stage2 确定是否有表格,如果没有表格,结束
        table_data = self.__img2table(self.__to_img_array(self.end_page, target_bbox))
        if len(table_data) != 0:
            if list_equal(self.header_list, table_data[0]):
                table_data = table_data[1:]
            for line_list in table_data:
                self.data_list.append(line_list)

    def __handle_pages(self):
        for page in range(self.start_page + 1, self.end_page):
            table_data = self.__img2table(self.__to_img_array(page))
            if len(table_data) == 0:
                break
            else:
                if list_equal(self.header_list, table_data[0]):
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
    pdf_path = r"C:\Users\Administrator\Desktop\2018泉州供电公司调度自动化系统信息安全等级测评报告-S2A3G3.pdf"
    start_page = 146
    end_page = 150
    start_content = '安全问题风险评估'
    end_content = '等级测评结论'

    th = OcrTableHelper(pdf_path, start_page, end_page, start_content, end_content)
    print(th.header_list)
    data_list = th.merge_table
    for line in data_list:
        print(line)
