import yaml
import uvicorn
from server.api_server.server_app import create_app
from config.basic_config import BASE_DIR, app_config
import os


def run_api_server(host: str, port: int, open_cross_domain: bool, debug: bool):
    app = create_app(open_cross_domain, debug)
    uvicorn.run(app, host=host, port=port)


def read_config():
    config_path = 'settings.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        return data


if __name__ == "__main__":
    config_dict = read_config()

    # 将配置注入到全局对象，所有子模块通过 app_config 读取（兼容二进制打包）
    app_config.load(config_dict)

    server_dict = config_dict['server']
    host = server_dict['host']
    port = server_dict['port']
    open_cross_domain = config_dict['open_cross_domain']
    debug = config_dict['debug']

    run_api_server(host, port, open_cross_domain, debug)
