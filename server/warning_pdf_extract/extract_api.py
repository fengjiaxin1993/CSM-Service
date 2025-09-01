import os
from fastapi import UploadFile, File

from config.basic_config import BASE_TEMP_DIR
from server.tools.base import shorten_filename
from server.warning_pdf_extract.warningHelper import WarningHelper
import logging

logger = logging.getLogger(__name__)

empty_dic = {
    "name": "",
    "code": "",
    "level": 0,
    "desc": "",
    "influence": "",
    "check": "",
    "repair": "",
    "requirement": ""
}


def check_dict(dic: dict) -> bool:
    for k, v in dic.items():
        if v == '' or v == 0:
            return False
    return True


# 上传文件并提取预警信息
def upload_extract_warning_info(
        file: UploadFile = File(..., description="上传文件")
) -> dict:
    """
    将文件保存到文件目录.
    """
    try:
        file_content = file.file.read()  # 读取上传文件的内容
        short_filename = shorten_filename(file.filename)
        new_file_path = os.path.join(BASE_TEMP_DIR, short_filename)
        logger.info(f"{file.filename} 文件保存成功!")
        with open(new_file_path, "wb") as f:
            f.write(file_content)
        wh = WarningHelper(new_file_path)
        res_dic = wh.extract_info()
        return res_dic
    except Exception as e:
        msg = f"{file.filename} 预警文件解析失败，报错信息为: {e}"
        logger.info(msg)
        return empty_dic
