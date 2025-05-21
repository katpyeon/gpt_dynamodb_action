# GPT DynamoDB Action API

An OpenAPI server for accessing DynamoDB databases, designed for use with ChatGPT Actions.

## Tech Stack

- Python 3.9+
- FastAPI
- boto3 (AWS SDK)
- Poetry (dependency management)
- AWS DynamoDB

## Installation & Run

### Prerequisites

- Python 3.9+
- Poetry
- AWS account and DynamoDB table
- AWS credentials configured

### Environment Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/gpt_dynamodb_action.git
   cd gpt_dynamodb_action
   ```

2. Install dependencies:

   ```bash
   poetry install
   ```

3. Set environment variables:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open the `.env` file and set the required values:
     ```ini
     # AWS credentials
     AWS_ACCESS_KEY_ID=your_access_key_id
     AWS_SECRET_ACCESS_KEY=your_secret_access_key
     AWS_REGION=ap-northeast-2

     # DynamoDB settings
     DYNAMO_TABLE_NAME=your_table_name

     # Server settings (optional)
     HOST=localhost
     PORT=8000
     DEBUG=False
     ```

   > **Important**: Never commit the `.env` file to GitHub as it contains sensitive information.
   > Use IAM best practices and only use credentials with the necessary permissions.

### Running the Server

To run the server locally:

```bash
poetry run python -m src.gpt_dynamodb_action.main
```

By default, the server runs at `http://localhost:8000`.

## Exposing Local Server with Ngrok

1. [Download and install Ngrok](https://ngrok.com/download)

2. Authenticate Ngrok:

   ```bash
   ngrok config add-authtoken YOUR_NGROK_TOKEN
   ```

3. Expose your local server:

   ```bash
   ngrok http 8000
   ```

4. Copy the URL provided by Ngrok (e.g., `https://abcd1234.ngrok-free.app`)

5. Update the Ngrok URL in `src/gpt_dynamodb_action/main.py`:
   ```python
   app = FastAPI(
       title="GPT DynamoDB Scanner API",
       version="1.0.0",
       servers=[
           {
               "url": "https://abcd1234.ngrok-free.app",  # Insert your Ngrok URL here
               "description": "Ngrok tunnel for local development"
           }
       ]
   )
   ```

## Adding ChatGPT Actions

1. Log in to the [OpenAI Developer Portal](https://platform.openai.com/apps)

2. In the GPTs section, create or select a GPT to add actions

3. Go to the Configure tab and select "Actions"

4. Click "Add Action" and fill in the details:

   - Authentication: Set as needed
   - API Schema: Enter the OpenAPI schema URL (e.g., `https://abcd1234.ngrok-free.app/openapi.json`)
   - Optionally, restrict to specific endpoints

5. Save and test the action in your GPT

## API Usage Examples

### Scan Table

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

### Query Table

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

### Get Single Item

```bash
curl -X POST "http://localhost:8000/get_item" \
  -H "Content-Type: application/json" \
  -d '{
    "pk": "USER#123",
    "sk": "POST#456",
    "projection": ["PK", "SK", "name", "createdAt", "content"]
  }'
```

#### query_table Parameter Description

- `pk`: (required) Partition key value (only "eq" operator supported)
- `sk`: (optional) Sort key value
- `sk_operator`: (optional) Sort key operator ("eq" or "begins_with")
- `filters`: (optional) Additional filter key-value pairs
- `filter_values`: (optional) Operators for filter conditions
- `limit`: (optional) Maximum number of items to return (default: 100)
- `projection`: (optional) List of attributes to return (default: ["PK", "SK", "name", "createdAt"])
- `last_evaluated_key`: (optional) Last evaluated key for pagination

#### get_item Parameter Description

- `pk`: (required) Partition key value
- `sk`: (required) Sort key value
- `projection`: (optional) List of attributes to return (default: ["PK", "SK", "name", "createdAt"])

## Data Retrieval Optimization Guidelines

For efficient data retrieval in DynamoDB, follow this recommended order:

1. `scan_table`: Use only when a full table scan is necessary (can be costly and slow)
2. `query_table`: Use when you know the partition key (PK); can filter with sort key (SK)
3. `get_item`: Use when you know both the exact PK and SK (most efficient and cost-effective)

Following this order will help optimize DynamoDB performance and reduce costs.

## License

MIT

---

<a href="https://www.buymeacoffee.com/katpyeon" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="40" />
</a>