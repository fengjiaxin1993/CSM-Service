from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from server.api_server.pdf_extract_routes import pdf_extract_router
from server.utils import MakeFastAPIOffline


def create_app(open_cross_domain: bool, debug:bool):
    app = FastAPI(title="CSM API Server", version="0.0.1", docs_url=None)  # 禁用默认的Swagger UI
    if debug: # 调试页面显示这个页面
        MakeFastAPIOffline(app)

    # Add CORS middleware to allow all origins
    if open_cross_domain:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/", summary="swagger 文档", include_in_schema=False)
    async def document():
        return RedirectResponse(url="/docs")

    app.include_router(pdf_extract_router)

    return app
