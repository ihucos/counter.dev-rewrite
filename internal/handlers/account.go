package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/gin-contrib/sessions"
	"github.com/gin-gonic/gin"

	"app.counter.dev/internal/db"
	"app.counter.dev/internal/middleware"
)

type userView struct {
	ID       string          `json:"id"`
	Username string          `json:"username"`
	Email    *string         `json:"email"`
	Timezone int32           `json:"timezone"`
	Prefs    json.RawMessage `json:"prefs"`
}

func userResponse(u *db.User) userView {
	prefs := json.RawMessage(u.Prefs)
	if len(prefs) == 0 {
		prefs = json.RawMessage("{}")
	}
	return userView{
		ID:       u.ID,
		Username: u.Username,
		Email:    u.Email,
		Timezone: u.Timezone,
		Prefs:    prefs,
	}
}

func (s *Server) GetMe(c *gin.Context) {
	uid := middleware.CurrentUserID(c)
	user, err := s.Q.GetUserByID(c, uid)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	}
	c.JSON(http.StatusOK, userResponse(&user))
}

type changeEmailReq struct {
	Email *string `json:"email"`
}

func (s *Server) ChangeEmail(c *gin.Context) {
	var req changeEmailReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	uid := middleware.CurrentUserID(c)
	if err := s.Q.UpdateEmail(c, db.UpdateEmailParams{ID: uid, Email: req.Email}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "update failed"})
		return
	}
	c.Status(http.StatusNoContent)
}

type updateTimezoneReq struct {
	Timezone int32 `json:"timezone"`
}

func (s *Server) UpdateTimezone(c *gin.Context) {
	var req updateTimezoneReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if req.Timezone < -14 || req.Timezone > 14 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "timezone out of range"})
		return
	}
	uid := middleware.CurrentUserID(c)
	if err := s.Q.UpdateTimezone(c, db.UpdateTimezoneParams{ID: uid, Timezone: req.Timezone}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "update failed"})
		return
	}
	c.Status(http.StatusNoContent)
}

func (s *Server) UpdatePrefs(c *gin.Context) {
	var prefs map[string]string
	if err := c.ShouldBindJSON(&prefs); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	raw, err := json.Marshal(prefs)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid prefs"})
		return
	}
	uid := middleware.CurrentUserID(c)
	if err := s.Q.UpdatePrefs(c, db.UpdatePrefsParams{ID: uid, Prefs: raw}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "update failed"})
		return
	}
	c.Status(http.StatusNoContent)
}

func (s *Server) DeleteAccount(c *gin.Context) {
	uid := middleware.CurrentUserID(c)
	if err := s.Q.DeleteUser(c, uid); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "delete failed"})
		return
	}
	sess := sessions.Default(c)
	sess.Clear()
	sess.Options(sessions.Options{Path: "/", MaxAge: -1})
	_ = sess.Save()
	c.Status(http.StatusNoContent)
}
