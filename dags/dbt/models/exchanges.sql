{{
  config(
    materialized='table'
  )
}}

WITH exchanges AS (
SELECT 
    exchange_id,
    exchange_name AS name,
    exchange_rank AS rank,
    socket,
    exchange_url, 
FROM
  `dibimbing-de.Final_Project_Dibimbing.Coin_Market_Cap`

)

SELECT 
*
FROM 
exchanges