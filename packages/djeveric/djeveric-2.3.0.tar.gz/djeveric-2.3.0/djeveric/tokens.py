from abc import ABCMeta, abstractmethod
from typing import Iterable

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class ProxyTokenGenerator(PasswordResetTokenGenerator):
    def __init__(self, proxy):
        super().__init__()
        self.proxy = proxy

    def _make_hash_value(self, instance, timestamp):
        data = list(self.proxy.get_token_data())
        assert all(
            isinstance(item, str) for item in data
        ), f"Iterable returned by {instance.__class__.__name__}.get_confirmation_token_data must contain strings."
        serialized_data = "".join(data)
        return f"{serialized_data}{timestamp}"


class TokenGeneratorProxy(metaclass=ABCMeta):
    token_generator_class = ProxyTokenGenerator

    def __init__(self, instance):
        self.instance = instance
        self.token_generator = self.token_generator_class(proxy=self)

    def check_token(self, token: str):
        return self.token_generator.check_token(self.instance, token)

    def make_token(self):
        return self.token_generator.make_token(self.instance)

    @abstractmethod
    def get_token_data(self) -> Iterable[str]:
        raise NotImplementedError(f"Implement {self.__class__.name}.get_token_data()")


class ConfirmationTokenGeneratorProxy(TokenGeneratorProxy):
    def get_token_data(self) -> Iterable[str]:
        return self.instance.get_confirmation_token_data()
