from starlette.types import Scope

from src.utils.observability.constants import DEFAULT_ATTRIBUTE


class SpanAttributesFactory:
    @staticmethod
    def server(headers: dict, scope: Scope, norman_ids: dict):
        client = scope.get("client")
        if client is None:
            client_address = DEFAULT_ATTRIBUTE
            client_port = DEFAULT_ATTRIBUTE
        else:
            client_address, client_port = client

        server = scope.get("server")
        if server is None:
            server_address = DEFAULT_ATTRIBUTE
            server_port = DEFAULT_ATTRIBUTE
        else:
            server_address, server_port = server

        content_length = 0
        content_length_string = headers.get("content-length")
        if content_length_string is not None:
            content_length = int(content_length_string)

        attributes = {
            "client.address": client_address,
            "client.port": client_port,
            "http.request.body.size": content_length,
            "http.request.header.content-type": headers.get("content-type", DEFAULT_ATTRIBUTE),
            "http.request.method": scope.get("method", DEFAULT_ATTRIBUTE),
            "network.protocol.version": scope.get("http_version", DEFAULT_ATTRIBUTE),
            "norman.account.id": norman_ids.get("account_id", DEFAULT_ATTRIBUTE),
            "norman.invocation.id":norman_ids.get("invocation_id", DEFAULT_ATTRIBUTE),
            "norman.model.id":norman_ids.get("model_id", DEFAULT_ATTRIBUTE),
            "server.address": server_address,
            "server.port": server_port,
            "url.scheme": scope.get("scheme", DEFAULT_ATTRIBUTE),
            "url.path": scope.get("path", DEFAULT_ATTRIBUTE)
        }

        return attributes

    @staticmethod
    def client(target_system: str, norman_client: str, target_service: str, target_method: str):
        attributes = {
            "norman.client": norman_client,
            "rpc.system": target_system,
            "rpc.service": target_service,
            "rpc.method": target_method
        }

        return attributes

    @staticmethod
    def producer(topic_name: str):
        attributes = {
            "messaging.destination.kind": "topic",
            "messaging.destination.name": topic_name,
            "messaging.operation": "publish",
            "messaging.system": "sns"
        }

        return attributes

    @staticmethod
    def consumer(topic_name: str, message_id: str, message_contents: dict):
        attributes = {
            "messaging.destination.kind": "queue",
            "messaging.destination.name": topic_name,
            "messaging.message.id": message_id,
            "norman.account.id": message_contents.get("account_id", DEFAULT_ATTRIBUTE),
            "norman.model.id": message_contents.get("model_id", DEFAULT_ATTRIBUTE),
            "norman.invocation.id": message_contents.get("invocation_id", DEFAULT_ATTRIBUTE),
            "messaging.operation.name": "receive",
            "messaging.system": "sqs"
        }

        return attributes

    @staticmethod
    def socket(server_socket: dict):
        attributes = {
            "client": server_socket.get("client_socket", DEFAULT_ATTRIBUTE),
            "network.buffer.size": server_socket.get("buffer_size", DEFAULT_ATTRIBUTE),
            "network.transport": "tcp",
            "norman.account.id":server_socket.get("account_id", DEFAULT_ATTRIBUTE),
            "norman.entity.id": server_socket.get("entity_id", DEFAULT_ATTRIBUTE),
            "server.address":server_socket.get("host", DEFAULT_ATTRIBUTE),
            "server.port": server_socket.get("port", DEFAULT_ATTRIBUTE)
        }

        return attributes

    @staticmethod
    def lambda_runtime(context, invocation_dict: dict):
        attributes = {
            "faas.aws.invocation.id": context.aws_request_id,
            "faas.aws.log.group": context.log_group_name,
            "faas.aws.resource.arn": context.invoked_function_arn,
            "faas.max_memory": context.memory_limit_in_mb,
            "faas.name": context.function_name,
            "faas.version": context.function_version,
            "norman.account.id": invocation_dict.get("account.id", DEFAULT_ATTRIBUTE),
            "norman.model.id": invocation_dict.get("model.id", DEFAULT_ATTRIBUTE),
            "norman.invocation.id": invocation_dict.get("id", DEFAULT_ATTRIBUTE)
        }

        return attributes
