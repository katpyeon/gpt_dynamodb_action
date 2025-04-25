from fastapi import APIRouter, Body
from typing import Optional, Dict, List
from fastapi.responses import JSONResponse
import json
import logging

from gpt_dynamodb_action.utils.dynamo_helpers import (
    get_table, 
    build_scan_kwargs, 
    execute_scan, 
    prepare_response_data,
    DecimalEncoder
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/scan_table")
def scan_table(
    filters: Optional[Dict[str, str]] = Body(default=None),
    start_key: Optional[dict] = Body(default=None),
    limit: Optional[int] = Body(default=100),
    operator: Optional[Dict[str, str]] = Body(default=None),
    projection: Optional[List[str]] = Body(default=["PK", "SK", "name", "createdAt"])
):
    """
    Scans DynamoDB with pagination. Handles 1MB response limits.
    Filters use AND logic with operators: eq(default), begins_with,
    contains, gt/gte, lt/lte. Gets results across pages.
    Example: {"filters":{"PK":"COM#"},"operator":{"PK":"begins_with"}}
    """
    
    # DynamoDB 테이블 참조 가져오기
    table = get_table()
    
    # 1. 필터 조건 로깅
    logger.info(f"필터 조건: {filters}, 연산자: {operator}, 시작 키: {start_key}, 제한: {limit}, 프로젝션: {projection}")
    
    # 스캔 파라미터 초기화
    scan_kwargs = build_scan_kwargs(filters, operator, projection)
    
    # 결과 수집 초기화
    all_items = []
    total_scanned_count = 0
    last_evaluated_key = None
    max_limit = min(limit or 100, 1000)  # limit이 None이면 100, 1000보다 크면 1000으로 제한
    current_start_key = start_key
    pages_scanned = 0
    
    # limit 개수에 도달하거나 더 이상 페이지가 없을 때까지 스캔 반복
    while len(all_items) < max_limit:
        # 다음 페이지 조회를 위한 스캔 쿼리 실행
        scan_result = execute_scan(table, scan_kwargs, current_start_key)
        
        # 결과 처리
        pages_scanned += 1
        items = scan_result.get("Items", [])
        items_needed = max_limit - len(all_items)
        all_items.extend(items[:items_needed])
        total_scanned_count += scan_result.get("ScannedCount", 0)
        
        # 마지막 평가 키 업데이트
        last_evaluated_key = scan_result.get("LastEvaluatedKey")
        
        # 다음 페이지가 없거나 충분한 항목을 얻었으면 중단
        if not last_evaluated_key or len(all_items) >= max_limit:
            break
            
        # 다음 페이지 조회를 위한 시작 키 업데이트
        current_start_key = last_evaluated_key
    
    # 응답 데이터 준비
    response_data = prepare_response_data(all_items, last_evaluated_key, total_scanned_count)
    
    # 응답 크기 측정
    response_json = json.dumps(response_data, cls=DecimalEncoder)
    response_size_kb = len(response_json.encode('utf-8')) / 1024
    
    # 2. 스캔 결과 로깅
    logger.info(f"결과: 스캔 항목 {total_scanned_count}개, 반환 항목 {len(all_items)}개, 데이터 크기 {response_size_kb:.2f}KB, 페이지 수: {pages_scanned}, 다음 페이지: {last_evaluated_key}")
    
    # 응답 헤더 설정
    headers = {
        "X-Content-Size-KB": f"{response_size_kb:.2f}",
        "X-Items-Count": str(len(all_items)),
        "X-Scanned-Count": str(total_scanned_count),
        "X-Pages-Scanned": str(pages_scanned)
    }
    
    return JSONResponse(content=response_data, headers=headers) 