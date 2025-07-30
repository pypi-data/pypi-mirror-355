from contextlib import contextmanager

import pymysql.err
from loguru import logger
from playhouse.pool import PooledMySQLDatabase
from pymysql.connections import Connection

from flashboot_odbc.database.base import BaseDatabaseManager
from flashboot_odbc.types import MySQLConfig


class MySQLDatabaseManager(BaseDatabaseManager):

	def __init__(self, mysql_config: MySQLConfig):
		super().__init__()
		self.mysql_config = mysql_config
		self.database: PooledMySQLDatabase = PooledMySQLDatabase(
			database=self.mysql_config.database,
			user=self.mysql_config.user,
			password=self.mysql_config.password,
			host=self.mysql_config.host,
			port=self.mysql_config.port,
			charset=self.mysql_config.charset,
			max_connections=self.mysql_config.max_connections,
			stale_timeout=self.mysql_config.stale_timeout
		)

	def get_database(self) -> PooledMySQLDatabase:
		return self.database

	def open_connection(self) -> Connection:
		return self.get_database().connection()

	def close_connection(self, connection: Connection) -> bool:
		try:
			connection.close()
			return True
		except pymysql.err.Error as e:
			logger.warning(f"Error closing connection: {e}")
			return False
		except Exception as e:
			logger.error(f"Unexpected error closing/releasing connection: {e}")
			return False

	@contextmanager
	def connection_context(self):
		db_instance = self.get_database()
		db_instance.connect(reuse_if_open=True)
		raw_connection = db_instance.connection()
		try:
			yield raw_connection
		finally:
			db_instance.close()

	@contextmanager
	def database_context(self):
		return self.get_database().connection_context()
