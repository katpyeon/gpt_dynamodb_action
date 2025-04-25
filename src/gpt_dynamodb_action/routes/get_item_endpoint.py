from fastapi import APIRouter, Body, HTTPException
from typing import Optional, List
from fastapi.responses import JSONResponse
import json
import logging

from gpt_dynamodb_action.utils.dynamo_helpers import (
    get_table,
    prepare_response_data,
    DecimalEncoder,
    build_projection_expression
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/get_item")
def get_item(
    pk: str = Body(..., description="파티션 키 값(PK에 할당될 값)"),
    sk: str = Body(..., description="정렬 키 값(SK에 할당될 값)"),
    projection: Optional[List[str]] = Body(default=None, description="반환할 속성 목록 (기본값: 모든 필드)")
):
    """
    DynamoDB GetItem operation. Retrieves a single item where PK and SK exactly match.
    Both fields support only 'eq' operation.
    Example: {"pk":"USR#john@example.com","sk":"USR#john@example.com"}
    """
    
    # DynamoDB 테이블 참조 가져오기
    table = get_table()
    
    # 로깅
    logger.info(f"GetItem 파라미터: PK={pk}, SK={sk}, 프로젝션={projection}")
    
    # 프로젝션 표현식 및 표현식 속성 이름 구성
    projection_expression = None
    expression_attribute_names = None
    if projection:
        projection_expression, expression_attribute_names = build_projection_expression(projection)
    
    # GetItem 요청 수행
    try:
        # Key는 파티션 키와 정렬 키로 구성된 딕셔너리여야 함
        get_item_kwargs = {
            "Key": {
                "PK": pk,
                "SK": sk
            }
        }
        
        # 프로젝션 표현식과 속성 이름이 있는 경우 추가
        if projection_expression and expression_attribute_names:
            get_item_kwargs["ProjectionExpression"] = projection_expression
            get_item_kwargs["ExpressionAttributeNames"] = expression_attribute_names
        
        response = table.get_item(**get_item_kwargs)
        
        # 'Item' 키가 있는지 확인 (항목이 존재하는 경우)
        item = response.get('Item')
        if not item:
            # 항목이 존재하지 않는 경우
            return JSONResponse(
                status_code=404,
                content={"detail": f"Item with PK='{pk}' and SK='{sk}' not found"}
            )
        
        # 항목 처리 (Decimal 타입 변환)
        # prepare_response_data 함수에서 마지막 매개변수는 scanned count이지만
        # get_item은's scanned count가 없으므로 1로 설정
        response_data = prepare_response_data([item], None, 1)
        response_data = {
            "item": response_data["items"][0],
            "count": 1
        }
        
        # 응답 크기 측정
        response_json = json.dumps(response_data, cls=DecimalEncoder)
        response_size_kb = len(response_json.encode('utf-8')) / 1024
        
        # GetItem 결과 로깅
        logger.info(f"GetItem 결과: 항목 발견됨, 데이터 크기 {response_size_kb:.2f}KB")
        
        # 응답 헤더 설정
        headers = {
            "X-Content-Size-KB": f"{response_size_kb:.2f}"
        }
        
        return JSONResponse(content=response_data, headers=headers)
    
    except Exception as e:
        # 예외 발생 시 로깅 및 에러 응답
        logger.error(f"GetItem 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GetItem operation failed: {str(e)}") 