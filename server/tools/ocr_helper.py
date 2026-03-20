# 表格由于结构化识别，总是出现问题，因此采用ocr的方法，解决表格识别问题
import warnings
import logging
# 1. 屏蔽所有警告（含你那条 FutureWarning）
warnings.filterwarnings("ignore")

# 2. 屏蔽所有日志
logging.basicConfig(level=logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

import fitz  # PyMuPDF
import numpy as np
from rapidocr import RapidOCR
from wired_table_rec.main import WiredTableInput
from wired_table_rec import WiredTableRecognition
from bs4 import BeautifulSoup

# 关闭所有日志
logging.getLogger().setLevel(logging.ERROR)
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).disabled = True
    logging.getLogger(name).setLevel(logging.ERROR)

# 关键库静音
logging.getLogger("rapidocr").disabled = True
logging.getLogger("wired_table_rec").disabled = True

def pdf_page_to_image(pdf_path, page_num, dpi=200):
    """
    使用PyMuPDF将PDF单页转换为图片（纯内存，不保存文件）

    Args:
        pdf_path: PDF文件路径
        page_num: 页码（从1开始）
        dpi: 图片分辨率

    Returns:
        numpy.ndarray: 转换后的图片数组（RGB格式）
    """
    doc = fitz.open(pdf_path)
    if doc.page_count < page_num:
        doc.close()
        raise ValueError(f"PDF总页数为{doc.page_count}，请求页码{page_num}超出范围")

    page = doc.load_page(page_num - 1)  # PyMuPDF页码从0开始
    pix = page.get_pixmap(dpi=dpi)
    doc.close()

    # 直接转换为numpy数组，不保存文件
    # pix.samples 是 RGB 格式的字节数据
    img_array = np.frombuffer(pix.samples, dtype=np.uint8)
    img_array = img_array.reshape(pix.height, pix.width, 3)  # RGB三通道

    return img_array


def html_to_table(html):
    """
    直接从 html 字符串提取表格 → 返回二维列表 [[行1],[行2]]
    稳定、不乱码、不报错
    """
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return []

    # 提取所有行
    rows = []
    for tr in table.find_all('tr'):
        # 提取每一列的文字
        cols = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
        rows.append(cols)
    return rows


def extract_table_from_pdf(pdf_path, page_num, dpi=200):
    """
    从PDF指定页提取表格（全内存处理，无中间文件）

    Args:
        pdf_path: PDF文件路径
        page_num: 页码（从1开始）
        dpi: 图片分辨率

    Returns:
        list: 表格二维列表
    """
    # 1. PDF转图片（内存中）
    img_array = pdf_page_to_image(pdf_path, page_num, dpi)
    # 2. 初始化引擎
    ocr_engine = RapidOCR()
    wired_input = WiredTableInput()
    table_engine = WiredTableRecognition(wired_input)

    # 3. OCR识别（直接传入numpy数组）
    rapid_ocr_output = ocr_engine(img_array, return_word_box=True)
    ocr_result = list(
        zip(rapid_ocr_output.boxes, rapid_ocr_output.txts, rapid_ocr_output.scores)
    )

    # 4. 表格识别（直接传入numpy数组）
    table_results = table_engine(img_array, ocr_result=ocr_result)
    html = table_results.pred_html

    # 5. HTML转表格
    table = html_to_table(html)

    return table


if __name__ == "__main__":
    # 示例：提取单页表格
    page_num = 147
    PDF_PATH = r"C:\Users\Administrator\Desktop\2018泉州供电公司调度自动化系统信息安全等级测评报告-S2A3G3.pdf"
    table = extract_table_from_pdf(PDF_PATH, page_num, dpi=200)
    for line in table:
        print(line)

