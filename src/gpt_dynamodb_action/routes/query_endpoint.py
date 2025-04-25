from fastapi import APIRouter, Body
from typing import Optional, Dict, List
from fastapi.responses import JSONResponse
import json
import logging
from boto3.dynamodb.conditions import Key

from gpt_dynamodb_action.utils.dynamo_helpers import (
    get_table,
    build_projection_expression,
    create_filter_expression,
    convert_to_number,
    prepare_response_data,
    DecimalEncoder
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/query_table")
def query_table(
    pk: str = Body(..., description="파티션 키 값(PK에 할당될 값)"),
    sk: Optional[str] = Body(default=None, description="정렬 키 값(SK에 할당될 값)"),
    sk_operator: Optional[str] = Body(default="eq", description="SK 연산자 - 'eq' 또는 'begins_with'"),
    filters: Optional[Dict[str, str]] = Body(default=None, description="추가 필터 조건 (키:값 쌍)"),
    operator: Optional[Dict[str, str]] = Body(default=None, description="필터 연산자 (키:연산자 쌍)"),
    start_key: Optional[dict] = Body(default=None, description="페이지네이션 시작 키"),
    limit: Optional[int] = Body(default=100, description="최대 반환 항목 수 (최대 100)"),
    projection: Optional[List[str]] = Body(default=["PK", "SK", "name", "createdAt"], description="반환할 속성 목록")
):
    """
    DynamoDB Query with pagination. PK supports 'eq', SK supports 'eq'/'begins_with'.
    Filters accept various operators. Returns max 100 items with pagination.
    Example: {"pk":"COM#","sk":"COM#ABC","sk_operator":"begins_with"}
    """
    
    # DynamoDB 테이블 참조 가져오기
    table = get_table()
    
    # 로깅
    logger.info(f"쿼리 파라미터: PK={pk}, SK={sk}, SK 연산자={sk_operator}, 필터={filters}, 필터 연산자={operator}, 시작 키={start_key}, 제한={limit}")
    
    # 기본 키 조건 생성 (PK는 항상 eq 연산만 지원)
    key_condition = Key("PK").eq(pk)
    
    # SK 조건 추가 (지정된 경우)
    if sk:
        if sk_operator == "begins_with":
            key_condition = key_condition & Key("SK").begins_with(sk)
        else:  # 기본값은 eq
            key_condition = key_condition & Key("SK").eq(sk)
    
    # 쿼리 파라미터 구성
    query_kwargs = {
        "KeyConditionExpression": key_condition,
        "Limit": min(limit, 100)  # 최대 100개로 제한
    }
    
    # 필터 표현식 추가 (있는 경우)
    if filters:
        filter_condition = None
        for k, v in filters.items():
            # 연산자 확인 (기본값은 'eq')
            op = operator.get(k, 'eq') if operator else 'eq'
            
            # 숫자 비교 연산자인 경우 값 변환
            if op in ['gt', 'gte', 'lt', 'lte']:
                v = convert_to_number(v)
                
            # 연산자에 따른 표현식 생성
            expr = create_filter_expression(k, op, v)
            filter_condition = expr if filter_condition is None else filter_condition & expr
            
        query_kwargs["FilterExpression"] = filter_condition
    
    # 프로젝션 표현식 추가
    if projection:
        projection_expression, expression_attribute_names = build_projection_expression(projection)
        
        if projection_expression and expression_attribute_names:
            query_kwargs["ProjectionExpression"] = projection_expression
            query_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    # 페이지네이션을 위한 시작 키 설정
    if start_key:
        query_kwargs["ExclusiveStartKey"] = start_key
    
    # 결과 수집 초기화
    all_items = []
    last_evaluated_key = None
    pages_scanned = 0
    max_limit = min(limit or 100, 100)  # 최대 100개로 제한
    
    # 쿼리 실행
    while len(all_items) < max_limit:
        # 쿼리 실행
        query_result = table.query(**query_kwargs)
        
        # 결과 처리
        pages_scanned += 1
        items = query_result.get("Items", [])
        items_needed = max_limit - len(all_items)
        all_items.extend(items[:items_needed])
        
        # 마지막 평가 키 업데이트
        last_evaluated_key = query_result.get("LastEvaluatedKey")
        
        # 다음 페이지가 없거나 충분한 항목을 얻었으면 중단
        if not last_evaluated_key or len(all_items) >= max_limit:
            break
            
        # 다음 페이지 조회를 위한 시작 키 업데이트
        query_kwargs["ExclusiveStartKey"] = last_evaluated_key
    
    # 응답 데이터 준비
    response_data = prepare_response_data(all_items, last_evaluated_key, len(all_items))
    
    # 응답 크기 측정
    response_json = json.dumps(response_data, cls=DecimalEncoder)
    response_size_kb = len(response_json.encode('utf-8')) / 1024
    
    # 쿼리 결과 로깅
    logger.info(f"쿼리 결과: 반환 항목 {len(all_items)}개, 데이터 크기 {response_size_kb:.2f}KB, 페이지 수: {pages_scanned}, 다음 페이지: {last_evaluated_key}")
    
    # 응답 헤더 설정
    headers = {
        "X-Content-Size-KB": f"{response_size_kb:.2f}",
        "X-Items-Count": str(len(all_items)),
        "X-Pages-Scanned": str(pages_scanned)
    }
    
    return JSONResponse(content=response_data, headers=headers) 