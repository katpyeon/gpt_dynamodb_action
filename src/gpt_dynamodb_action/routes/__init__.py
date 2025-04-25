from fastapi import APIRouter
from gpt_dynamodb_action.routes import scan_endpoint, query_endpoint, schema_endpoints, get_item_endpoint

router = APIRouter()

# 각 모듈의 라우터 통합
router.include_router(scan_endpoint.router)
router.include_router(query_endpoint.router)
router.include_router(schema_endpoints.router)
router.include_router(get_item_endpoint.router)
