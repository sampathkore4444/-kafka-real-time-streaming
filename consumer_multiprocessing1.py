from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.admin import AdminClient
import multiprocessing as mp
import json
import time
from collections import defaultdict
import oracledb
from datetime import datetime

# -----------------------------
# Kafka / Oracle config
# -----------------------------
KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "my-first-topic-test"
CONSUMER_GROUP = "multiproc-aggregation-group"

WINDOW_SIZE = 15  # seconds
ALLOWED_LATENESS = 30  # seconds

ORACLE_USER = "SYSTEM"
ORACLE_PASSWORD = "LOMA@1234"
ORACLE_DSN = "localhost/XE"


# -----------------------------
# Load offset from Oracle
# -----------------------------
def load_offset_from_oracle(partition_id):
    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT offset
        FROM kafka_offsets
        WHERE topic = :t AND partition_id = :p
        """,
        {"t": TOPIC_NAME, "p": partition_id},
    )

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    return row[0] if row else None


# -----------------------------
# Persist window + offset atomically
# -----------------------------
def persist_window_and_offset(
    partition_id, window_start, window_end, metrics, last_offset
):
    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
    cursor = conn.cursor()

    try:
        ws_ts = datetime.fromtimestamp(window_start)
        we_ts = datetime.fromtimestamp(window_end)

        # 1️⃣ Aggregation
        for merchant, data in metrics.items():
            cursor.execute(
                """
                MERGE INTO merchant_agg t
                USING dual
                ON (
                    t.window_start = :ws AND
                    t.partition_id = :pid AND
                    t.merchant_id = :mid
                )
                WHEN MATCHED THEN UPDATE SET
                    txn_count = t.txn_count + :cnt,
                    total_amount = t.total_amount + :amt
                WHEN NOT MATCHED THEN INSERT
                    (window_start, window_end, partition_id, merchant_id, txn_count, total_amount)
                VALUES
                    (:ws, :we, :pid, :mid, :cnt, :amt)
                """,
                {
                    "ws": ws_ts,
                    "we": we_ts,
                    "pid": partition_id,
                    "mid": merchant,
                    "cnt": data["count"],
                    "amt": data["amount"],
                },
            )

        # 2️⃣ Offset persistence (EOS)
        cursor.execute(
            """
            MERGE INTO kafka_offsets t
            USING dual
            ON (t.topic = :t AND t.partition_id = :p)
            WHEN MATCHED THEN UPDATE SET
                offset = :o,
                updated_at = SYSTIMESTAMP
            WHEN NOT MATCHED THEN INSERT
                (topic, partition_id, offset, updated_at)
            VALUES
                (:t, :p, :o, SYSTIMESTAMP)
            """,
            {
                "t": TOPIC_NAME,
                "p": partition_id,
                "o": last_offset + 1,
            },
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# -----------------------------
# Partition consumer
# -----------------------------
def consume_partition(partition_id):
    consumer_conf = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": CONSUMER_GROUP,
        "enable.auto.commit": False,  # 🔥 Oracle controls offsets
        "auto.offset.reset": "earliest",
    }

    consumer = Consumer(consumer_conf)

    stored_offset = load_offset_from_oracle(partition_id)

    if stored_offset is not None:
        consumer.assign([TopicPartition(TOPIC_NAME, partition_id, stored_offset)])
        print(f"▶ Resuming partition {partition_id} from offset {stored_offset}")
    else:
        consumer.assign([TopicPartition(TOPIC_NAME, partition_id)])
        print(f"▶ Starting partition {partition_id} from earliest")

    # metrics[window_start][merchant]
    metrics = defaultdict(lambda: defaultdict(lambda: {"count": 0, "amount": 0.0}))

    max_event_time = 0
    last_offset = None

    print(f"🚀 Started consumer for partition {partition_id}")

    try:
        while True:
            msgs = consumer.consume(num_messages=500, timeout=1.0)

            for msg in msgs:
                if msg is None or msg.error():
                    continue

                last_offset = msg.offset()

                event = json.loads(msg.value().decode("utf-8"))

                merchant = event["merchant_id"]
                amount = float(event["amount"])
                event_time = int(event["event_time"])

                max_event_time = max(max_event_time, event_time)

                ws = event_time - (event_time % WINDOW_SIZE)
                metrics[ws][merchant]["count"] += 1
                metrics[ws][merchant]["amount"] += amount

            # 🔔 Event-time watermark
            watermark = max_event_time - ALLOWED_LATENESS

            closable_windows = [ws for ws in metrics if ws + WINDOW_SIZE <= watermark]

            for ws in closable_windows:
                we = ws + WINDOW_SIZE

                persist_window_and_offset(
                    partition_id, ws, we, metrics[ws], last_offset
                )

                del metrics[ws]

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        print(f"🛑 Consumer closed for partition {partition_id}")


# -----------------------------
# Multiprocessing main
# -----------------------------
if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    admin = AdminClient({"bootstrap.servers": KAFKA_BROKER})
    metadata = admin.list_topics(timeout=10)

    partitions = [p.id for p in metadata.topics[TOPIC_NAME].partitions.values()]
    print(f"🔍 Detected partitions: {partitions}")

    processes = []

    for p_id in partitions:
        p = mp.Process(target=consume_partition, args=(p_id,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
