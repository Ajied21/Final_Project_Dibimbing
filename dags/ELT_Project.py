from datetime import timedelta
from pathlib import Path
from airflow.decorators import dag
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from astronomer.providers.dbt.task_group import DbtTaskGroup, DbtRunOperator

# Fungsi DAG utama
@dag(
    description="Dhoifullah Luth Majied",
    dag_id=Path(__file__).stem,
    schedule_interval=None,
    dagrun_timeout=timedelta(minutes=60),
    start_date=days_ago(1),
    default_args={
        "owner": "Ajied(WhatsApp), Ajied(Email)",
    },
    owner_links={
        "Ajied(WhatsApp)": "https://wa.me/+6287787106077",
        "Ajied(Email)": "mailto:dhoifullah.luthmajied05@gmail.com",
    },
    tags=["Final Project Dibimbing batch 7"],
)

def ELT_Projects():

    # Task dan alur eksekusi DAG
    start_task = EmptyOperator(task_id="start_task")

    with TaskGroup(group_id='Extract') as E:
        extract_data = SparkSubmitOperator(
            application="/spark-scripts/ELT/extract_data.py",
            conn_id="spark_main",
            task_id="spark_submit_task",
            jars="/spark-scripts/jars/jars_postgresql-42.2.20.jar",
        )
        extract_data
    
    with TaskGroup(group_id='Load') as L:
        load_data = SparkSubmitOperator(
            application="/spark-scripts/ELT/load_data.py",
            conn_id="spark_main",
            task_id="spark_submit_task",
            jars="/spark-scripts/jars/jars_postgresql-42.2.20.jar",
        )
        load_data
    
    with TaskGroup(group_id='Transform') as T:
        assets = DbtRunOperator(
            task_id="assets",
            models="/dags/dbt/models/assets.sql",
            conn_id="my_dbt_connection",
        )

        rates = DbtRunOperator(
            task_id="rates",
            models="/dags/dbt/models/rates.sql",
            conn_id="my_dbt_connection",
        )

        exchanges = DbtRunOperator(
            task_id="exchanges",
            models="/dags/dbt/models/exchanges.sql",
            conn_id="my_dbt_connection",
        )

        markets = DbtRunOperator(
            task_id="markets",
            models="/dags/dbt/models/markets.sql",
            conn_id="my_dbt_connection",
        )
        assets
        rates
        exchanges
        markets

    end_task = EmptyOperator(task_id="end_task")
    
    # Definisikan alur eksekusi
    start_task >> E >> L >> T >> end_task

ELT_Projects()