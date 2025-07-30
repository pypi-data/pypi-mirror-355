from abc import ABC, abstractmethod

from playhouse.pool import PooledMySQLDatabase
from pymysql.connections import Connection


class BaseDatabaseManager(ABC):

    def __init__(self):
        ...

    @abstractmethod
    def get_database(self) -> PooledMySQLDatabase:
        ...

    @abstractmethod
    def open_connection(self) -> Connection:
        ...

    def close_connection(self, connection: Connection) -> bool:
        ...

    @abstractmethod
    def connection_context(self):
        ...

    @abstractmethod
    def database_context(self):
        ...
