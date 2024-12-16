import json
import requests
import time
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from confluent_kafka import Producer

# Kafka Configuration
KAFKA_BROKER = 'broker:29092'

# List of API URLs and corresponding Kafka topic names
urls = [
    ("https://api.coincap.io/v2/assets", "assets"),
    ("https://api.coincap.io/v2/rates", "rates"),
    ("https://api.coincap.io/v2/exchanges", "exchanges"),
    ("https://api.coincap.io/v2/markets", "markets")
]

# Fungsi untuk mengambil data dari API
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Memastikan response statusnya 200
        json_data = response.json()
        return json_data.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return []

# Fungsi untuk mengirim data ke Kafka
def send_to_kafka(producer, topic, data):
    if data:
        for item in data:
            data_json = json.dumps(item)
            producer.produce(topic, value=data_json)
            producer.flush()
        print(f"Data sedang proses dikirim ke topik {topic}")
    else:
        print(f"Tidak ada data yang sedang di proses untuk dikirim ke topik {topic}")

# Fungsi untuk polling API secara periodik
def poll_api_to_kafka():
    producer = Producer({'bootstrap.servers': KAFKA_BROKER})
    while True:
        for url, topic in urls:
            data = fetch_data(url)
            send_to_kafka(producer, topic, data)
        time.sleep(60)  # Poll setiap 60 detik

# Spark Streaming Configuration
os.environ["PYSPARK_SUBMIT_ARGS"] = (
    "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2"
)

spark_host = "spark://spark-master:7077"

spark = SparkSession.builder \
    .appName("Procedur_data") \
    .master("local[*]") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Membaca data dari Kafka untuk semua topik yang ada
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", ",".join([topic for _, topic in urls])) \
    .load()

# Konversi kolom 'value' dari binary menjadi string
df_parsed = df.selectExpr("CAST(value AS STRING) as message")

# Misalkan Anda ingin melihat hasilnya, Anda bisa menulisnya ke output
df_parsed.writeStream \
    .format("console") \
    .trigger(processingTime="1 minutes") \
    .start()

# Jalankan polling API secara periodik
poll_api_to_kafka()  # Fungsi ini akan berjalan dalam loop utama tanpa thread

# Menunggu hingga query streaming selesai
df_parsed.awaitTermination()
