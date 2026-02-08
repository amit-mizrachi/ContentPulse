# LLM Judge - System Specification

## Overview

LLM Judge is a **microservices-based system** for evaluating Large Language Model (LLM) responses. It accepts user prompts, executes inference against target models (via OpenAI), evaluates the responses using a judge model, and persists the results for historical analysis.

The system follows an **asynchronous message-driven architecture** using AWS SQS/SNS for inter-service communication.

---

## Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   User/Client   │
                                    └────────┬────────┘
                                             │ POST /submit
                                             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        GATEWAY SERVICE (Port 8000)                          │
│  - Accepts GatewayRequest (prompt, target_model, api_key, judge_model)     │
│  - Generates request_id (UUID)                                              │
│  - Stores ProcessedRequest in Redis (stage=Gateway)                         │
│  - Publishes InferenceMessage to SNS inference topic                        │
│  - Returns request_id to caller                                             │
└────────────────────────────────────────┬───────────────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  AWS SNS (inference) │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  AWS SQS (inference) │
                              └──────────┬───────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      INFERENCE SERVICE (Port 8003)                          │
│  - Polls SQS for InferenceMessage                                          │
│  - Updates Redis: stage=Inference                                           │
│  - Calls OpenAI API with user's prompt                                      │
│  - Stores InferenceResult in Redis                                          │
│  - Publishes JudgeMessage to SNS judge topic                                │
└────────────────────────────────────────┬───────────────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │    AWS SNS (judge)   │
                              └──────────┬───────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │    AWS SQS (judge)   │
                              └──────────┬───────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                        JUDGE SERVICE (Port 8004)                            │
│  - Polls SQS for JudgeMessage                                              │
│  - Updates Redis: stage=Judge                                               │
│  - Calls Judge Inference Service to score response                          │
│  - Updates Redis: stage=Completed, stores JudgeResult                       │
│  - Persists RequestHistory to MySQL via Persistence Service                 │
└────────────────────────────────────────┬───────────────────────────────────┘
                                         │
                                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                     PERSISTENCE SERVICE (Port 8002)                         │
│  - FastAPI HTTP server for database operations                              │
│  - Repository pattern for data access                                       │
│  - SQLAlchemy ORM with MySQL                                                │
└────────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────────────────┐
                    │        SUPPORTING SERVICES         │
                    ├───────────────────────────────────┤
                    │  Redis Service (Port 8001)        │
                    │  - HTTP wrapper for Redis         │
                    │  - Request state management       │
                    │  - 7-day TTL on cached data       │
                    ├───────────────────────────────────┤
                    │  Redis (Port 6379)                │
                    │  - In-memory cache                │
                    ├───────────────────────────────────┤
                    │  MySQL (Port 3306)                │
                    │  - Persistent storage             │
                    └───────────────────────────────────┘
```

---

## Directory Structure

```
LLM_Judge/
├── ingress_gateway_service/        # Entry point for user requests
│   ├── server.py                   # FastAPI HTTP server
│   ├── request_manager.py          # Request orchestration
│   └── Dockerfile
│
├── external_inference_service/     # LLM inference worker
│   ├── server.py                   # Async queue consumer
│   ├── inference_manager.py        # OpenAI API integration
│   └── Dockerfile
│
├── judge_service/                  # Response evaluation worker
│   ├── server.py                   # Async queue consumer
│   ├── judge_manager.py            # Judge scoring logic
│   └── Dockerfile
│
├── redis_service/                  # Redis HTTP wrapper
│   ├── server.py                   # FastAPI HTTP server
│   ├── redis_manager.py            # Direct Redis client
│   └── Dockerfile
│
├── persistence_service/            # Database service
│   ├── server.py                   # FastAPI HTTP server
│   ├── db_manager.py               # SQLAlchemy session factory
│   ├── models/
│   │   ├── base.py                 # Declarative base
│   │   └── history.py              # RequestHistory model
│   └── repositories/
│       ├── base_repository.py      # Generic CRUD operations
│       └── history_repository.py   # History-specific queries
│
├── objects/                        # Shared data models (Pydantic)
│   ├── enums/
│   │   ├── processed_request.py    # Request state model
│   │   ├── request_stage.py        # Pipeline stages enum
│   │   └── request_status.py       # Status values enum
│   ├── requests/
│   │   ├── gateway_request.py      # User input model
│   │   └── history_request.py      # History creation model
│   ├── responses/
│   │   ├── gateway_response.py     # Initial response model
│   │   └── history_response.py     # History query response
│   ├── results/
│   │   ├── inference_result.py     # LLM output model
│   │   └── judge_result.py         # Judge scoring model
│   ├── messages/
│   │   ├── base_message.py         # Common message fields
│   │   ├── inference_message.py    # Inference task message
│   │   └── judge_message.py        # Judge task message
│   ├── target_models/
│   │   └── target_model.py         # Target LLM config
│   └── judge_models/
│       └── judge_model.py          # Judge model config
│
├── utils/                          # Shared utilities
│   ├── services/                   # External service clients
│   │   ├── appconfig_service.py    # AWS AppConfig client
│   │   ├── openai_client.py        # OpenAI API wrapper
│   │   ├── judge_inference_client.py
│   │   ├── redis_client.py         # Redis HTTP client
│   │   ├── persistence_client.py   # Persistence HTTP client
│   │   ├── sqs_service.py          # AWS SQS client
│   │   ├── sns_service.py          # AWS SNS client
│   │   ├── health_server.py        # Health check server
│   │   └── service_config.py       # Port configuration
│   ├── queue/                      # Message queue infrastructure
│   │   ├── queue_consumer.py       # Main consumer orchestrator
│   │   ├── queue_message_handler.py
│   │   ├── queue_message_processor.py
│   │   ├── queue_message_parser.py
│   │   ├── queue_poller.py
│   │   ├── queue_visibility_extender.py
│   │   └── context_preserving_executor.py
│   ├── observability/              # Logging & tracing
│   │   └── observability_base.py
│   └── singleton.py
│
├── tests/
│   ├── unit/                       # Unit tests (153 tests)
│   └── integration/                # Integration tests
│
├── docker/
│   └── Dockerfile.base             # Base image with dependencies
├── docker-compose.yml              # Local development stack
├── requirements.txt
├── appconfig.example.json
└── .env.example
```

---

## Services

### 1. Ingress Gateway Service (Port 8000)

**Purpose**: Entry point for all user requests.

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| POST | `/submit` | Submit a new inference request |
| GET | `/metadata/{request_id}` | Get request status and metadata |
| GET | `/health` | Health check |

**Request Flow**:
1. Receive `GatewayRequest` with prompt, target model, API key, judge model
2. Generate unique request ID (UUID)
3. Create `ProcessedRequest` with `stage=Gateway`
4. Store in Redis via Redis Service
5. Publish `InferenceMessage` to SNS inference topic
6. Return `GatewayResponse` with request_id

---

### 2. External Inference Service (Port 8003)

**Purpose**: Consumes inference tasks and calls OpenAI API.

**Model Mapping**:
| Friendly Name | OpenAI Model ID |
|---------------|-----------------|
| ChatGPT | gpt-4o-mini |
| GPT-4 | gpt-4 |
| GPT-4o | gpt-4o |
| GPT-4o-mini | gpt-4o-mini |

**Processing Flow**:
1. Poll SQS `inference_queue` for messages
2. Parse `InferenceMessage`
3. Update Redis: `stage=Inference`
4. Call OpenAI API with user's prompt and API key
5. Create `InferenceResult` (response, latency, tokens)
6. Store result in Redis
7. Publish `JudgeMessage` to SNS judge topic
8. Delete SQS message

---

### 3. Judge Service (Port 8004)

**Purpose**: Evaluates LLM responses using a judge model.

**Processing Flow**:
1. Poll SQS `judge_queue` for messages
2. Parse `JudgeMessage`
3. Update Redis: `stage=Judge`
4. Call Judge Inference Service
5. Create `JudgeResult` (score, reasoning, categories)
6. Update Redis: `stage=Completed`
7. Convert `ProcessedRequest` to history data
8. Persist to MySQL via Persistence Service
9. Delete SQS message

---

### 4. Redis Service (Port 8001)

**Purpose**: HTTP wrapper for Redis operations.

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| POST | `/requests` | Create request state |
| GET | `/requests/{request_id}` | Get request state |
| PUT | `/requests/{request_id}` | Update request state |
| DELETE | `/requests/{request_id}` | Delete request state |
| GET | `/health` | Health check |

**Features**:
- 7-day TTL on cached data
- JSON serialization of Pydantic models
- Key format: `request:{request_id}`

---

### 5. Persistence Service (Port 8002)

**Purpose**: Long-term storage of completed requests.

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| POST | `/history` | Create history record |
| GET | `/history` | List history (paginated, filterable) |
| GET | `/history/{request_id}` | Get history by request ID |
| GET | `/health` | Health check |

**Architecture**:
- Repository pattern with generic CRUD operations
- `BaseRepository` provides: create, get_by_id, get_all, update, delete
- `HistoryRepository` adds: get_by_request_id, get_by_status
- Context manager access: `with db_manager.history() as repo`

---

## Data Models

### Request Stage Progression

```
Gateway → Inference → Judge → Completed
                ↓           ↓
              Failed      Failed
```

### ProcessedRequest (Redis)

```python
class ProcessedRequest:
    request_id: str
    gateway_request: GatewayRequest
    stage: RequestStage  # Gateway|Inference|Judge|Completed|Failed
    inference_result: Optional[InferenceResult]
    judge_result: Optional[JudgeResult]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### GatewayRequest

```python
class GatewayRequest:
    prompt: str
    target_model: TargetModel
    api_key: SecretStr
    judge_model: JudgeModel
```

### InferenceResult

```python
class InferenceResult:
    response: str
    model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```

### JudgeResult

```python
class JudgeResult:
    score: float
    reasoning: str
    categories: Optional[dict]
    model: str
    latency_ms: float
```

### RequestHistory (MySQL)

```sql
CREATE TABLE request_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    request_id VARCHAR(36) UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    target_model VARCHAR(100) NOT NULL,
    judge_model VARCHAR(100) NOT NULL,
    inference_response TEXT,
    inference_latency_ms FLOAT,
    inference_tokens INT,
    judge_score FLOAT,
    judge_reasoning TEXT,
    judge_categories JSON,
    judge_latency_ms FLOAT,
    status VARCHAR(20) NOT NULL,  -- Completed|Failed
    error_message TEXT,
    created_at DATETIME NOT NULL,
    completed_at DATETIME NOT NULL,

    INDEX idx_request_id (request_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

---

## Queue Messages

### InferenceMessage

```json
{
    "request_id": "uuid-string",
    "gateway_request": {
        "prompt": "What is 2+2?",
        "target_model": {"name": "ChatGPT"},
        "api_key": "sk-...",
        "judge_model": {"name": "qwen", "version": "2.5:latest"}
    },
    "topic_name": "inference"
}
```

### JudgeMessage

```json
{
    "request_id": "uuid-string",
    "gateway_request": {...},
    "inference_result": {
        "response": "The answer is 4.",
        "model": "gpt-4o-mini",
        "latency_ms": 523.4,
        "prompt_tokens": 12,
        "completion_tokens": 8,
        "total_tokens": 20
    },
    "topic_name": "judge"
}
```

---

## Configuration

### AWS AppConfig Structure

```json
{
    "aws": {
        "region": "us-east-1"
    },
    "sqs": {
        "inference_queue_url": "https://sqs...",
        "judge_queue_url": "https://sqs...",
        "max_worker_count": 10,
        "visibility_timeout_seconds": 300,
        "visibility_extension_interval_seconds": 30
    },
    "sns": {
        "inference_topic_arn": "arn:aws:sns:...",
        "judge_topic_arn": "arn:aws:sns:..."
    },
    "redis": {
        "host": "redis",
        "port": 6379,
        "default_ttl_seconds": 604800
    },
    "mysql": {
        "host": "mysql",
        "port": 3306,
        "user": "llm_judge",
        "password": "password",
        "database": "llm_judge"
    },
    "services": {
        "redis": {"host": "redis-service", "port": 8001},
        "persistence": {"host": "persistence-service", "port": 8002},
        "judge_inference": {"host": "judge-inference-service", "port": 8003}
    }
}
```

### Environment Variables

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# AppConfig Bootstrap
APPCONFIG_APPLICATION_ID=
APPCONFIG_ENVIRONMENT_ID=
APPCONFIG_PROFILE_ID=

# MySQL (local docker-compose)
MYSQL_ROOT_PASSWORD=
MYSQL_DATABASE=llm_judge
MYSQL_USER=llm_judge
MYSQL_PASSWORD=
```

### Service Ports

| Service | Port |
|---------|------|
| Gateway | 8000 |
| Redis Service | 8001 |
| Persistence Service | 8002 |
| Inference Service | 8003 |
| Judge Service | 8004 |
| Redis (infra) | 6379 |
| MySQL (infra) | 3306 |

---

## External Dependencies

### AWS Services
- **SQS**: Message queues (inference_queue, judge_queue)
- **SNS**: Pub/sub topics (inference, judge)
- **AppConfig**: Centralized configuration

### Third-Party APIs
- **OpenAI**: LLM inference (GPT-4, GPT-4o, GPT-4o-mini)

### Infrastructure
- **Redis**: In-memory cache (7-day TTL)
- **MySQL**: Persistent storage

---

## Design Patterns

| Pattern | Usage |
|---------|-------|
| Singleton | Service clients (AppConfigService, SNSService, RedisClient, etc.) |
| Repository | Data access layer (BaseRepository, HistoryRepository) |
| Context Manager | Database sessions and repository access |
| Message Handler | Base class for queue consumers |
| Factory | DBManager provides repository instances |

---

## Testing

**153 tests** across unit and integration suites:

```
tests/
├── unit/
│   ├── test_gateway_service.py
│   ├── test_inference_service.py
│   ├── test_judge_service.py
│   ├── test_persistence_service.py
│   ├── test_redis_service.py
│   ├── test_services.py
│   ├── test_objects.py
│   └── test_queue.py
└── integration/
    ├── flows/
    │   ├── test_gateway_to_inference_flow.py
    │   └── test_inference_to_judge_flow.py
    ├── messaging/
    │   └── test_sqs_message_parsing.py
    ├── lifecycle/
    │   └── test_request_state_transitions.py
    └── serialization/
        └── test_model_serialization.py
```

Run tests:
```bash
python3 -m pytest tests/ -v
```

---

## Docker Deployment

### Local Development

```bash
docker-compose up --build
```

### Service Dependencies

```
gateway-service ──► redis-service ──► redis
invoke-service  ──► redis-service
judge-service   ──► redis-service
                ──► persistence-service ──► mysql
```

---

## API Examples

### Submit Request

```bash
curl -X POST http://localhost:8000/submit \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "target_model": {"name": "ChatGPT"},
    "api_key": "sk-your-openai-key",
    "judge_model": {"name": "qwen", "version": "2.5:latest"}
  }'

# Response
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "Accepted"
}
```

### Get Request Status

```bash
curl http://localhost:8000/metadata/550e8400-e29b-41d4-a716-446655440000

# Response
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "Completed",
  "inference_result": {...},
  "judge_result": {...}
}
```

### Get History

```bash
curl "http://localhost:8002/history?limit=10&status=Completed"

# Response
[
  {
    "id": 1,
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "prompt": "What is the capital of France?",
    "target_model": "ChatGPT",
    "judge_model": "qwen2.5:latest",
    "inference_response": "The capital of France is Paris.",
    "judge_score": 0.95,
    "status": "Completed",
    ...
  }
]
```
