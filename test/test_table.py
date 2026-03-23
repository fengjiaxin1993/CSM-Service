import pymupdf

pdf_path = r"C:\Users\Administrator\Desktop\2018泉州供电公司调度自动化系统信息安全等级测评报告-S2A3G3.pdf"
page = 5

doc = pymupdf.open(pdf_path)
page = doc.load_page(page - 1)

tables = page.find_tables()
table = tables.tables[0]
text_list = table.extract()
print(text_list)
for line in text_list:
    print(line)

