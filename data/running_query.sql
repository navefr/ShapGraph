SELECT category.value
FROM items as source_items
JOIN also_buy
ON source_items.asin = also_buy.asin
JOIN items as bought_items
ON also_buy.buy = bought_items.asin
JOIN review as review1
ON review1.asin = source_items.asin
JOIN review as review2
ON review2.asin = source_items.asin
JOIN feature
ON source_items.asin = feature.asin
JOIN category
ON bought_items.asin = category.asin
WHERE (
        source_items.main_cat = 'Computers'
        OR source_items.main_cat = 'All Electronics'
    )
    AND (
        LOWER(feature.value) LIKE '%mb%'
        OR LOWER(feature.value) LIKE '%memory%'
    )
    AND review1.overall >= 4
    AND review1.vote > 0
    AND review1.verified = 1
    AND review2.overall >= 4
    AND review2.vote > 0
    AND review2.verified = 1
GROUP BY category.value