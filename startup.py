import yaml
import uvicorn
from server.api_server.server_app import create_app


def run_api_server(host: str, port: int, open_cross_domain: bool, debug:bool):
    app = create_app(open_cross_domain, debug)
    uvicorn.run(app, host=host, port=port)


def read_config():
    with open('settings.yaml', 'r') as f:
        data = yaml.safe_load(f)  # 使用safe_load以避免潜在的安全风险，例如执行恶意代码的风险。
        return data


if __name__ == "__main__":
    config_dict = read_config()
    server_dict = config_dict['server']
    host = server_dict['host']
    port = server_dict['port']
    open_cross_domain = config_dict['open_cross_domain']
    debug = config_dict['debug']

    run_api_server(host, port, open_cross_domain, debug)
