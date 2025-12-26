from kafka import KafkaProducer
import time

# Kafka configuration
# KAFKA_BROKER = "localhost:9092"  # Use 'kafka:9092' if running inside Docker container
KAFKA_BROKER = "localhost:9092"  # Use 'kafka:9092' if running inside Docker container

TOPIC_NAME = "my-first-topic"

# Initialize producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: v.encode("utf-8"),  # Convert string to bytes
)

# Produce messages in a loop
for i in range(1, 10001):  # 1 to 10000
    message = f"Message {i}"
    producer.send(TOPIC_NAME, value=message)

    if i % 1000 == 0:
        print(f"Sent {i} messages...")
        producer.flush()  # Ensure messages are sent to broker

# Final flush
producer.flush()
print("All 10000 messages sent successfully!")

# Close producer
producer.close()
