package handlers

import (
	"github.com/jackc/pgx/v5/pgxpool"

	"app.counter.dev/internal/config"
	"app.counter.dev/internal/db"
)

type Server struct {
	Q    *db.Queries
	Pool *pgxpool.Pool
	Cfg  *config.Config
}
