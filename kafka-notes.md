# Kafka Docker CLI Cheatsheet for Windows

## 📦 **Container Management**

| Command | Description |
|---------|------------|
| `docker exec -it kafka bash` | Open bash shell inside Kafka container |
| `docker exec -it zookeeper bash` | Open bash shell inside Zookeeper container |
| `docker logs -f kafka` | Follow Kafka logs |
| `docker-compose up -d` | Start Kafka stack in background |

## 🚀 **Basic Kafka Operations**

### **1. Topic Management**

#### From **Inside Container** (use `kafka:9092`):
```bash
# Create topic
kafka-topics --create --topic test-topic --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1

# List topics
kafka-topics --list --bootstrap-server kafka:9092

# Describe topic
kafka-topics --describe --topic test-topic --bootstrap-server kafka:9092

# Delete topic
kafka-topics --delete --topic test-topic --bootstrap-server kafka:9092
```

#### From **Windows Host** (use `localhost:9092`):
```cmd
# Create topic
kafka-topics --create --topic test-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# List topics
kafka-topics --list --bootstrap-server localhost:9092
```

### **2. Produce Messages**

#### Simple producer:
```bash
# Inside container
kafka-console-producer --topic test-topic --bootstrap-server kafka:9092

# From Windows
kafka-console-producer --topic test-topic --bootstrap-server localhost:9092
```
**Type messages and press Enter:**
```
Hello Kafka
Message 2
Message 3
Ctrl+C to exit
```

#### Producer with keys:
```bash
kafka-console-producer --topic test-topic --bootstrap-server kafka:9092 \
  --property "parse.key=true" \
  --property "key.separator=:"
```
**Format:** `key:message`
```
user1:Hello from user1
user2:Message from user2
```

### **3. Consume Messages**

#### Consume from beginning:
```bash
# Inside container
kafka-console-consumer --topic test-topic --from-beginning --bootstrap-server kafka:9092

# With keys
kafka-console-consumer --topic test-topic --from-beginning --bootstrap-server kafka:9092 \
  --property print.key=true \
  --property key.separator=":"
```

#### Consume new messages only:
```bash
kafka-console-consumer --topic test-topic --bootstrap-server kafka:9092
```

#### Consumer group:
```bash
# With consumer group
kafka-console-consumer --topic test-topic --bootstrap-server kafka:9092 \
  --group my-consumer-group

# List consumer groups
kafka-consumer-groups --list --bootstrap-server kafka:9092

# Describe group
kafka-consumer-groups --describe --group my-consumer-group --bootstrap-server kafka:9092
```

## 🔧 **Advanced Operations**

### **Partition Management**
```bash
# Increase partitions
kafka-topics --alter --topic test-topic --partitions 5 --bootstrap-server kafka:9092

# Create compacted topic (for key-based retention)
kafka-topics --create --topic compact-topic --bootstrap-server kafka:9092 \
  --partitions 1 --replication-factor 1 \
  --config cleanup.policy=compact \
  --config delete.retention.ms=100 \
  --config segment.ms=100 \
  --config min.cleanable.dirty.ratio=0.01
```

### **Check Configuration**
```bash
# Check broker configuration
cat /etc/kafka/server.properties | grep advertised.listeners

# Check broker version
kafka-broker-api-versions --bootstrap-server kafka:9092
```

### **Performance Testing**
```bash
# Producer performance test
kafka-producer-perf-test --topic perf-test --num-records 1000 \
  --record-size 1000 --throughput 100 \
  --producer-props bootstrap.servers=kafka:9092

# Consumer performance test
kafka-consumer-perf-test --topic perf-test --messages 1000 \
  --bootstrap-server kafka:9092
```

## 🖥️ **Kafka UI (Web Interface)**

| URL | Purpose |
|-----|---------|
| `http://localhost:8080` | Kafka UI Dashboard |
| `http://localhost:8080/clusters` | View clusters |
| `http://localhost:8080/topics` | Browse topics & messages |

**In Kafka-UI you can:**
- Browse topics and partitions
- View messages in real-time
- Produce test messages
- Monitor consumer groups
- Check broker health

## ⚠️ **Troubleshooting**

### **Common Issues & Solutions:**

1. **Connection refused on localhost:9092**
   ```cmd
   # Check if port is mapped
   docker ps
   # Should show: 0.0.0.0:9092->9092/tcp
   ```

2. **Topic not created**
   ```bash
   # Check if auto.create.topics.enabled=true
   docker exec kafka cat /etc/kafka/server.properties | grep auto.create
   ```

3. **Consumer not receiving messages**
   ```bash
   # Check consumer group offsets
   kafka-consumer-groups --describe --group my-group --bootstrap-server kafka:9092
   ```

4. **Produce from file**
   ```bash
   # Create messages file
   echo -e "message1\nmessage2\nmessage3" > messages.txt
   
   # Produce from file
   kafka-console-producer --topic test-topic --bootstrap-server kafka:9092 < messages.txt
   ```

## 📝 **Quick Test Script**

Save as `test-kafka.bat` on Windows:
```batch
@echo off
echo 1. Creating topic...
kafka-topics --create --topic quick-test --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

echo 2. Producing messages...
echo Hello Kafka | kafka-console-producer --topic quick-test --bootstrap-server localhost:9092
echo Test Message | kafka-console-producer --topic quick-test --bootstrap-server localhost:9092

echo 3. Consuming messages...
timeout /t 2 /nobreak >nul
kafka-console-consumer --topic quick-test --from-beginning --bootstrap-server localhost:9092 --timeout-ms 5000

echo 4. Check Kafka-UI at http://localhost:8080
```

## 🔗 **Useful Docker Commands**

```cmd
# Restart services
docker-compose restart kafka

# View all logs
docker-compose logs

# Recreate and start fresh
docker-compose down -v
docker-compose up -d

# Check service health
docker-compose ps
```

---

## ✅ **Quick Verification Steps**

1. **Check containers are running:**
   ```cmd
   docker ps
   ```
   Should show: `kafka`, `zookeeper`, `kafka-ui`

2. **Test from Windows:**
   ```cmd
   kafka-topics --list --bootstrap-server localhost:9092
   ```

3. **Test from container:**
   ```cmd
   docker exec -it kafka kafka-topics --list --bootstrap-server kafka:9092
   ```

4. **Verify in Web UI:**
   Open `http://localhost:8080` in browser

---

**Remember:**
- Inside Docker containers → use `kafka:9092`
- From Windows host → use `localhost:9092`
- Kafka-UI updates in real-time
- Messages persist until retention period (default 7 days)

This cheatsheet covers 95% of daily Kafka operations in Docker! 🚀