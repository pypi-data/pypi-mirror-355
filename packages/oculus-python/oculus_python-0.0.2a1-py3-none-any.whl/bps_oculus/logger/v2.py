import sqlite3
from bps_oculus import core
from pathlib import Path
from enum import IntEnum
"""
The Oculus V2 log is a SQLite Database.

The file consists of 6 tables

metadata
dataSources
dataSourceProperties
data
resources
bookmarks
"""

class dataSourceProperties(IntEnum):
    User = -1
    Oculus = 0
    SeaTrac = 1
    StarFish = 2


def table_fetch_all(table_name: str, cursor: sqlite3.Cursor):
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    for row in rows:
        print(row)


def table_fetch_iter(table_name: str, cursor: sqlite3.Cursor) -> tuple:
    cursor.execute(f"SELECT * FROM {table_name};")
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        yield row


class V2LogParser:
    def __init__(self, logfile: Path):
        self._connection = sqlite3.connect(logfile)
        self._cursor = self._connection.cursor()
        self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        self._table_names = self._cursor.fetchall()
        self._cursor.execute(f"SELECT * FROM metadata;")
        self._metadata = {key: val for key, val in self._cursor.fetchall()}

    @property
    def metadata(self):
        return self._metadata

    @property
    def data(self):
        self._cursor.execute("SELECT * FROM data;")
        return self._cursor

    def close(self):
        self._connection.close()

    def __del__(self):
        self.close()



def main():
    try:
        connection = sqlite3.connect("./data/V2/haul_9_884_exported.oculus")
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table_name in tables:
            print(table_name[0])
        for item in table_fetch_iter("data", cursor):
            ping_result, polar_image, clean_msg = core.unpack_data_entry(item[-1])
    finally:
        connection.close()


if __name__ == "__main__":
    main()
