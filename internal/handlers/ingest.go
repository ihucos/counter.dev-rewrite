package handlers

import (
	"errors"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"

	"app.counter.dev/internal/db"
)

type ingestItem struct {
	User   string `json:"user" binding:"required"`
	Site   string `json:"site" binding:"required"`
	Metric string `json:"metric" binding:"required"`
	Value  string `json:"value" binding:"required"`
	Incr   int64  `json:"incr"`
}

func (s *Server) Ingest(c *gin.Context) {
	var items []ingestItem
	if err := c.ShouldBindJSON(&items); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if len(items) == 0 {
		c.JSON(http.StatusOK, gin.H{"processed": 0})
		return
	}

	tx, err := s.Pool.Begin(c)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "tx error"})
		return
	}
	defer tx.Rollback(c)

	q := s.Q.WithTx(tx)

	userCache := map[string]*db.User{}
	siteCache := map[string]int64{} // key = userID + "|" + domain

	processed := 0
	for _, it := range items {
		incr := it.Incr
		if incr <= 0 {
			incr = 1
		}

		user, ok := userCache[it.User]
		if !ok {
			u, err := q.GetUserByID(c, it.User)
			if err != nil {
				if errors.Is(err, pgx.ErrNoRows) {
					userCache[it.User] = nil
					continue
				}
				c.JSON(http.StatusInternalServerError, gin.H{"error": "db error"})
				return
			}
			user = &u
			userCache[it.User] = user
		}
		if user == nil {
			continue
		}

		siteKey := it.User + "|" + it.Site
		siteID, ok := siteCache[siteKey]
		if !ok {
			site, err := q.CreateSite(c, db.CreateSiteParams{UserID: it.User, Domain: it.Site})
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "site error"})
				return
			}
			siteID = site.ID
			siteCache[siteKey] = siteID
		}

		date := userLocalDate(user.Timezone)
		if err := q.IncrementCount(c, db.IncrementCountParams{
			SiteID: siteID,
			Date:   date,
			Metric: it.Metric,
			Value:  it.Value,
			Count:  incr,
		}); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "count error"})
			return
		}
		processed++
	}

	if err := tx.Commit(c); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "commit error"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"processed": processed})
}

func userLocalDate(tzOffsetHours int32) pgtype.Date {
	t := time.Now().UTC().Add(time.Duration(tzOffsetHours) * time.Hour)
	y, m, d := t.Date()
	return pgtype.Date{
		Time:  time.Date(y, m, d, 0, 0, 0, 0, time.UTC),
		Valid: true,
	}
}
