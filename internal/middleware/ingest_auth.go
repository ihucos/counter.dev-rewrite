package middleware

import (
	"crypto/subtle"
	"net/http"

	"github.com/gin-gonic/gin"
)

func RequireIngestSecret(secret string) gin.HandlerFunc {
	expected := []byte(secret)
	return func(c *gin.Context) {
		provided := []byte(c.GetHeader("X-Ingest-Secret"))
		if len(provided) == 0 || subtle.ConstantTimeCompare(provided, expected) != 1 {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}
		c.Next()
	}
}
