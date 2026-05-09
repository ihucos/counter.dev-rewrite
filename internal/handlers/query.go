package handlers

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgtype"

	"app.counter.dev/internal/db"
	"app.counter.dev/internal/middleware"
)

const dateLayout = "2006-01-02"

func (s *Server) Query(c *gin.Context) {
	startStr := c.Query("start_date")
	endStr := c.Query("end_date")
	siteStr := c.Query("site")
	if startStr == "" || endStr == "" || siteStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "start_date, end_date, site required"})
		return
	}

	start, err := time.Parse(dateLayout, startStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "bad start_date"})
		return
	}
	end, err := time.Parse(dateLayout, endStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "bad end_date"})
		return
	}

	uid := middleware.CurrentUserID(c)
	site, err := s.Q.GetSiteByDomain(c, db.GetSiteByDomainParams{UserID: uid, Domain: siteStr})
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "site not found"})
		return
	}

	rows, err := s.Q.AggregateCounts(c, db.AggregateCountsParams{
		SiteID:    site.ID,
		StartDate: pgtype.Date{Time: start, Valid: true},
		EndDate:   pgtype.Date{Time: end, Valid: true},
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "query failed"})
		return
	}

	out := map[string]map[string]int64{}
	for _, r := range rows {
		bucket, ok := out[r.Metric]
		if !ok {
			bucket = map[string]int64{}
			out[r.Metric] = bucket
		}
		bucket[r.Value] = r.Total
	}
	c.JSON(http.StatusOK, out)
}
