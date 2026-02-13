import threading

import psycopg2

from config.config import DB_DATABASE, DB_HOST, DB_PASSWORD, DB_PORT, DB_USER


def connect_to_db():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_DATABASE, user=DB_USER, password=DB_PASSWORD
    )

    cur = conn.cursor()
    lock = threading.Lock()

    connection_dict = {
        "cur": cur,
        "conn": conn,
        "lock": lock,
    }
    return connection_dict


def run_query(db_connection, query, params=None):
    cur = db_connection["cur"]
    conn = db_connection["conn"]
    lock = db_connection["lock"]

    with lock:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        conn.commit()


def get_query(db_connection, query, params=None):
    cur = db_connection["cur"]
    lock = db_connection["lock"]

    with lock:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        rows = cur.fetchall()

    return rows


def close_db(db_connection):
    cur = db_connection["cur"]
    conn = db_connection["conn"]

    cur.close()
    conn.close()
