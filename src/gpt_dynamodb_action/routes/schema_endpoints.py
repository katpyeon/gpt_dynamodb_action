from fastapi import APIRouter

router = APIRouter()

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

@router.get("/privacy-policy")
def privacy_policy():
    """
    Returns privacy policy information for the application.
    """
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