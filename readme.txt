## 1.python项目环境配置

### 1.1 环境安装
conda create -n csm-service python=3.11
conda activate csm-service
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
or
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

### 1.2.启动代码
cd CSM-Service
python startup.py
访问 ip:port 端口即可, 可在settings.yaml中设置

## 2.打包程序和依赖，实现迁移部署

### 2.1 打包程序
pip install cx_Freeze -i https://pypi.tuna.tsinghua.edu.cn/simple/
在项目目录中 执行如下命令
python setup.py build
执行该命令后会在当前目录下生成一个build文件夹
将settings.yaml移动build/exe.linux-x86_64-3.11文件夹中

# 4.二进制程序启动
./csmServer
访问 ip:port 端口即可, 可在settings.yaml中设置