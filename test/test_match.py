# 查看目录后一页，显示的第几页和实际是第几页 pattern = r"第(\d+)页"
import re
text = "第26页/共519页"
pattern = r"第(\d+)页"

match = re.search(pattern, text)
if match:
    page_number = match.group(1)
    print(f"找到了页码: {page_number}")  # 输出: 找到了页码: 123
else:
    print("未找到匹配的页码。")