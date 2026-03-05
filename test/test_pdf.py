from server.protection_pdf_extract.extract_api import extract_safe_table, extract_safe_split_table, output_standard


def unmark_test():
    # ok
    pdf_path1 = r"D:\code\CSM-Service\files\unmark\5-1网络安全等级保护测评报告-实时监控.pdf"

    # ok
    pdf_path2 = r"D:\code\CSM-Service\files\unmark\5-1网络安全等级保护测评报告调度管理.pdf"

    # ok
    pdf_path3 = r"D:\code\CSM-Service\files\unmark\7-1 DB-2308-0028_天津市滨海新区金开新能源科技有限公司金开新能锦湖轮胎18MW分布式光伏电站监控_测评报告.pdf"

    # ok
    pdf_path4 = r"D:\code\CSM-Service\files\unmark\7-1 DB-2401-0023_天津悦通达新能源科技有限公司110KV悦通达风电场电力监控系统_测评报告.pdf"

    # ok
    pdf_path5 = r"D:\code\CSM-Service\files\unmark\DB-2003-0034_国网天津市电力公司滨海供电分公司调度自动化系统_测评报告.pdf"

    # ok
    pdf_path6 = r"D:\code\CSM-Service\files\unmark\刘岗庄网络安全等级保护测评报告-.pdf"

    # ok
    pdf_path7 = r"D:\code\CSM-Service\files\unmark\吴忠第五十光伏电站电力监控系统等级保护测评.pdf"

    # ok
    pdf_path8 = r"D:\code\CSM-Service\files\unmark\国网银川供电公司银川智能电网调度控制系统等级测评报告-2024-Z.pdf"

    # ok
    pdf_path9 = r"D:\code\CSM-Service\files\unmark\国能宁东新能源有限公司330千伏曙光变电力监控系统（S2A3）网络安全等级保护测评报告.pdf"

    # ok
    pdf_path10 = r"D:\code\CSM-Service\files\unmark\青龙山第二储能电站电力监控系统等级测评报告.pdf"

    table_list = extract_safe_split_table(pdf_path10)
    res = output_standard(table_list)
    print(res)


def mark_test():
    # ok
    pdf_path1 = r"D:\code\CSM-Service\files\mark\DB-2405-0051_国网天津市电力公司国网天津市电力公司智能电网调度技术支持系统实时监控与预警系统主备一体系统_测评报告.pdf"

    # ok
    pdf_path2 = r"D:\code\CSM-Service\
    files\mark\DB-2405-0051_国网天津市电力公司国网天津市电力公司智能电网调度技术支持系统调度计划与安全校核系统_测评报告.pdf"

    # ok
    pdf_path3 = r"D:\code\CSM-Service\files\mark\盖章版_等保_宁夏超高压-新一代集控站设备监控系统-终.pdf"

    # ok
    pdf_path4 = r"D:\code\CSM-Service\files\mark\等级测评报告-宁夏翔腾电源科技有限公司-江汉第二储能电站电力监控系统.pdf"

    table_list = extract_safe_split_table(pdf_path2)
    res = output_standard(table_list)
    print(res)


# 解决问题1
def new_test1():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\01\SA-MI07-HT24031-CP24705_张易第一风电场电力监控系统_测评报告.pdf"

    # ok
    pdf_path2 = r"D:\github\CSM-Service\file\01\中卫第六十一光伏电站电力监控系统_测评报告 .pdf"

    # ok
    pdf_path3 = r"D:\github\CSM-Service\file\01\中宁县欣文新能源有限公司-中卫第六十四光伏电站电力监控系统等级测评报告.pdf"

    # ok
    pdf_path4 = r"D:\github\CSM-Service\file\01\中宁第六十光伏电站测评报告终版2024.pdf"

    # ok
    pdf_path5 = r"D:\github\CSM-Service\file\01\吴忠市瑞储科技有限公司-泉眼第三储能电站电力监控系统-等级测评报告.pdf"

    table_list = extract_safe_split_table(pdf_path5)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题2
def new_test2():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\02\中卫第四十七光伏电站电力监控系统_测评报告.pdf"

    table_list = extract_safe_split_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题3
def new_test3():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\03\向阳第一储能电站电力监控系统测评报告(盖章版) .pdf"

    # ok
    pdf_path2 = r"D:\github\CSM-Service\file\03\吴忠第五十光伏电站电力监控系统等级保护测评 (1).pdf"

    # ok
    pdf_path3 = r"D:\github\CSM-Service\file\03\星能第四风电场电力监控系统测评报告.pdf"

    # ok
    pdf_path4 = r"D:\github\CSM-Service\file\03\杨家窑第三风电场监控系统等保测评报告.pdf"

    # ok
    pdf_path5 = r"D:\github\CSM-Service\file\03\杨家窑第二风光电场电力监控系统等保测评报告.pdf"

    # ok
    pdf_path6 = r"D:\github\CSM-Service\file\03\电力监控系统测评报告-嘉泽第一风电场.pdf"

    # ok
    pdf_path7 = r"D:\github\CSM-Service\file\03\T2024072303250001_国家电投集团宁夏能源铝业中卫新能源有限公司_国电投框架-宁夏-铝电公司中卫新能源香山第六风电场及沙梁110kV变电站监控系统第三级信息系统等级保护测评报告-出口复核-二次邮寄-1-V69298 (1).pdf"

    table_list = extract_safe_split_table(pdf_path7)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题4
def new_test4():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\04\XMBH2025050924+6001523 绿塬第一储能电站电力控制系统v1.0(3) (1).pdf"

    table_list = extract_safe_split_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题6
def new_test6():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\06\中铝宁夏能源集团马莲台发电分公司NCS变电站（S3A2）网络控制系统网络安全等级保护测评报告 - 盖章.pdf"

    table_list = extract_safe_split_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题8
def new_test8():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\08\银川第四光伏电站电力监控系统测评报告(2024).pdf"

    table_list = extract_safe_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决问题9
def new_test9():
    # ok
    pdf_path1 = r"D:\github\CSM-Service\file\09\银阳电站电力监控子系统_测评报告（中卫第四十光伏电站）.pdf"

    table_list = extract_safe_table(pdf_path1)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


# 解决一部分无法识别问题 2026-03-05
def new_test10():
    # ok # 解决是目录显示， 第一页对应不上的问题
    pdf_path1 = r"C:\Users\Administrator\Desktop\新建文件夹\DB-2003-0034_国网天津市电力公司滨海供电分公司调度自动化系统_测评报告.pdf"
    # ok # 表格识别空列问题也解决了
    pdf_path2 = r"C:\Users\Administrator\Desktop\新建文件夹\国网银川供电公司银川智能电网调度控制系统等级测评报告-2024-Z.pdf"
    # ok 提取表格的设置参数
    pdf_path3 = r"C:\Users\Administrator\Desktop\新建文件夹\吴忠第五十光伏电站电力监控系统等级保护测评.pdf"
    #
    pdf_path4 = r"D:\工作\科东\智能安全研发分部\CSM\csm本地安装\表格提取csm服务\等保测评所有文件\中卫第四十七光伏电站电力监控系统_测评报告.pdf"
    table_list = extract_safe_table(pdf_path4)
    print(table_list[0])
    for line in table_list[1:]:
        print(line)


if __name__ == '__main__':
    new_test10()
