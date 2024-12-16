SELECT 'CREATE DATABASE data_staging'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'data_staging')\gexec