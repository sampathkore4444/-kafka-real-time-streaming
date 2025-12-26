from kafka import KafkaConsumer, TopicPartition
import multiprocessing as mp
import time

KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "my-first-topic-test"
CONSUMER_GROUP = "multiproc-ui-group"
NUM_PROCESSES = 4  # Adjust based on CPU cores and partitions


def consume_partition(partition_id):
    """
    Each process consumes a partition using the same consumer group.
    """
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BROKER,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,  # ✅ commits offsets so UI sees messages
        max_poll_records=500,  # batch size
        consumer_timeout_ms=5000,  # exit if no messages
    )

    # Assign specific partition manually (optional)
    tp = TopicPartition(TOPIC_NAME, partition_id)
    consumer.assign([tp])

    count = 0
    start_time = time.time()

    for msg in consumer:
        count += 1
        # process messages here (avoid printing per message for speed)

    duration = round(time.time() - start_time, 2)
    print(f"Partition {partition_id} consumed {count} messages in {duration} seconds")
    consumer.close()


if __name__ == "__main__":
    # Detect all partitions
    temp_consumer = KafkaConsumer(bootstrap_servers=KAFKA_BROKER)
    partitions = temp_consumer.partitions_for_topic(TOPIC_NAME)
    partitions = list(partitions) if partitions else [0]
    temp_consumer.close()

    processes = []
    start_time = time.time()

    # Start one process per partition
    for partition_id in partitions:
        p = mp.Process(target=consume_partition, args=(partition_id,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    total_duration = round(time.time() - start_time, 2)
    print(f"\n✅ Finished consuming all partitions in {total_duration} seconds")
