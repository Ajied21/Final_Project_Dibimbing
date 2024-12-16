from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, year, from_unixtime
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
import os

# Menambahkan dependensi untuk koneksi ke Kafka dan PostgreSQL
os.environ["PYSPARK_SUBMIT_ARGS"] = (
    "--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2, \
                org.apache.kafka:kafka-clients:7.2.0, \
                org.postgresql:postgresql:42.6.0"
)

spark_host = "spark://spark-master:7077"

# Membuat sesi Spark
spark = SparkSession.builder \
    .appName("Consumer_data_assets") \
    .master("local[*]") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2, \
                                    org.apache.kafka:kafka-clients:7.2.0, \
                                    org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Schema untuk JSON data
schema = StructType([
    StructField("exchangeId", StringType(), True),
    StructField("name", StringType(), True),
    StructField("rank", StringType(), True),
    StructField("percentTotalVolume", StringType(), True),
    StructField("volumeUsd", StringType(), True),
    StructField("tradingPairs", StringType(), True),
    StructField("socket", StringType(), True),
    StructField("exchangeUrl", StringType(), True),
    StructField("updated", StringType(), True) 
])

# Fungsi untuk mengonversi tipe data ke tipe yang sesuai dengan PostgreSQL
def convert_to_postgres_typed_df(df):
    df = df.withColumn("exchangeId", col("exchangeId").cast("string")) \
            .withColumn("name", col("name").cast("string")) \
            .withColumn("rank", col("rank").cast("int")) \
            .withColumn("percentTotalVolume", col("percentTotalVolume").cast("double")) \
            .withColumn("volumeUsd", col("volumeUsd").cast("double")) \
            .withColumn("tradingPairs", col("tradingPairs").cast("int")) \
            .withColumn("socket", col("socket").cast("boolean")) \
            .withColumn("exchangeUrl", col("exchangeUrl").cast("string")) \
            .withColumn("updated", from_unixtime(col("updated") / 1000).cast("timestamp"))
    
    df_filtered = df.filter(year(col("updated")) == 2024)

    return df_filtered

# Fungsi untuk memproses stream Kafka dan menyimpannya ke PostgreSQL
def process_kafka_stream(topic_name):
    # Membaca data dari Kafka
    df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "broker:29092")
        .option("subscribe", topic_name)
        .option("startingOffsets", "latest")
        .load()
    )
    
    # Mengubah nilai Kafka dari binary ke string
    json_df = df.selectExpr("CAST(value AS STRING) AS json_data")
    
    # Mem-parsing JSON
    parsed_df = json_df.select(from_json(col("json_data"), schema).alias("parsed"))
    
    # Mengambil data dalam kolom 'parsed'
    final_df = parsed_df.select("parsed.*")
    
    # Konversi tipe data agar sesuai dengan tipe PostgreSQL
    postgres_df = convert_to_postgres_typed_df(final_df)
    
    # Menyimpan data ke PostgreSQL dalam bentuk batch menggunakan foreachBatch
    def write_to_postgres(batch_df, batch_id):
        batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres:5432/data_staging") \
            .option("dbtable", "exchanges") \
            .option("user", "user") \
            .option("password", "admin123") \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()

    # Menggunakan foreachBatch untuk menulis data ke PostgreSQL
    postgres_df.writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("append") \
        .trigger(processingTime="30 seconds") \
        .start() \
        .awaitTermination()

# Topik yang akan diproses
topics = ['exchanges']
for topic_name in topics:
    print(f"\nProses untuk topik: {topic_name}")
    process_kafka_stream(topic_name)