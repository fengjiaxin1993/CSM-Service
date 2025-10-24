
# 链路、安全设备
# 'bbox': (170.3300018310547, 452.6177978515625, 253.1414794921875, 465.1419677734375)

text_bbox = (170.3300018310547, 452.6177978515625, 253.1414794921875, 465.1419677734375)

# 2行2列
cell1_box = (164.45250129699707, 307.8499755859375, 253.12945348566228, 579.1900024414062)

# 2行3列
cell2_box = (253.12945348566228, 307.8499755859375, 323.0406786600749, 579.1900024414062)

def area_percent(a_bbox, b_bbox): # 获取 a_bbox与b_bbox的交集面积/a_bbox
    a_x0, a_y0, a_x1, a_y1 = a_bbox
    b_x0, b_y0, b_x1, b_y1 = b_bbox
    # 完全没有交集
    if a_x1 < b_x0 or a_y1 < b_y0 or b_x1 < a_x0 or b_y1 < a_y0:
        return 0
    x0 = max(a_x0, b_x0)
    y0 = max(a_y0, b_y0)
    x1 = min(a_x1, b_x1)
    y1 = min(a_y1, b_y1)
    intersect_area = (x1 - x0) * (y1 - y0)
    a_area = (a_x1 - a_x0) * (a_y1 - a_y0)
    return intersect_area / a_area

a1 = area_percent(text_bbox,cell1_box)
print(a1)
a2 = area_percent(text_bbox,cell2_box)
print(a2)