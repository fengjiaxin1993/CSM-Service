import fitz  # PyMuPDF
import numpy as np
from rapidocr import RapidOCR
from wired_table_rec.main import WiredTableInput
from wired_table_rec import WiredTableRecognition
from bs4 import BeautifulSoup

# 配置
PDF_PATH = r"C:\Users\Administrator\Desktop\2018泉州供电公司调度自动化系统信息安全等级测评报告-S2A3G3.pdf"


def pdf_page_to_image(pdf_path, page_num, dpi=200, bbox=None):
    """
    使用PyMuPDF将PDF单页转换为图片（纯内存，不保存文件）
    
    Args:
        pdf_path: PDF文件路径
        page_num: 页码（从1开始）
        dpi: 图片分辨率
        bbox: 可选，截取区域，格式为 (x0, y0, x1, y1) 或 fitz.Rect
              坐标为PDF坐标系（左下角为原点，单位为点）
    
    Returns:
        numpy.ndarray: 转换后的图片数组（RGB格式）
    """
    doc = fitz.open(pdf_path)
    if doc.page_count < page_num:
        doc.close()
        raise ValueError(f"PDF总页数为{doc.page_count}，请求页码{page_num}超出范围")

    page = doc.load_page(page_num - 1)  # PyMuPDF页码从0开始

    # 如果指定了bbox，则只截取该区域
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
            print(f"  ⚠ bbox已裁剪到页面范围内: {clip_rect}")

        pix = page.get_pixmap(dpi=dpi, clip=clip_rect)
    else:
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
    print(f"正在处理第 {page_num} 页...")
    img_array = pdf_page_to_image(pdf_path, page_num, dpi)
    print(f"  ✓ 图片转换成功，尺寸: {img_array.shape}")

    # 2. 初始化引擎
    ocr_engine = RapidOCR()
    wired_input = WiredTableInput()
    table_engine = WiredTableRecognition(wired_input)

    # 3. OCR识别（直接传入numpy数组）
    rapid_ocr_output = ocr_engine(img_array, return_word_box=True)
    ocr_result = list(
        zip(rapid_ocr_output.boxes, rapid_ocr_output.txts, rapid_ocr_output.scores)
    )
    print(f"  ✓ OCR识别完成，文本区域: {len(ocr_result)}")

    # 4. 表格识别（直接传入numpy数组）
    table_results = table_engine(img_array, ocr_result=ocr_result)
    html = table_results.pred_html
    print(f"  ✓ 表格识别完成")

    # 5. HTML转表格
    table = html_to_table(html)
    print(f"  ✓ 表格提取完成，行数: {len(table)}")

    return table


def extract_table_from_pdf_with_bbox(pdf_path, page_num, bbox, dpi=200):
    """从PDF指定页的特定区域提取表格"""
    print(f"正在处理第 {page_num} 页，区域: {bbox}...")
    img_array = pdf_page_to_image(pdf_path, page_num, dpi, bbox)
    print(f"  ✓ 图片转换成功，尺寸: {img_array.shape}")

    # 初始化引擎
    ocr_engine = RapidOCR()
    wired_input = WiredTableInput()
    table_engine = WiredTableRecognition(wired_input)

    # OCR识别
    rapid_ocr_output = ocr_engine(img_array, return_word_box=True)
    ocr_result = list(
        zip(rapid_ocr_output.boxes, rapid_ocr_output.txts, rapid_ocr_output.scores)
    )
    print(f"  ✓ OCR识别完成，文本区域: {len(ocr_result)}")

    # 表格识别
    table_results = table_engine(img_array, ocr_result=ocr_result)
    html = table_results.pred_html

    # HTML转表格
    table = html_to_table(html)
    print(f"  ✓ 表格提取完成，行数: {len(table)}")

    return table


if __name__ == "__main__":
    # 示例1：提取整页表格
    page_num = 102
    # PDF_PATH = r"C:\Users\Administrator\Desktop\2018泉州供电公司调度自动化系统信息安全等级测评报告-S2A3G3.pdf"
    PDF_PATH = r"D:\工作\科东\智能安全研发分部\CSM\csm本地安装\表格提取csm服务\等保测评反馈\第二次反馈\00-识别成功的报告\等级测评报告-中宁县佳洋新能源有限公司-吴忠第五十九光伏电站电力监控系统-扫描.pdf"
    table = extract_table_from_pdf(PDF_PATH, page_num, dpi=200)
    for line in table:
        print(line)
"""
['序号', '安全类', '安全问题', '关联资产', '关联威胁', '危害分析结果', '风险等级']
['', '', '二次室未设置自动检测火情、自动报警、自动灭火的自动消防系统。', '二次室', '物理环境影响', '导致火灾发生时火势不能第一时间被控制并扑灭，可能对机房重要设备造成严重损害。', '低']
['2', '安全物理环境', '机房内未采取措施防止水蒸气结露，重要区域未设置防水围堰或排水沟，无法防止地下积水的转移与渗透。', '二次室', '物理环境影响', '存在水蒸气结露风险，可能导致设备损坏,影响系统正常运行。', '低']
['3', '', '机房未安装漏水检测及漏水报警装置，无法在机房发生渗水或漏水情况下及时检测并报警。', '二次室', '物理环境影响', '如果机房出现漏水事故，不能第一时间报警并通知运维人员解决，可能导致水患影响重要设备运行。', '低']
['4', '', '机房内未部署专用精密空调，使用家用空调进行温度控制，无法自动', '二次室', '物理环境影响', '导致机房不能做到湿度恒定，不利于电子设备的稳定运行，进而增加', '低']
"""