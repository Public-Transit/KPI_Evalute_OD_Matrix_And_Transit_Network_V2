# src/service_layer/unit_of_work.py
import abc
from src.adapters.repository.abstract_repository import AbstractRepository

class AbstractUnitOfWork(abc.ABC):
    repo: AbstractRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        pass

    @abc.abstractmethod
    def rollback(self):
        pass

class DummyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, repo: AbstractRepository):
        self.repo = repo
        self.committed = False

    def __enter__(self):
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
