import duckdb
from pathlib import Path


# A specific class to handle the connection to the DuckDB.
# This class uses a context manager, to make sure  the connection is closed after use.
class DataBase_Connection:
    def __init__(self, db_filename="jobads_data_warehouse.duckdb", read_only=True):
        self.db_path = Path(__file__).parent.parent / db_filename
        self.read_only = read_only
        self.connection = None

    def __enter__(self):
        self.connection = duckdb.connect(database=self.db_path, read_only=True)
        return self.connection
    
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()