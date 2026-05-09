-- name: IncrementCount :exec
INSERT INTO counts (site_id, date, metric, value, count)
VALUES ($1, $2, $3, $4, $5)
ON CONFLICT (site_id, date, metric, value)
DO UPDATE SET count = counts.count + EXCLUDED.count;

-- name: AggregateCounts :many
SELECT metric, value, SUM(count)::bigint AS total
FROM counts
WHERE site_id = sqlc.arg('site_id')
  AND date BETWEEN sqlc.arg('start_date') AND sqlc.arg('end_date')
GROUP BY metric, value
ORDER BY metric, total DESC;
