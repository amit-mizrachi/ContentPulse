import json
import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


@pytest.fixture
def mock_appconfig():
    """Mock AppConfigService for testing."""
    config = {
        "aws.region": "us-east-1",
        "sqs.inference_queue_url": "https://sqs.us-east-1.amazonaws.com/123/inference-queue",
        "sqs.judge_queue_url": "https://sqs.us-east-1.amazonaws.com/123/judge-queue",
        "sqs.max_worker_count": 10,
        "sqs.visibility_timeout_seconds": 300,
        "sqs.visibility_extension_interval_seconds": 30,
        "sqs.max_message_process_time_seconds": 600,
        "sqs.seconds_between_receive_attempts": 1,
        "sqs.wait_time_seconds": 1,
        "sqs.consumer_shutdown_timeout_seconds": 30,
        "sns.inference_topic_arn": "arn:aws:sns:us-east-1:123:inference",
        "sns.judge_topic_arn": "arn:aws:sns:us-east-1:123:judge",
        "redis.host": "localhost",
        "redis.port": 6379,
        "redis.default_ttl_seconds": 604800,
        "mysql.host": "localhost",
        "mysql.port": 3306,
        "mysql.user": "test_user",
        "mysql.password": "test_pass",
        "mysql.database": "test_db",
        "services.redis.host": "redis-service",
        "services.redis.port": 8001,
        "services.persistence.host": "persistence-service",
        "services.persistence.port": 8002,
        "services.judge_inference.host": "judge-inference-service",
        "services.judge_inference.port": 8003,
        "observability.logs.files.path": "/tmp/logs",
        "observability.logs.files.buffer_capacity": 100,
        "observability.logs.minimum_logging_levels.logger": "INFO",
        "observability.logs.minimum_logging_levels.files_handler": "DEBUG",
        "observability.logs.minimum_logging_levels.stdout_handler": "INFO",
        "messaging.broker": "sns_sqs",
        "kafka.bootstrap_servers": "localhost:9092",
        "kafka.group_id": "llm-judge",
        "kafka.client_id": "llm-judge-producer",
        "kafka.auto_offset_reset": "earliest",
        "kafka.inference_topic": "llm-judge-inference",
        "kafka.judge_topic": "llm-judge-judge",
        "environment": "test",
        "service_name": "test-service",
    }

    mock = MagicMock()
    mock.get = lambda key, default=None: config.get(key, default)
    return mock


@pytest.fixture
def sample_gateway_request():
    """Sample gateway request data."""
    return {
        "prompt": "What is 2+2?",
        "target_model": {"name": "ChatGPT"},
        "api_key": "sk-test-key",
        "judge_model": {"name": "qwen2.5", "version": "latest"}
    }


@pytest.fixture
def sample_inference_result():
    """Sample inference result data."""
    return {
        "response": "2+2 equals 4.",
        "model": "gpt-4o-mini",
        "latency_ms": 150.5,
        "prompt_tokens": 10,
        "completion_tokens": 8,
        "total_tokens": 18
    }


@pytest.fixture
def sample_judge_result():
    """Sample judge result data."""
    return {
        "score": 0.95,
        "reasoning": "The answer is correct and concise.",
        "categories": {
            "relevance": 1.0,
            "accuracy": 1.0,
            "helpfulness": 0.9,
            "safety": 1.0
        },
        "model": "qwen2.5:latest",
        "latency_ms": 200.0
    }


@pytest.fixture
def sample_processed_request(sample_gateway_request):
    """Sample processed request data."""
    return {
        "request_id": "test-uuid-1234",
        "gateway_request": sample_gateway_request,
        "stage": "Gateway",
        "inference_result": None,
        "judge_result": None,
        "error_message": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
