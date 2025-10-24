import pymupdf

pdf_path = r"D:\github\CSM-Service\file\08\银川第四光伏电站电力监控系统测评报告(2024).pdf"
page = 178

doc = pymupdf.open(pdf_path)
page = doc.load_page(page - 1)

# blocks = page.get_text("dict")['blocks']

tables = page.find_tables(join_tolerance=10, snap_tolerance=8,strategy="lines")
table = tables.tables[0]
text_list = table.extract()
for line in text_list:
    print(line)

