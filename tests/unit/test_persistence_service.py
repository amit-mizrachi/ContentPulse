"""Unit tests for persistence_service module."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestRequestHistory:
    def test_model_columns(self):
        from src.services.persistence.models import RequestHistory

        assert hasattr(RequestHistory, 'id')
        assert hasattr(RequestHistory, 'request_id')
        assert hasattr(RequestHistory, 'prompt')
        assert hasattr(RequestHistory, 'target_model')
        assert hasattr(RequestHistory, 'judge_model')
        assert hasattr(RequestHistory, 'inference_response')
        assert hasattr(RequestHistory, 'inference_latency_ms')
        assert hasattr(RequestHistory, 'inference_tokens')
        assert hasattr(RequestHistory, 'judge_score')
        assert hasattr(RequestHistory, 'judge_reasoning')
        assert hasattr(RequestHistory, 'judge_categories')
        assert hasattr(RequestHistory, 'judge_latency_ms')
        assert hasattr(RequestHistory, 'status')
        assert hasattr(RequestHistory, 'error_message')
        assert hasattr(RequestHistory, 'created_at')
        assert hasattr(RequestHistory, 'completed_at')

    def test_table_name(self):
        from src.services.persistence.models import RequestHistory

        assert RequestHistory.__tablename__ == "request_history"


class TestBaseRepository:
    def test_create(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance

        repo = BaseRepository(mock_session, mock_model)
        result = repo.create({"field": "value"})

        mock_model.assert_called_once_with(field="value")
        mock_session.add.assert_called_once_with(mock_instance)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_instance)
        assert result == mock_instance

    def test_get_by_id(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_instance = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_instance

        repo = BaseRepository(mock_session, mock_model)
        result = repo.get_by_id(1)

        mock_session.query.assert_called_once_with(mock_model)
        assert result == mock_instance

    def test_get_by_id_not_found(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        repo = BaseRepository(mock_session, mock_model)
        result = repo.get_by_id(999)

        assert result is None

    def test_get_all(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_items = [MagicMock(), MagicMock()]

        mock_query = MagicMock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_items
        mock_session.query.return_value = mock_query

        repo = BaseRepository(mock_session, mock_model)
        result = repo.get_all(limit=10, offset=0)

        assert result == mock_items
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(10)

    def test_get_all_with_filters(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_model.status = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_session.query.return_value = mock_query

        repo = BaseRepository(mock_session, mock_model)
        repo.get_all(limit=10, offset=0, filters={"status": "Completed"})

        mock_query.filter.assert_called()

    def test_update(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_instance = MagicMock()
        mock_instance.status = "Pending"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_instance

        repo = BaseRepository(mock_session, mock_model)
        result = repo.update(1, {"status": "Completed"})

        assert mock_instance.status == "Completed"
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_instance)

    def test_update_not_found(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        repo = BaseRepository(mock_session, mock_model)
        result = repo.update(999, {"status": "Completed"})

        assert result is None

    def test_delete(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_instance = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_instance

        repo = BaseRepository(mock_session, mock_model)
        result = repo.delete(1)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_instance)
        mock_session.commit.assert_called_once()

    def test_delete_not_found(self):
        from src.services.persistence.repositories import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        repo = BaseRepository(mock_session, mock_model)
        result = repo.delete(999)

        assert result is False


class TestHistoryRepository:
    def test_get_by_request_id(self):
        from src.services.persistence.repositories import HistoryRepository

        mock_session = MagicMock()
        mock_history = MagicMock()
        mock_history.request_id = "test-123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_history

        repo = HistoryRepository(mock_session)
        result = repo.get_by_request_id("test-123")

        assert result is not None
        assert result.request_id == "test-123"

    def test_get_by_request_id_not_found(self):
        from src.services.persistence.repositories import HistoryRepository
        from src.services.persistence.repositories.history_repository import RequestHistoryNotFoundError

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        repo = HistoryRepository(mock_session)

        with pytest.raises(RequestHistoryNotFoundError):
            repo.get_by_request_id("non-existent")

    def test_get_by_status(self):
        from src.services.persistence.repositories import HistoryRepository

        mock_session = MagicMock()
        mock_history_list = [MagicMock(status="Completed") for _ in range(3)]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_history_list
        mock_session.query.return_value = mock_query

        repo = HistoryRepository(mock_session)
        result = repo.get_by_status("Completed", limit=10, offset=0)

        assert len(result) == 3


class TestDatabaseProvider:
    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_initialization(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        mock_create_engine.assert_called_once()
        connection_string = mock_create_engine.call_args[0][0]
        assert "mysql+pymysql://test:test@localhost:3306/test_db" in connection_string

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_session_context_manager(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        with provider.session() as session:
            assert session == mock_session

        mock_session.close.assert_called_once()

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_history_context_manager(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        from src.services.persistence.repositories import HistoryRepository
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        with provider.history_repository() as repo:
            assert isinstance(repo, HistoryRepository)

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_create_history_via_repository(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        history_data = {
            "request_id": "test-123",
            "prompt": "What is 2+2?",
            "target_model": "ChatGPT",
            "judge_model": "qwen2.5:latest",
            "status": "Completed",
            "created_at": datetime.utcnow(),
            "completed_at": datetime.utcnow()
        }

        with provider.history_repository() as repo:
            repo.create(history_data)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called()
        mock_session.refresh.assert_called_once()

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_get_history_by_request_id_via_repository(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_history = MagicMock()
        mock_history.request_id = "test-123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_history
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        with provider.history_repository() as repo:
            result = repo.get_by_request_id("test-123")

        assert result is not None
        assert result.request_id == "test-123"

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_get_history_by_request_id_not_found_via_repository(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        from src.services.persistence.repositories.history_repository import RequestHistoryNotFoundError

        with pytest.raises(RequestHistoryNotFoundError):
            with provider.history_repository() as repo:
                repo.get_by_request_id("non-existent")

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_get_history_with_pagination_via_repository(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_history_list = [MagicMock(request_id=f"test-{i}") for i in range(3)]

        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_history_list
        mock_session.query.return_value = mock_query
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        with provider.history_repository() as repo:
            result = repo.get_all(limit=10, offset=0, order_by="created_at", descending=True)

        assert len(result) == 3

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_get_history_with_status_filter_via_repository(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_session.status = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_session.query.return_value = mock_query
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        with provider.history_repository() as repo:
            repo.get_all(limit=10, offset=0, filters={"status": "Completed"})

        mock_query.filter.assert_called()

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_is_healthy_returns_true(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()
        result = provider.is_healthy()

        assert result is True
        mock_session.execute.assert_called_once()

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_is_healthy_returns_false(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("DB connection failed")
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()
        result = provider.is_healthy()

        assert result is False

    @patch('src.services.persistence.database_provider.create_engine')
    @patch('src.services.persistence.database_provider.sessionmaker')
    @patch('src.services.persistence.database_provider.get_config_service')
    def test_session_rollback_on_exception(self, mock_get_config, mock_sessionmaker, mock_create_engine):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "mysql.host": "localhost",
            "mysql.port": 3306,
            "mysql.user": "test",
            "mysql.password": "test",
            "mysql.database": "test_db"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session

        from src.services.persistence import DatabaseProvider
        DatabaseProvider._instances = {}

        provider = DatabaseProvider()

        with pytest.raises(ValueError):
            with provider.session() as session:
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestHistoryResponse:
    def test_from_orm(self):
        from src.objects.responses.history_response import HistoryResponse

        mock_history = MagicMock()
        mock_history.id = 1
        mock_history.request_id = "test-123"
        mock_history.prompt = "What is 2+2?"
        mock_history.target_model = "ChatGPT"
        mock_history.judge_model = "qwen2.5:latest"
        mock_history.inference_response = "4"
        mock_history.inference_latency_ms = 100.0
        mock_history.inference_tokens = 10
        mock_history.judge_score = 0.95
        mock_history.judge_reasoning = "Correct answer"
        mock_history.judge_categories = {"accuracy": True}
        mock_history.judge_latency_ms = 50.0
        mock_history.status = "Completed"
        mock_history.error_message = None
        mock_history.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_history.completed_at = datetime(2024, 1, 1, 12, 0, 1)

        response = HistoryResponse.from_orm(mock_history)

        assert response.id == 1
        assert response.request_id == "test-123"
        assert response.prompt == "What is 2+2?"
        assert response.target_model == "ChatGPT"
        assert response.judge_model == "qwen2.5:latest"
        assert response.inference_response == "4"
        assert response.judge_score == 0.95
        assert response.status == "Completed"
        assert response.created_at == "2024-01-01T12:00:00"
        assert response.completed_at == "2024-01-01T12:00:01"


class TestHistoryCreateRequest:
    def test_create_request(self):
        from src.objects.requests.history_request import HistoryCreateRequest

        request = HistoryCreateRequest(
            request_id="test-123",
            prompt="What is 2+2?",
            target_model="ChatGPT",
            judge_model="qwen2.5:latest",
            status="Completed"
        )

        assert request.request_id == "test-123"
        assert request.prompt == "What is 2+2?"
        assert request.target_model == "ChatGPT"
        assert request.judge_model == "qwen2.5:latest"
        assert request.status == "Completed"

    def test_optional_fields(self):
        from src.objects.requests.history_request import HistoryCreateRequest

        request = HistoryCreateRequest(
            request_id="test-123",
            prompt="What is 2+2?",
            target_model="ChatGPT",
            judge_model="qwen2.5:latest",
            status="Completed",
            inference_response="4",
            judge_score=0.95
        )

        assert request.inference_response == "4"
        assert request.judge_score == 0.95
        assert request.inference_latency_ms is None
        assert request.error_message is None
