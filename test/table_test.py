from pymupdf import pymupdf, Page


# ===================== 【复制上面的清洗函数】 =====================
def clean_table_data(table):
    if not table:
        return []
    cleaned_cells = []
    for row in table:
        new_row = []
        for cell in row:
            if cell is None:
                new_row.append("")
            else:
                new_cell = str(cell).strip().replace("\n", "").replace("\t", "")
                new_row.append(new_cell)
        cleaned_cells.append(new_row)
    transposed = list(zip(*cleaned_cells))
    non_empty_cols = [col for col in transposed if any(cell.strip() for cell in col)]
    if not non_empty_cols:
        return []
    cleaned_table = list(zip(*non_empty_cols))
    cleaned_table = [row for row in cleaned_table if any(cell.strip() for cell in row)]
    return cleaned_table


def clean_fitz_table(table):
    """
    专门修复 fitz.find_tables() 提取的表格：
    1. 合并单元格内换行（被拆成两行的自动合并）
    2. 删除全空列、全空行
    3. 清理空格、换行
    4. 消除多余列
    """
    if not table:
        return []

    # 1. 清理每个单元格：去除换行、空格
    cleaned = []
    for row in table:
        new_row = []
        for cell in row:
            if cell is None:
                new_row.append("")
            else:
                # 关键：把单元格内的换行 → 空格
                s = str(cell).strip().replace("\n", " ").replace("  ", " ")
                new_row.append(s)
        cleaned.append(new_row)

    # 2. 【核心】合并被换行拆分成两行的内容（最关键）
    merged = []
    i = 0
    max_col = max(len(r) for r in cleaned) if cleaned else 0

    while i < len(cleaned):
        current = cleaned[i]
        # 如果当前行 非空，但有效内容很少 → 大概率是上一行的换行
        if i > 0 and sum(1 for c in current if c) <= 2:
            prev = merged[-1]
            # 把当前行拼接回上一行
            for col in range(min(len(prev), len(current))):
                if current[col].strip():
                    prev[col] += " " + current[col]
            i += 1
        else:
            merged.append(current)
            i += 1

    # 3. 删除全空行
    merged = [r for r in merged if any(c.strip() for c in r)]

    # 4. 转置 → 删除【全空列】→ 转置回来（解决列数变多）
    if not merged:
        return []

    transposed = list(zip(*merged))
    # 只保留至少有一个非空值的列
    transposed = [col for col in transposed if any(c.strip() for c in col)]
    final = list(zip(*transposed)) if transposed else []

    # 5. 转成列表格式（方便转DataFrame）
    return [list(row) for row in final]


# ===================== 主提取逻辑 =====================

pdf_path1 = r"C:\Users\Administrator\Desktop\2018泉州供电公司调度自动化系统信息安全等级测评报告-S2A3G3.pdf"
start_page1 = 146
end_page1 = 150

pdf_path2 = r"C:\Users\Administrator\Desktop\2018泉州供电公司调度自动化系统信息安全等级测评报告-S2A3G3.pdf"
start_page2 = 146
end_page2 = 150

pdf_path3 = r"D:\工作\科东\智能安全研发分部\CSM\csm本地安装\表格提取csm服务\等保测评所有文件\中卫第四十七光伏电站电力监控系统_测评报告.pdf"
start_page3 = 168
end_page3 = 186


def header_valid(header_list):
    for line in header_list:
        if line is None or line == '':
            return False
    return True



def find_valid_snap(page):
    snap_list = [3, 4, 5, 6, 7]
    for snap in snap_list:
        tables = page.find_tables(snap_tolerance=snap)
        table = tables.tables[0]
        table_data = table.extract()
        header_list = table_data[0]
        if header_valid(header_list):
            return snap
    return snap_list[0]

    return 0


with pymupdf.open(pdf_path1) as doc:
    for idx in range(start_page1 - 1, end_page1):
        page = doc.load_page(idx)
        snap = find_valid_snap(page)
        tables = page.find_tables()
        table = tables.tables[0]
        table_data = table.extract()
        # pure_table = clean_fitz_table(table_data)
        print(table_data)
