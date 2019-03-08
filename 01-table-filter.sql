DROP TABLE IF EXISTS monkeytemp.rp_equity_filtered_djns2;

CREATE TABLE IF NOT EXISTS monkeytemp.rp_equity_filtered_djns2 
AS (SELECT * FROM rp.equity_just_djns2
WHERE RELEVANCE = 100
AND ENS = 100
AND `GROUP` IN ("acquisitions-mergers", "analyst-ratings", "assets", "bankruptcy", "credit", "credit-ratings", "dividends", "earnings", "equity-actions", "labor-issues", "product-services", "revenues")
AND ISIN LIKE 'US%');

ALTER TABLE monkeytemp.rp_equity_filtered_djns2 ADD COLUMN CUSIP_FROM_ISIN varchar(12) AFTER ISIN;

UPDATE monkeytemp.rp_equity_filtered_djns2 SET CUSIP_FROM_ISIN = SUBSTRING(ISIN, 3, 8);

-- will result in duplicate news records, but should not affect final binary results on news exists/does not exist for certain periods
DROP TABLE IF EXISTS monkeytemp.rp_equity_filtered_djns2_permno;

CREATE TABLE IF NOT EXISTS monkeytemp.rp_equity_filtered_djns2_permno 
AS (SELECT * FROM
(
(SELECT * 
	FROM monkeytemp.rp_equity_filtered_djns2) A
	INNER JOIN
(SELECT DISTINCT PERMNO, NCUSIP, COMNAM
	FROM crsp.dsenames) B
ON A.CUSIP_FROM_ISIN = B.NCUSIP))
;

-- check for different names: no ENTITY_NAME in djns2 table. Aborted
/* 
ALTER TABLE monkeytemp.rp_equity_filtered_djns2_permno ADD COLUMN SAME_NAME_SUBSTR tinyint;

UPDATE monkeytemp.rp_equity_filtered_djns2_permno 
SET SAME_NAME_SUBSTR = SUBSTRING_INDEX(ENTITY_NAME, ' ', 1) 
RLIKE SUBSTRING_INDEX(COMNAM, ' ', 1);

SELECT ENTITY_NAME, COMNAM
FROM monkeytemp.rp_equity_filtered_djns2_permno
WHERE SAME_NAME_SUBSTR = 0;
*/

-- create simplified table for processing in python:
DROP TABLE IF EXISTS monkeytemp.rp_equity_filtered_djns2_permno_simplified;

CREATE TABLE IF NOT EXISTS monkeytemp.rp_equity_filtered_djns2_permno_simplified
AS (SELECT TIMESTAMP_UTC, PERMNO
FROM monkeytemp.rp_equity_filtered_djns2_permno)

-- derive trading dates available
CREATE TABLE IF NOT EXISTS monkeytemp.trading_dates
AS (SELECT DISTINCT date FROM taq_prices.returns_15min 
ORDER BY date ASC);

-- select columns & dates from crsp.dsf for use
DROP TABLE IF EXISTS monkeytemp.crsp_dsf_filtered;

CREATE TABLE IF NOT EXISTS monkeytemp.crsp_dsf_filtered
AS (SELECT permno, date, prc, ret, shrout FROM crsp.dsf
WHERE date BETWEEN '2016-01-01' AND '2017-07-03');

