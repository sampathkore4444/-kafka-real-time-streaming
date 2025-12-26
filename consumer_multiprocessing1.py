from confluent_kafka import Consumer, TopicPartition
import multiprocessing as mp
import time

KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "my-first-topic-test"
CONSUMER_GROUP = "multiproc-ui-group"


def consume_partition(partition_id):
    consumer_conf = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,  # commit offsets so UI sees them
    }

    consumer = Consumer(consumer_conf)
    tp = TopicPartition(TOPIC_NAME, partition_id)
    consumer.assign([tp])

    count = 0
    start_time = time.time()

    try:
        while True:
            msgs = consumer.consume(num_messages=500, timeout=1.0)
            if not msgs:
                break  # no more messages
            for msg in msgs:
                if msg.error():
                    continue
                count += 1
                # process message here (avoid print for speed)
    finally:
        duration = round(time.time() - start_time, 2)
        print(
            f"Partition {partition_id} consumed {count} messages in {duration} seconds"
        )
        consumer.close()


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)  # Windows-safe

    # Detect partitions using admin client
    from confluent_kafka.admin import AdminClient

    admin = AdminClient({"bootstrap.servers": KAFKA_BROKER})
    metadata = admin.list_topics(timeout=10)
    partitions = [p.id for p in metadata.topics[TOPIC_NAME].partitions.values()]

    processes = []
    start_time = time.time()

    for p_id in partitions:
        p = mp.Process(target=consume_partition, args=(p_id,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    total_duration = round(time.time() - start_time, 2)
    print(f"\n✅ Finished consuming all partitions in {total_duration} seconds")
