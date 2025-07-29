-- Network rewards, by day

SELECT 
    DATE(`timestamp`) `day`, 
    SUM(CAST(`value` AS BIGNUMERIC)) `rewards` 
FROM `dharitri.transactions` 
WHERE `operation` = "reward"
GROUP BY `day`
ORDER BY `day` DESC

-- Number of transactions, by day

SELECT 
    DATE(`timestamp`) `day`, 
    COUNT(*) `transactions`
FROM `dharitri.transactions`
GROUP BY `day`
ORDER BY `day` DESC

--- Transactions with the largest transferred `value`, by day

SELECT DATE(`timestamp`) `day`, `_id` `hash`, `sender`, `receiver`, `value`
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY DATE(`timestamp`) ORDER BY value DESC) AS `row_num`
    FROM `dharitri.transactions`
    WHERE `status` = 'success'
)
WHERE `row_num` = 1
ORDER BY `day` DESC
LIMIT 100;
