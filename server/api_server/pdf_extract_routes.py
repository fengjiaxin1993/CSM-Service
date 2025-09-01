from fastapi import APIRouter
from server.protection_pdf_extract.extract_api import upload_extract_safe_split_table, upload_extract_safe_table
from server.warning_pdf_extract.extract_api import upload_extract_warning_info

pdf_extract_router = APIRouter(prefix="/parse_pdf", tags=["parse pdf file"])

# 上传文件后，提取安全问题风险分析对应的表格, 保留原始表格样式
pdf_extract_router.post(
    "/extract_safe_table",
    summary="上传文件后，提取安全问题风险分析对应的表格",
)(upload_extract_safe_table)

# 上传文件后，提取安全问题风险分析表格后，对关联资产列进行split
pdf_extract_router.post(
    "/extract_safe_split_table",
    summary="上传文件后，提取安全问题风险分析表格后，对关联资产列进行split",
)(upload_extract_safe_split_table)

# 上传文件后，提取预警单信息
pdf_extract_router.post(
    "/extract_warning",
    summary="上传文件后，提取预警单的关键信息",
)(upload_extract_warning_info)
