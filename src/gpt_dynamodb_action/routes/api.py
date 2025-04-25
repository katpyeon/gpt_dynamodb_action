from fastapi import APIRouter, Body
from typing import Optional, Dict, List
import boto3
from boto3.dynamodb.conditions import Attr
import os
import logging
import json
from decimal import Decimal
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Decimal 타입 처리를 위한 JSONEncoder 클래스
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

load_dotenv()

router = APIRouter()

def get_table():
    session = boto3.Session(
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_REGION", "ap-northeast-2")
    )
    dynamodb = session.resource("dynamodb")
    return dynamodb.Table(os.environ["DYNAMO_TABLE_NAME"])

@router.get("/describe_table_schema")
def describe_table_schema():
    """
    Returns a comprehensive schema description of the DynamoDB table columns.
    Includes all field names and their descriptions in English.
    """
    return {
        "columns": {
            "PK": "Primary Partition Key",
            "SK": "Sort Key",
            "accountChannelCode": "Registration channel code",
            "accountLoginId": "Account login ID",
            "accountLoginPassword": "Account login password",
            "accountNewsSubscription": "Newsletter subscription consent status",
            "accountRegistrationSource": "User registration source",
            "accountRegistrationType": "Registration method (email, social login)",
            "activatedAt": "Account activation timestamp",
            "agreeTerm": "Terms agreement status",
            "authProvider": "External authentication provider (e.g., Google, Facebook)",
            "companyCode": "Company code",
            "companyDepartment": "Company department",
            "companyEmployeeNumber": "Employee ID number",
            "companyName": "Company name",
            "companySK": "Company detailed identifier (Sort Key)",
            "createdAt": "Creation timestamp",
            "dataType": "Data type identifier",
            "email": "Email address",
            "engName": "English name",
            "engNation": "Nationality in English",
            "estimate": "Estimated amount",
            "estimateFile": "Quotation file reference",
            "finishAt": "Service end timestamp",
            "gender": "Gender",
            "groupKey": "Group identification key",
            "groupName": "Group name",
            "idNumber": "ID number or national identification number",
            "insuranceCertificateUrl": "Insurance certificate URL",
            "insuranceEndDate": "Insurance end date",
            "insuranceEvacuationPlan": "Insurance evacuation plan",
            "insurancePlan": "Insurance plan type",
            "insuranceStartDate": "Insurance start date",
            "linkPaperGuide": "Paper application guide link",
            "linkPaperJoin": "Paper application submission link",
            "linkPaperJoinEng": "Paper application submission link (English)",
            "managerEmail": "Manager's email",
            "managerName": "Manager's name",
            "managerTel": "Manager's phone number",
            "membershipCertificateUrl": "Corporate membership certificate URL",
            "membershipCorporateType": "Corporate membership type",
            "membershipEndDate": "Corporate membership end date",
            "membershipPersonalType": "Corporate membership individual type",
            "membershipStartDate": "Corporate membership start date",
            "name": "Name",
            "nation": "Country",
            "paidAt": "Payment timestamp",
            "paidPrice": "Payment amount",
            "period": "Usage period",
            "policyNumber": "Insurance policy number",
            "price": "Base price",
            "productName": "Product name",
            "productSk": "Product detailed identifier (SK)",
            "receipts": "Receipt list or file reference",
            "registrationCount": "Registration count",
            "registrationNumber": "Registration number",
            "residenceBusinessTripType": "Stay type (residence/business trip)",
            "residenceCityCode": "Residence city code",
            "residenceCountryCode": "Residence country code",
            "residenceCountryName": "Residence country name",
            "residenceEndDate": "Residence end date",
            "residenceStartDate": "Residence start date",
            "residenceStayType": "Residence type (short-term/long-term)",
            "startAt": "Start timestamp",
            "status": "Status (e.g., active, expired)",
            "tel": "Phone number",
            "timestamp": "Timestamp (Unix epoch)",
            "totalPrice": "Total amount",
            "trainingInfo": "Training information",
            "updatedAt": "Update timestamp",
            "userBirthDate": "User birth date",
            "userEmail": "User email address",
            "userEmergencyContact": "Emergency contact",
            "userEnglishName": "User's English name",
            "userGender": "User gender",
            "userName": "User's full name",
            "userNote": "User note/memo",
            "userPhone": "User phone number",
            "userRegistrationNumber": "User registration number or ID number",
            "userRelation": "Relationship to applicant (self, spouse, etc.)",
            "userType": "User type (admin, regular, guest, etc.)"
        }
    }

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
    scan_kwargs = _build_scan_kwargs(filters, operator, start_key, projection)
    
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
        scan_result = _execute_scan(table, scan_kwargs, current_start_key)
        
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
    response_data = _prepare_response_data(all_items, last_evaluated_key, total_scanned_count)
    
    # 응답 크기 측정
    response_json = json.dumps(response_data)
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


def _build_scan_kwargs(filters, operator, start_key, projection=None):
    """필터와 연산자를 기반으로 DynamoDB 스캔 파라미터를 구성합니다."""
    scan_kwargs = {}
    
    if filters:
        condition = None
        for k, v in filters.items():
            # 연산자 확인 (기본값은 'eq')
            op = operator.get(k, 'eq') if operator else 'eq'
            
            # 숫자 비교 연산자인 경우 값 변환
            if op in ['gt', 'gte', 'lt', 'lte']:
                v = _convert_to_number(v)
                
            # 연산자에 따른 표현식 생성
            expr = _create_filter_expression(k, op, v)
            condition = expr if condition is None else condition & expr
            
        scan_kwargs["FilterExpression"] = condition
    
    # 프로젝션 표현식 추가
    if projection:
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
        scan_kwargs["ProjectionExpression"] = ", ".join(projection_expression_names)
        scan_kwargs["ExpressionAttributeNames"] = expression_attribute_names
        
    return scan_kwargs


def _convert_to_number(value):
    """문자열 값을 가능한 경우 숫자로 변환합니다."""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _create_filter_expression(key, operator, value):
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


def _execute_scan(table, scan_kwargs, current_start_key):
    """DynamoDB 테이블에 대한 스캔을 실행합니다."""
    # 시작 키 설정
    if current_start_key:
        scan_kwargs["ExclusiveStartKey"] = current_start_key
    elif "ExclusiveStartKey" in scan_kwargs:
        del scan_kwargs["ExclusiveStartKey"]
        
    return table.scan(**scan_kwargs)


def _prepare_response_data(items, last_evaluated_key, total_scanned_count):
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

@router.get("/privacy-policy")
def privacy_policy():
    return {
        "purpose": "DynamoDB 기반 고객 질의 자동화",
        "collected_fields": ["userName", "email", "userBirthDate", "companyCode", ...],
        "storage": "AWS DynamoDB (region: ap-northeast-2)",
        "retention": "계약 종료 또는 서비스 이용 해지 시까지",
        "third_party": "OpenAI API를 통한 GPT 호출 외, 제3자 제공 없음",
        "security": "IAM 권한 통제 및 TLS 보안 사용",
        "notes": "주민등록번호, 계좌번호, 카드번호 등의 민감 정보는 입력하지 마세요."
    }

@router.get("/describe_key_design")
def describe_key_design():
    """
    Describes the DynamoDB key design patterns used in the database.
    Includes information about PK (Partition Key), SK (Sort Key) patterns, and brief explanations.
    """
    return {
        "key_patterns": [
            {
                "entity_type": "user",
                "description": "Mostly administrators",
                "pk_pattern": "USR#{email}",
                "sk_pattern": "USR#{email}",
                "example": {
                    "PK": "USR#john@example.com",
                    "SK": "USR#john@example.com"
                },
                "notes": "Single-item access pattern based on email address"
            },
            {
                "entity_type": "company",
                "description": "Mostly sellers/vendors",
                "pk_pattern": "COM#",
                "sk_pattern": "COM#{companyCode}",
                "example": {
                    "PK": "COM#",
                    "SK": "COM#ABC123"
                },
                "notes": "Access company info by company code, query all companies with PK='COM#'"
            },
            {
                "entity_type": "product",
                "description": "Insurance, membership, or combined products",
                "pk_pattern": "PROD#",
                "sk_pattern": "PROD#{INSU|MSB|CMD}#{short uuid}",
                "example": {
                    "PK": "PROD#",
                    "SK": "PROD#INSU#a7ud3fc94X"
                },
                "notes": "Distinguished by product type (INSU: Insurance, MSB: Membership, CMD: Combined) and UUID"
            },
            {
                "entity_type": "groupInsurance",
                "description": "Company group insurance subscription",
                "pk_pattern": "COM#GRPINSU#{companyCode}",
                "sk_pattern": "COM#GRPINSU#{companyCode}#{timestamp}",
                "example": {
                    "PK": "COM#GRPINSU#ABC123",
                    "SK": "COM#GRPINSU#ABC123#1621234567890"
                },
                "notes": "Company group insurance info, chronological access using timestamp"
            },
            {
                "entity_type": "groupInsuranceMember",
                "description": "Group insurance members",
                "pk_pattern": "COM#MEM#{companyCode}",
                "sk_pattern": "COM#MEM#{companyCode}#{timestamp}#{number}",
                "example": {
                    "PK": "COM#MEM#ABC123",
                    "SK": "COM#MEM#ABC123#1621234567890#001"
                },
                "notes": "Company membership user info, distinguished by timestamp and sequence number"
            },
            {
                "entity_type": "insuplus",
                "description": "Members registered in InsuPlus admin system",
                "pk_pattern": "INSUPLUS#",
                "sk_pattern": "INSUPLUS#{ulid}",
                "example": {
                    "PK": "INSUPLUS#",
                    "SK": "INSUPLUS#01H5TWVJ4NT8B93M8T70HC20XK"
                },
                "notes": "InsuPlus system members, chronological access using ULID"
            }
        ],
        "access_patterns": [
            {
                "description": "Get individual user",
                "pattern": "GET PK='USR#{email}' SK='USR#{email}'"
            },
            {
                "description": "List all companies",
                "pattern": "QUERY PK='COM#'"
            },
            {
                "description": "Get specific company",
                "pattern": "GET PK='COM#' SK='COM#{companyCode}'"
            },
            {
                "description": "List all products",
                "pattern": "QUERY PK='PROD#'"
            },
            {
                "description": "List insurance products only",
                "pattern": "QUERY PK='PROD#' SK begins_with 'PROD#INSU#'"
            },
            {
                "description": "List all group insurance for a company",
                "pattern": "QUERY PK='COM#GRPINSU#{companyCode}'"
            },
            {
                "description": "List all members for a company",
                "pattern": "QUERY PK='COM#MEM#{companyCode}'"
            },
            {
                "description": "List all InsuPlus members",
                "pattern": "QUERY PK='INSUPLUS#'"
            }
        ],
        "design_principles": [
            "Single-table design: All entities stored in one table",
            "PK (Partition Key) for data grouping, SK (Sort Key) for individual item identification",
            "Prefixes (USR#, COM#, PROD#, etc.) to differentiate data types",
            "Timestamps and UUIDs for uniqueness and chronological sorting",
            "dataType attribute for additional item type distinction"
        ]
    }