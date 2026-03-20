import pymupdf

# pdf_path = r"D:\工作\科东\智能安全研发分部\CSM\csm本地安装\表格提取csm服务\等保测评所有文件\青龙山第二储能电站电力监控系统等级测评报告.pdf"
# page_num = 18


pdf_path = r"C:\Users\Administrator\Desktop\2018泉州供电公司调度自动化系统信息安全等级测评报告-S2A3G3.pdf"
start_page = 14

with pymupdf.open(pdf_path) as doc:
    page = doc.load_page(start_page-1)
    text = page.get_text("text")
    text = text.replace(" ", "").replace("\t", "")
    print(text)
    # blocks = page.get_text("dict")['blocks']
    # print(blocks)
    x=5




"""
{'number': 2, 
'type': 0, 
'bbox': (273.5299987792969, 79.1596450805664, 324.50201416015625, 96.82736206054688), 
'lines': [
    {'spans': [
                {'size': 15.960000038146973, 'flags': 4, 'bidi': 0, 'char_flags': 16, 'font': 'SimHei', 'color': 0, 'alpha': 255, 'ascender': 0.859000027179718, 'descender': -0.14100000262260437, 'text': '目', 'origin': (273.5299987792969, 93.3800048828125), 'bbox': (273.5299987792969, 79.67036437988281, 289.489990234375, 95.63036346435547)},
                {'size': 15.960000038146973, 'flags': 20, 'bidi': 0, 'char_flags': 24, 'font': 'TimesNewRomanPS-BoldMT', 'color': 0, 'alpha': 255, 'ascender': 0.890999972820282, 'descender': -0.2160000056028366, 'text': '  ', 'origin': (289.7300109863281, 93.3800048828125), 'bbox': (289.7300109863281, 79.1596450805664, 301.760009765625, 96.82736206054688)}, 
                {'size': 15.960000038146973, 'flags': 4, 'bidi': 0, 'char_flags': 16, 'font': 'SimHei', 'color': 0, 'alpha': 255, 'ascender': 0.859000027179718, 'descender': -0.14100000262260437, 'text': '录', 'origin': (305.69000244140625, 93.3800048828125), 'bbox': (305.69000244140625, 79.67036437988281, 321.6499938964844, 95.63036346435547)},
                 {'size': 12.0, 'flags': 16, 'bidi': 0, 'char_flags': 24, 'font': 'Calibri-Bold', 'color': 0, 'alpha': 255, 'ascender': 0.75, 'descender': -0.25, 'text': ' ', 'origin': (321.7900085449219, 93.3800048828125), 'bbox': (321.7900085449219, 84.3800048828125, 324.50201416015625, 96.3800048828125)}
                ], 
    'wmode': 0, 
    'dir': (1.0, 0.0), 
    'bbox': (273.5299987792969, 79.1596450805664, 324.50201416015625, 96.82736206054688)
    }]}
"""