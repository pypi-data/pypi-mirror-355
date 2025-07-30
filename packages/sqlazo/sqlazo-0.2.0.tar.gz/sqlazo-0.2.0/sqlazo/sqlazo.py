# v0.2.0
"""SQLazo for managing SQLITE databases

Allows you to access methods that perform transactions with the database of your choice, as long as it is a SQLITE database.

@author Tutos Rive

Version history:
- `0.2.0`: A new method was added to correctly check whether a table exists or not, and the code was modified to try to be
	compatible with older versions of Python and:
		- `Fix`: issue #1 (https://github.com/Dev2Forge/sqlazo/issues/1)
- `0.1.5`: Updated dependencies and links
- `0.1.4`: Updated dependencies and links
- `0.1.3`: Updated dependency versions
- `0.1.2`: Updated dependency versions
- `0.1.1`: Added dependency handling in the build file (.toml)
- `0.1.0`: Initial release
"""

import sqlite3 as sql
from typing import Optional, Union
from chromologger import Logger

__version__ = "0.2.0"
__author__ = "Tutos Rive"
__license__ = "MIT"
__email__ = "support@dev2forge.software"
__website__ = "https://docs.dev2forge.software/sqlazo/"

# Log Writer
log = Logger()

class Database:
	"""Manage SQLITE database"""
	def __init__(self, name:str, check_thread:bool = False) -> None:
		# Database name
		self.name:str = name
		# Check "Multi Thread"
		self.check:bool = check_thread
		# Connection to the database
		self.conn:sql.Connection = self.__connect()
		# Cursor
		self.cur:sql.Cursor = self.__cursor()

	def __connect(self) -> Union[sql.Connection, int]:
		"""Create connection to the database

		Returns:
			`sql.Connection | int`:
				`sql.Cursor`: Success
				`int`: `-1`, Error
		"""
		try: return sql.connect(self.name, check_same_thread=self.check)
		except sql.Error as e: log.log_e(e); return -1

	def __cursor(self) -> Union[sql.Cursor, int]:
		"""Add a cursor to the connection

		Returns:
			`sql.Cursor | int`:
				`sql.Cursor`: Success
				`int`: `-1`, Error
		"""
		try: return self.conn.cursor()
		except sql.Error as e: log.log_e(e); return -1

	def create_table(self, table_name:str, cols:list) -> bool:
		"""Create table in database

		Args:
			`table_name:str`: Name of the table you want to create
			`cols:list`: Columns that are added to the table

		Returns:
			`bool`:
				`False`: Errors
				`True`: Success
		"""
		tp:type = type(cols)
		if tp == list:
			try:
				cols:str = ', '.join(cols)
				self.cur.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({cols})')

				# Success query
				return True
			except sql.Error as error: log.log_e(error); return False
		else: log.log(f'Received {tp} as cols attribute, should be of type List'); return False

	def insert_data(self, data:list, cols:list, table_name:str) -> bool:
		"""Insert data in a specific table

			Args:
			    `data:list`: Data to insert into the table
			    `cols:list`: Columns in which the values will be inserted
			    `table_name:str`: Table name in which the values will be inserted

			Returns:
			    `bool`: `True` success, `False` error
			"""
		if not self.table_exists(table_name): log.log(f'Table {table_name} does not exist'); return False

		try:
			# Try to avoid SQLInjection
			sign:str = ', '.join(['?' for _ in cols])

			try:
				# Format query
				query:str = f'INSERT INTO {table_name} ({", ".join(cols)}) VALUES ({sign})'

				# Query execute
				self.cur.execute(query, data)

				# Commit changes
				self.__commit(); return True
			except sql.Error as error: log.log_e(error); return False
		except TypeError as e: log.log_e(e); return False

	def get_data_all(self, table_name:str) -> Optional[sql.Cursor]:
		"""Get all data from a specific table

		Args:
			`table_name:str`: Name of table

		Returns:
			`sql.Cursor` | `None`: `sql.Cursor` success, `None` error
		"""
		# First check if the table exists
		if not self.table_exists(table_name): log.log(f'Table {table_name} does not exist'); return None

		try: return self.cur.execute(f'SELECT * FROM {table_name}')
		except sql.Error as e: log.log_e(e)

	def table_exists(self, table_name:str) -> bool:
		"""Check if exists a table into the database

		Args:
			`table_name:str`: The table name to check if exists
		"""
		__return: bool = False
		if self.cur.execute(f'PRAGMA table_info({table_name})').fetchone() is not None: __return = True
		return __return

	def get_data_where(self, table_name:str, condition:str, *args:str) -> Optional[sql.Cursor]:
		"""Select data with a "where" condition

		Args:
			`table_name:str`: Name of table to get data
			`condition:str`: Where is the condition to get the data

		Returns:
			sql.Cursor | None: The cursor assigned to query
		"""
		if not self.table_exists(table_name): log.log(f'Table {table_name} does not exist'); return None
		if condition.strip() == '': log.log('Missing condition'); return None
		args = ", ".join(args) if len(args) > 0 else '*'

		try: return self.cur.execute(f'SELECT {args} FROM {table_name} WHERE {condition}')
		except sql.Error as error: log.log_e(error)

	def delete_data(self, table:str, condition:str) -> bool:
		"""Delete data from table whit a where condition

		Args:
			`table:str`: Nombre de la tabla
			`condition:str`: Condition to delete a data (`WHERE`)

		Returns:
			`bool`: `True` success, `False` error
		"""
		if not self.table_exists(table): log.log(f'Table {table} does not exist'); return False
		if condition.strip() != '':
			try:
				query = self.cur.execute(f'DELETE FROM {table} WHERE {condition}')
				print(query)
				self.__commit(); return True
			except sql.Error as error: log.log_e(error); return False
		else:
			log.log('No valid condition was added (where)')
			return False

	def __commit(self) -> bool:
		"""Commit changes to database

			Returns:
				`bool`: `True` When commit was success, `False` when error
		"""
		try: self.conn.commit(); return True
		except sql.Error as e: log.log_e(e); return False

	def close(self) -> bool:
		"""Close database connection

		Returns:
			`bool`: `True` Database was closed, `False` when error
		"""
		try: self.conn.close(); return True
		except sql.Error as e: log.log_e(e); return False