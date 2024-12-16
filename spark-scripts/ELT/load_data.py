import pyspark
import polars as pl
from google.cloud import bigquery
import os

# Konfigurasi Google Cloud
service_account_key = "/spark-scripts/ELT/credentials/keys.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_key

project_id = "dibimbing-de"
dataset_id = "Final_Project_Dibimbing"
table_name = "Coin_Market_Cap"

table_id = f"{project_id}.{dataset_id}.{table_name}"

# Konfigurasi untuk koneksi ke PostgreSQL
spark_host = "spark://spark-master:7077"

sparkcontext = pyspark.SparkContext.getOrCreate(conf=(
                pyspark
                .SparkConf()
                .setAppName('load_data')
                .setMaster(spark_host)
                .set("spark.jars", "/opt/bitnami/spark/jars/postgresql-42.2.18.jar")
            ))

sparkcontext.setLogLevel("WARN")

spark = pyspark.sql.SparkSession(sparkcontext.getOrCreate())

def load():
    # Konfigurasi JDBC untuk PostgreSQL
    jdbc_url = "jdbc:postgresql://postgres:5432/data_staging"
    properties = {
        "user": "user",
        "password": "admin123",
        "driver": "org.postgresql.Driver",
        "stringtype": "unspecified"
    }

    # Query SQL untuk ekstraksi data
    query = """
           SELECT DISTINCT
                a.id AS asset_id, 
                a.rank AS asset_rank, 
                a.symbol AS asset_symbol, 
                a.name AS asset_name, 
                a.supply, 
                a."marketCapUsd", 
                a."volumeUsd24Hr", 
                a."priceUsd", 
                a."changePercent24Hr", 
                a."vwap24Hr", 
                a.explorer,
                r.id AS rates_id,  
                r.symbol AS rates_symbol,
                r."currencySymbol" AS rates_currency_Symbol,
                r.type AS rates_type, 
                r."rateUsd", 
                e."exchangeId" AS exchange_id,
                e."name" AS exchange_name,
                e."rank" AS exchange_rank,
                CASE 
                    WHEN e."socket" = false THEN 'FALSE'
                    WHEN e."socket" = true THEN 'TRUE'
                END AS socket,
                e."percentTotalVolume", 
                e."volumeUsd", 
                e."tradingPairs",
                e."exchangeUrl" AS exchange_url, 
                m."quoteSymbol",
                m."quoteId",
                m."priceQuote",
                m."percentExchangeVolume",
                m."tradesCount24Hr",
                TO_CHAR(m.updated, 'YYYY-MM-DD HH24:MI:SS') AS updated
                FROM
                    public.markets m
                INNER JOIN
                    public.assets a ON m."baseId" = a.id
                INNER JOIN
                    public.rates r ON m."quoteId" = r.id
                INNER JOIN
                    public.exchanges e ON m."exchangeId" = e."exchangeId"
                WHERE e.updated IS NOT NULL
                LIMIT 1000000
        """
    # Bungkus query dengan alias
    query = f"({query}) AS subquery"

    # Ekstraksi data dari PostgreSQL menggunakan JDBC
    data = spark.read.jdbc(
        jdbc_url,
        query,
        properties=properties
    )

    data.show(5)

    # Konversi Spark DataFrame ke Arrow DataFrame 
    # karena Polars tidak memiliki dukungan bawaan untuk langsung membaca data dari PySpark DataFrame
    arrow_df = data._sc._jvm.org.apache.spark.sql.execution.arrow.ArrowUtils.toArrowTable(data._jdf)

    # Konversi Arrow DataFrame ke Polars DataFrame
    df = pl.from_arrow(arrow_df)

    # Simpan Polars DataFrame sebagai file Parquet
    parquet_file = "Coins_Markets_Caps.parquet"
    df.write_parquet(parquet_file)

    # Inisialisasi client BigQuery
    client = bigquery.Client()


    # Konfigurasi job untuk mengunggah data
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,  # Ubah ke Parquet
        autodetect=True                               # Deteksi otomatis schema
    )

    # Muat file Parquet ke BigQuery
    try:
        with open(parquet_file, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        job.result()  # Tunggu hingga pekerjaan selesai
        print("Data berhasil diupload ke BigQuery!")
    except Exception as e:
        print(f"Terjadi error saat menulis ke BigQuery: {e}")
    finally:
        # Hapus file Parquet setelah selesai
        if os.path.exists(parquet_file):
            os.remove(parquet_file)

if __name__ == "__main__":
    
    load()  