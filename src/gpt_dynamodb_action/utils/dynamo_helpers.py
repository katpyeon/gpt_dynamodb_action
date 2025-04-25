import boto3
import logging
import os
import json
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Decimal 타입 처리를 위한 JSONEncoder 클래스
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def get_table():
    """DynamoDB 테이블 연결을 반환합니다."""
    session = boto3.Session(
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_REGION", "ap-northeast-2")
    )
    dynamodb = session.resource("dynamodb")
    return dynamodb.Table(os.environ["DYNAMO_TABLE_NAME"])

def convert_to_number(value):
    """문자열 값을 가능한 경우 숫자로 변환합니다."""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value

def create_filter_expression(key, operator, value):
    """지정된 키, 연산자, 값에 대한 DynamoDB 필터 표현식을 생성합니다."""
    attr = Attr(key)
    
    if operator == 'begins_with':
        return attr.begins_with(value)
    elif operator == 'contains':
        return attr.contains(value)
    elif operator == 'gt':
        return attr.gt(value)
    elif operator == 'gte':
        return attr.gte(value)
    elif operator == 'lt':
        return attr.lt(value)
    elif operator == 'lte':
        return attr.lte(value)
    else:  # 기본값은 equals
        return attr.eq(value)

def build_projection_expression(projection: List[str]) -> tuple:
    """프로젝션 표현식과 속성 이름을 구성합니다."""
    if not projection:
        return None, None
        
    # '#' 접두사가 있는 표현식 이름과 이름 값을 맵핑할 딕셔너리
    expression_attribute_names = {}
    
    # '#name' 형태의 프로젝션 필드 이름 목록
    projection_expression_names = []
    
    # 투영할 속성 목록을 생성
    for i, attr in enumerate(projection):
        # 예약어 및 특수 문자 처리를 위해 '#' 접두사를 사용한 표현식 이름 생성
        expr_name = f"#proj{i}"
        expression_attribute_names[expr_name] = attr
        projection_expression_names.append(expr_name)
    
    # 프로젝션 표현식 설정
    projection_expression = ", ".join(projection_expression_names)
    
    return projection_expression, expression_attribute_names

def execute_scan(table, scan_kwargs, current_start_key):
    """DynamoDB 테이블에 대한 스캔을 실행합니다."""
    # 시작 키 설정
    if current_start_key:
        scan_kwargs["ExclusiveStartKey"] = current_start_key
    elif "ExclusiveStartKey" in scan_kwargs:
        del scan_kwargs["ExclusiveStartKey"]
        
    return table.scan(**scan_kwargs)

def prepare_response_data(items, last_evaluated_key, total_scanned_count):
    """응답 데이터를 준비하고 Decimal을 float로 변환합니다."""
    # Decimal 값을 float로 변환하는 함수
    def convert_decimal(obj):
        if isinstance(obj, dict):
            return {k: convert_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimal(i) for i in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj
    
    # 데이터 변환
    converted_items = convert_decimal(items)
    converted_last_key = convert_decimal(last_evaluated_key)
    
    # 응답 데이터 구성
    return {
        "items": converted_items,
        "lastEvaluatedKey": converted_last_key,
        "count": len(items),
        "scannedCount": total_scanned_count
    }

def build_scan_kwargs(filters, operator, projection=None):
    """필터와 연산자를 기반으로 DynamoDB 스캔 파라미터를 구성합니다."""
    scan_kwargs = {}
    
    # 필터 표현식 추가
    if filters:
        condition = None
        for k, v in filters.items():
            # 연산자 확인 (기본값은 'eq')
            op = operator.get(k, 'eq') if operator else 'eq'
            
            # 숫자 비교 연산자인 경우 값 변환
            if op in ['gt', 'gte', 'lt', 'lte']:
                v = convert_to_number(v)
                
            # 연산자에 따른 표현식 생성
            expr = create_filter_expression(k, op, v)
            condition = expr if condition is None else condition & expr
            
        scan_kwargs["FilterExpression"] = condition
    
    # 프로젝션 표현식 추가
    if projection:
        projection_expression, expression_attribute_names = build_projection_expression(projection)
        
        if projection_expression and expression_attribute_names:
            scan_kwargs["ProjectionExpression"] = projection_expression
            scan_kwargs["ExpressionAttributeNames"] = expression_attribute_names
        
    return scan_kwargs 