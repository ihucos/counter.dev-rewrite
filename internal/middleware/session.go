package middleware

import (
	"net/http"

	"github.com/gin-contrib/sessions"
	"github.com/gin-gonic/gin"
)

const SessionUserIDKey = "user_id"

func RequireSession() gin.HandlerFunc {
	return func(c *gin.Context) {
		s := sessions.Default(c)
		uid := s.Get(SessionUserIDKey)
		uidStr, ok := uid.(string)
		if !ok || uidStr == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}
		c.Set(SessionUserIDKey, uidStr)
		c.Next()
	}
}

func CurrentUserID(c *gin.Context) string {
	v, _ := c.Get(SessionUserIDKey)
	s, _ := v.(string)
	return s
}
