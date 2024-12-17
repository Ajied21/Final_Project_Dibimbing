{{
  config(
    materialized='table'
  )
}}

WITH rates AS (
SELECT DISTINCT
    rates_id AS id,
    rates_symbol AS symbol,
    rates_currency_Symbol AS currency_Symbol,
    rates_type AS type,
FROM
  `dibimbing-de.Final_Project_Dibimbing.Coin_Market_Cap`

)

SELECT 
*
FROM 
rates