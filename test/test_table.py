import pymupdf

pdf_path = r"D:\工作\科东\CSM\csm本地安装\表格提取csm服务\等保测评反馈\第二次反馈\02-【已解决】识别成功，主页面不显示识别的问题\中卫第四十七光伏电站电力监控系统_测评报告.pdf"
page = 168

doc = pymupdf.open(pdf_path)
page = doc.load_page(page - 1)

# blocks = page.get_text("dict")['blocks']

# tables = page.find_tables(join_tolerance=20, snap_tolerance=20,strategy="lines")
tables = page.find_tables()
table = tables.tables[0]
text_list = table.extract()
for line in text_list:
    print(line)

