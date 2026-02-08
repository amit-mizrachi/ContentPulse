from starlette.types import Scope

from src.shared.observability.constants import DEFAULT_ATTRIBUTE


class SpanAttributesFactory:
    @staticmethod
    def server():
        attributes = {
        }

        return attributes

    @staticmethod
    def client():
        attributes = {
        }

        return attributes

    @staticmethod
    def producer():
        attributes = {
        }

        return attributes

    @staticmethod
    def consumer():
        attributes = {
        }

        return attributes
