# GPT DynamoDB Action API

DynamoDB 데이터베이스에 액세스하기 위한 OpenAPI 서버로, ChatGPT Actions와 함께 사용할 수 있습니다.

## 기술 스택

- Python 3.9+
- FastAPI
- boto3 (AWS SDK)
- Poetry (의존성 관리)
- AWS DynamoDB

## 설치 및 실행

### 사전 요구사항

- Python 3.9+
- Poetry
- AWS 계정 및 DynamoDB 테이블
- AWS 자격 증명 설정 완료

### 환경 설정

1. 저장소 클론하기:

   ```bash
   git clone https://github.com/yourusername/gpt_dynamodb_action.git
   cd gpt_dynamodb_action
   ```

2. 의존성 설치:

   ```bash
   poetry install
   ```

3. 환경 변수 설정:
   - `.env.example` 파일을 `.env`로 복사:
     ```bash
     cp .env.example .env
     ```
   - `.env` 파일을 열어 필요한 값들을 설정:
     ```ini
     # AWS 자격 증명 설정
     AWS_ACCESS_KEY_ID=your_access_key_id
     AWS_SECRET_ACCESS_KEY=your_secret_access_key
     AWS_REGION=ap-northeast-2

     # DynamoDB 설정
     DYNAMO_TABLE_NAME=your_table_name

     # 서버 설정 (선택사항)
     HOST=localhost
     PORT=8000
     DEBUG=False
     ```

   > **중요**: `.env` 파일은 민감한 정보를 포함하고 있으므로 절대로 깃허브에 커밋하지 마세요.
   > AWS 자격 증명은 IAM 모범 사례에 따라 적절한 권한을 가진 사용자의 것을 사용하세요.

### 서버 실행

로컬에서 서버 실행:

```bash
poetry run python -m src.gpt_dynamodb_action.main
```

서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

## Ngrok으로 로컬 서버 공개 접속 설정

1. [Ngrok 다운로드 및 설치](https://ngrok.com/download)

2. Ngrok 인증:

   ```bash
   ngrok config add-authtoken YOUR_NGROK_TOKEN
   ```

3. 로컬 서버를 외부에 노출:

   ```bash
   ngrok http 8000
   ```

4. Ngrok이 제공하는 URL을 복사 (예: `https://abcd1234.ngrok-free.app`)

5. `src/gpt_dynamodb_action/main.py` 파일에서 Ngrok URL 업데이트:
   ```python
   app = FastAPI(
       title="GPT DynamoDB Scanner API",
       version="1.0.0",
       servers=[
           {
               "url": "https://abcd1234.ngrok-free.app",  # 여기에 Ngrok URL 넣기
               "description": "Ngrok tunnel for local development"
           }
       ]
   )
   ```

## ChatGPT Actions 추가 방법

1. [OpenAI 개발자 포털](https://platform.openai.com/apps)에 로그인

2. GPTs 섹션에서 액션을 추가할 GPT 생성 또는 선택

3. 구성(Configure) 탭에서 "Actions"로 이동

4. "Add Action" 클릭 후 정보 입력:

   - Authentication: 필요에 따라 설정
   - API 스키마: OpenAPI 스키마 URL 입력 (예: `https://abcd1234.ngrok-free.app/openapi.json`)
   - 필요한 경우 특정 엔드포인트만 사용하도록 지정

5. 저장 후 GPT에 액션 테스트

## API 사용 예시

### 테이블 스캔

```bash
curl -X POST "http://localhost:8000/scan_table" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {"PK": "COM#"},
    "operator": {"PK": "begins_with"},
    "limit": 5,
    "projection": ["PK", "SK", "name", "createdAt"]
  }'
```

### 테이블 쿼리

```bash
curl -X POST "http://localhost:8000/query_table" \
  -H "Content-Type: application/json" \
  -d '{
    "pk": "USER#123",
    "sk": "POST#",
    "sk_operator": "begins_with",
    "filters": {
      "status": "active",
      "category": "tech"
    },
    "filter_values": {
      "status": "eq",
      "category": "eq"
    },
    "limit": 100,
    "projection": ["PK", "SK", "name", "createdAt"]
  }'
```

### 단일 항목 조회

```bash
curl -X POST "http://localhost:8000/get_item" \
  -H "Content-Type: application/json" \
  -d '{
    "pk": "USER#123",
    "sk": "POST#456",
    "projection": ["PK", "SK", "name", "createdAt", "content"]
  }'
```

#### query_table 파라미터 설명

- `pk`: (필수) 파티션 키 값 (eq 연산만 지원)
- `sk`: (선택) 정렬 키 값
- `sk_operator`: (선택) 정렬 키 연산자 ("eq" 또는 "begins_with")
- `filters`: (선택) 추가 필터 조건의 키-값 쌍
- `filter_values`: (선택) 필터 조건의 연산자 지정
- `limit`: (선택) 반환할 최대 항목 수 (기본값: 100)
- `projection`: (선택) 반환할 속성 목록 (기본값: ["PK", "SK", "name", "createdAt"])
- `last_evaluated_key`: (선택) 페이지네이션을 위한 마지막 평가 키

#### get_item 파라미터 설명

- `pk`: (필수) 파티션 키 값
- `sk`: (필수) 정렬 키 값
- `projection`: (선택) 반환할 속성 목록 (기본값: ["PK", "SK", "name", "createdAt"])

## 데이터 조회 최적화 지침

DynamoDB의 특성을 고려한 효율적인 데이터 조회를 위해 다음 순서로 API를 사용하는 것을 권장합니다:

1. `scan_table`: 전체 테이블 스캔이 필요한 경우에만 사용 (비용이 많이 들고 성능이 저하될 수 있음)
2. `query_table`: 파티션 키(PK)를 알고 있는 경우 사용. 정렬 키(SK)로 필터링 가능
3. `get_item`: 정확한 PK와 SK 값을 알고 있는 경우 사용 (가장 효율적이고 비용 효과적)

이러한 순서로 데이터를 조회하도록 설계하면 DynamoDB의 성능을 최적화하고 비용을 절감할 수 있습니다.

## 라이선스

MIT
