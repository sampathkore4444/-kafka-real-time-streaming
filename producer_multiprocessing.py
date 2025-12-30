from kafka import KafkaProducer
import multiprocessing as mp
import os
import time
import uuid
import random
import json


# Kafka configuration
KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "my-first-topic-test"
TOTAL_MESSAGES = 10000000
NUM_PROCESSES = min(8, os.cpu_count())  # cap processes

MERCHANTS = ["M001", "M002", "M003", "M004", "M005"]


def create_txn(i):
    return {
        "txn_id": f"TXN-{uuid.uuid4().hex[:12]}",
        "merchant_id": random.choice(MERCHANTS),
        "account_id": f"ACC{random.randint(1000, 9999)}",
        "amount": round(random.uniform(5, 5000), 2),
        "currency": "USD",
        "event_time": int(time.time()),
    }


def produce_messages(start, end, process_id):
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        # value_serializer=lambda v: v.encode("utf-8"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        linger_ms=5,  # batch for a few ms
        batch_size=64 * 1024,  # 64KB batch
        acks=1,  # faster than acks=all
    )

    for i in range(start, end):
        producer.send(
            TOPIC_NAME,
            #             value=f""" In the soft morning light filtering through the pagoda grounds of Promaoy, dozens of families huddled beneath makeshift tents, clutching bags packed in panic. They are exhausted, cold and frightened—but for many of them, this was not the first time they had fled gunfire.
            # They are survivors of the Khmer Rouge era who, five decades later, have once again become war refugees.
            # These residents of Ekareach village in Thmar Da commune along the Cambodia-Thailand border, were evacuated by the authorities after Thai troops fired on Cambodian positions on December 7 and 8 in Preah Vihear, Oddar Meanchey, Banteay Meanchey and Battambang provinces. At dawn on December 9, Thai soldiers launched an attack on Military Post No 5 in Thmar Da commune and continued firing indiscriminately—including into areas where civilians were gathered.
            # By nightfall, the villagers were fleeing in lorries, on motorbikes and even on foot, trying to outrun the fear they thought they had buried long ago.
            # Among them is Li Mao, 58, a soft-spoken woman who sells dried fish paste for a living. She survived the Khmer Rouge as a child. Now she is trying to survive yet another war.
            # Sitting on a straw mat near the pagoda entrance, Mao wraps her scarf tightly around her shoulders against the December cold. Her voice quivered as she recounted her life—a story shaped by conflict from the very beginning.
            # Born in Banteay Meanchey, she was forced by the Khmer Rouge between 1975 and 1979 into a child-labour unit. She tended cattle, mixed fertilisers and dug canals in Komping Puoy, Battambang—backbreaking work for a girl who never had the chance to study.
            # Peace never lasted long. In 1997, her husband, a border soldier, was transferred to Thmar Da. He soon stepped on a landmine and lost a leg. In 2000, Mao walked three nights from Promaoy to reach him, settling in a remote military village surrounded by forest and danger. {i}""",
            value=create_txn(i),
        )

    producer.flush()
    producer.close()
    print(f"Process {process_id} sent messages {start} to {end-1}")


if __name__ == "__main__":
    start_time = time.time()

    chunk_size = TOTAL_MESSAGES // NUM_PROCESSES
    processes = []

    for i in range(NUM_PROCESSES):
        start = i * chunk_size + 1
        end = start + chunk_size

        if i == NUM_PROCESSES - 1:
            end = TOTAL_MESSAGES + 1  # last process sends remainder

        p = mp.Process(target=produce_messages, args=(start, end, i))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print(
        f"\n✅ Sent {TOTAL_MESSAGES} messages in "
        f"{round(time.time() - start_time, 2)} seconds"
    )
