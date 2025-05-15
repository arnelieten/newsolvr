import json
import threading
import psycopg2


def connect_to_db():
    print("Connecting to db... ", end="")


    with open("connection_details.json", "r") as f:
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

    print("Done!")

    return connection_dict


def run_query(cdb, query):
    cur = cdb["cur"]
    conn = cdb["conn"]
    lock = cdb["lock"]

    with lock:
        cur.execute(query)
        conn.commit()

    return


def get_query(cdb, query):
    cur = cdb["cur"]
    lock = cdb["lock"]

    with lock:
        cur.execute(query)
        rows = cur.fetchall()

    return rows