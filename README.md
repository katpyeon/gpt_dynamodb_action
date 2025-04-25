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
- AWS 액세스 키 및 시크릿 키

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

3. 환경 변수 설정 (.env 파일 생성):
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=ap-northeast-2
   DYNAMO_TABLE_NAME=your_table_name
   ```

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

DynamoDB 테이블 스캔:

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

## 라이선스

MIT
