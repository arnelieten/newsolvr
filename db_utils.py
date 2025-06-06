import threading
import psycopg2
from dotenv import dotenv_values

def connect_to_db():
    config = dotenv_values(".env")

    conn = psycopg2.connect(
        host=config["DB_HOST"], port=config["DB_PORT"], database=config["DB_DATABASE"], user=config["DB_USER"], password=config["DB_PASSWORD"]
    )

    cur = conn.cursor()
    lock = threading.Lock()

    connection_dict = {
        "cur": cur,
        "conn": conn,
        "lock": lock,
    }
    return connection_dict


def run_query(cdb, query, params=None):
    cur = cdb["cur"]
    conn = cdb["conn"]
    lock = cdb["lock"]

    with lock:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        conn.commit()


def get_query(cdb, query):
    cur = cdb["cur"]
    lock = cdb["lock"]

    with lock:
        cur.execute(query)
        rows = cur.fetchall()

    return rows

def close_query (cdb):
    cur = cdb["cur"]
    conn = cdb["conn"]

    cur.close()
    conn.close()