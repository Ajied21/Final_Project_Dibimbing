{{
  config(
    materialized='table'
  )
}}

WITH fact_markets AS (
SELECT DISTINCT
    exchange_id,
    asset_id AS base_id,
    quoteId AS quote_id,
    supply,
    marketCapUsd AS market_cap_usd,
    priceQuote AS price_quote,
    priceUsd AS price_usd,
    rateUsd AS rates_usd,
    volumeUsd24Hr AS volume_usd,
    changePercent24Hr AS change_percent,
    vwap24Hr AS vwap,
    percentExchangeVolume AS percent_exchange_volume,
    percentTotalVolume AS percent_total_volume,
    tradingPairs AS trading_pairs,
    updated
FROM
  `dibimbing-de.Final_Project_Dibimbing.Coin_Market_Cap`

)

SELECT 
*
FROM 
fact_markets