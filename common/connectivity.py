import logging
import os

from google.cloud import bigquery, storage
from sadsconnectivity.sql_server import create_psc_iam_engine, create_read_engine
from sqlalchemy import Engine, create_engine

try:
    if "K_SERVICE" in os.environ:
        sql_engine: Engine = create_psc_iam_engine()
    else:
        sql_engine: Engine = create_read_engine()

except Exception as _e:
    logging.warning(f"Could not connect to the database: {_e} - using a fake in-memory database instead.")
    sql_engine = create_engine("sqlite:///:memory:")

bq_client = bigquery.Client()
storage_client = storage.Client()
