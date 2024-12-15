include .env

help:
	@echo "## docker-build			- Build Docker Images (amd64) including its inter-container network."
	@echo "## spark					- Run a Spark cluster, rebuild the postgres container, then create the destination tables "
	@echo "## kafka					- Spinup kafka cluster"
	@echo "## airflow				- Build to orchestrator"
	@echo "## postgres				- Run database of relationship"
	@echo "## grafana				- Monitoring real-time data"
	@echo "## dbt					- Run modeling and transform data"
	@echo "## clean					- Cleanup all running containers related to the challenge."

docker-build:
	@echo '__________________________________________________________'
	@echo 'Building Docker Images ...'
	@echo '__________________________________________________________'
	@docker network inspect Dibimbing-Network >/nul 2>&1 || docker network create Dibimbing-Network
	@echo '__________________________________________________________'
	@docker build -t Dibimbing/airflow -f ./docker/Dockerfile.airflow .
	@echo '__________________________________________________________'
	@docker build -t Dibimbing/spark -f ./docker/Dockerfile.spark .
	@echo '__________________________________________________________'
# @docker build -t Dibimbing/dbt -f ./docker/Dockerfile.dbt .
	@echo '==========================================================='

kafka:
	@echo '__________________________________________________________'
	@echo 'Creating Kafka Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-kafka.yaml --env-file .env up -d
	@echo '==========================================================='

spark:
	@echo '__________________________________________________________'
	@echo 'Creating Spark Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-spark.yaml --env-file .env up -d
	@echo '==========================================================='

spark-produce:
	@echo '__________________________________________________________'
	@echo 'Producing streaming events ...'
	@echo '__________________________________________________________'
	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-1 \
		python \
		/spark-scripts/cryptocurrency.py.py

spark-consume-assets:
	@echo '__________________________________________________________'
	@echo 'Consuming Assets events ...'
	@echo '__________________________________________________________'
	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-2 \
		spark-submit \
		/spark-scripts/assets.py

spark-consume-rates:
	@echo '__________________________________________________________'
	@echo 'Consuming Rates events ...'
	@echo '__________________________________________________________'
	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-2 \
		spark-submit \
		/spark-scripts/rates.py

spark-consume-exchanges:
	@echo '__________________________________________________________'
	@echo 'Consuming Exchanges events ...'
	@echo '__________________________________________________________'
	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-2 \
		spark-submit \
		/spark-scripts/exchanges.py

spark-consume-markets:
	@echo '__________________________________________________________'
	@echo 'Consuming Markets events ...'
	@echo '__________________________________________________________'
	@docker exec ${SPARK_WORKER_CONTAINER_NAME}-2 \
		spark-submit \
		/spark-scripts/markets.py

postgres: postgres-create postgres-create-warehouse

postgres-create:
	@docker compose -f ./docker/docker-compose-postgres.yaml --env-file .env up -d
	@echo '__________________________________________________________'
	@echo 'Postgres container created at port ${POSTGRES_PORT}...'
	@echo '__________________________________________________________'
	@echo 'Postgres Docker Host	: ${POSTGRES_CONTAINER_NAME}' &&\
		echo 'Postgres Account	: ${POSTGRES_USER}' &&\
		echo 'Postgres password	: ${POSTGRES_PASSWORD}' &&\
		echo 'Postgres Db		: ${POSTGRES_DW_DB}'
	@echo '==========================================================='

postgres-create-warehouse:
	@echo '__________________________________________________________'
	@echo 'Creating Warehouse DB...'
	@echo '_________________________________________'
	@docker exec -it ${POSTGRES_CONTAINER_NAME} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f ./sql/warehouse-ddl.sql
	@echo '==========================================================='

airflow:
	@echo '__________________________________________________________'
	@echo 'Creating Airflow Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-airflow.yaml --env-file .env up -d
	@echo '==========================================================='

dbt:
	@echo '__________________________________________________________'
	@echo 'Creating dbt Instance ...'
	@echo '__________________________________________________________'
	@docker compose -f ./docker/docker-compose-dbt.yaml up -d
	@echo '==========================================================='

clean:
	@bash ./scripts/goodnight.sh