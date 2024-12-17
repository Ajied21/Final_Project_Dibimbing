{{
  config(
    materialized='table'
  )
}}

WITH assets AS (
SELECT DISTINCT
    asset_id AS id,
    asset_name AS name,
    asset_rank AS rank,
    asset_symbol AS symbol,
    explorer,
FROM
  `dibimbing-de.Final_Project_Dibimbing.Coin_Market_Cap`

)

SELECT 
*
FROM 
assets