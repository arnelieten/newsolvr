import json
import threading
import psycopg2


def connect_to_db():
    with open("db_credentials.json", "r") as f:
        connection_details = json.load(f)

    cdb = connection_details

    conn = psycopg2.connect(
        host=cdb["host"], port=cdb["port"], database=cdb["database"], user=cdb["user"], password=cdb["password"]
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