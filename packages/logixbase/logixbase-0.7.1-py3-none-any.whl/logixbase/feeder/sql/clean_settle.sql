UPDATE [FUTURE_RESEARCH_1MIN].[dbo].TA
SET [SETTLE] = ROUND(([HIGH] + [LOW] + [CLOSE] + [OPEN]) / 4 / 2, 0) * 2
WHERE PK IN (SELECT PK
FROM  [FUTURE_RESEARCH_1MIN].[dbo].TA
WHERE [SETTLE] = 0 
OR [Settle] / [Close] > 1.2
OR [Settle] / [Close] < 0.8
)

SELECT * FROM
[FUTURE_RESEARCH_1MIN].[dbo].TA
WHERE PK IN (
SELECT PK
FROM  [FUTURE_RESEARCH_1MIN].[dbo].TA
WHERE [SETTLE] = 0 
OR [Settle] / [Close] > 1.2
OR [Settle] / [Close] < 0.8
)