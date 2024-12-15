import pyspark

# Konfigurasi untuk koneksi ke PostgreSQL
spark_host = "spark://spark-master:7077"

sparkcontext = pyspark.SparkContext.getOrCreate(conf=(
                pyspark
                .SparkConf()
                .setAppName('extract_data')
                .setMaster(spark_host)
                .set("spark.jars", "/opt/bitnami/spark/jars/postgresql-42.2.18.jar")
            ))

sparkcontext.setLogLevel("WARN")

spark = pyspark.sql.SparkSession(sparkcontext.getOrCreate())

def extract():
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
                m.updated AS updated
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
    
    return data

if __name__ == "__main__":

    extract()