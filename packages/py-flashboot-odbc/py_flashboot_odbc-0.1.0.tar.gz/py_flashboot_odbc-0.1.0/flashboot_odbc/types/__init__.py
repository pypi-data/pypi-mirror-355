from typing import Optional

from flashboot_core.env import property_bind


@property_bind("flashboot.datasource.mysql")
class MySQLConfig:
	host: str
	port: int
	user: str
	password: str
	database: str
	charset: str
	max_connections: Optional[int] = 10
	stale_timeout: Optional[int] = 300

	def __init__(self):
		pass
