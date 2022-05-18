SELECT
    DISTINCT category.value
FROM
    items
JOIN category
    ON items.asin = category.asin
JOIN review
    ON items.asin = review.asin
WHERE
    review.verified = 1
    AND review.overall = 5
    AND review.vote >= 10