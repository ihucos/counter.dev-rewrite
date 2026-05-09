package handlers

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"net/http"
	"time"

	"github.com/gin-contrib/sessions"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"golang.org/x/crypto/bcrypt"

	"app.counter.dev/internal/db"
	"app.counter.dev/internal/middleware"
)

type signupReq struct {
	Username string  `json:"username" binding:"required,min=2,max=64"`
	Password string  `json:"password" binding:"required,min=8"`
	Email    *string `json:"email"`
}

func (s *Server) Signup(c *gin.Context) {
	var req signupReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if _, err := s.Q.GetUserByUsername(c, req.Username); err == nil {
		c.JSON(http.StatusConflict, gin.H{"error": "username taken"})
		return
	} else if !errors.Is(err, pgx.ErrNoRows) {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "db error"})
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "hash failed"})
		return
	}

	user, err := s.Q.CreateUser(c, db.CreateUserParams{
		ID:           uuid.NewString(),
		Username:     req.Username,
		Email:        req.Email,
		PasswordHash: string(hash),
		Timezone:     0,
		Prefs:        []byte("{}"),
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "create failed"})
		return
	}

	if err := writeSession(c, user.ID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "session error"})
		return
	}

	c.JSON(http.StatusCreated, userResponse(&user))
}

type loginReq struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

func (s *Server) Login(c *gin.Context) {
	var req loginReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := s.Q.GetUserByUsername(c, req.Username)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
		return
	}
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid credentials"})
		return
	}

	if err := writeSession(c, user.ID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "session error"})
		return
	}

	c.JSON(http.StatusOK, userResponse(&user))
}

func (s *Server) Logout(c *gin.Context) {
	sess := sessions.Default(c)
	sess.Clear()
	sess.Options(sessions.Options{Path: "/", MaxAge: -1})
	if err := sess.Save(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "session error"})
		return
	}
	c.Status(http.StatusNoContent)
}

type changePasswordReq struct {
	CurrentPassword string `json:"current_password" binding:"required"`
	NewPassword     string `json:"new_password" binding:"required,min=8"`
}

func (s *Server) ChangePassword(c *gin.Context) {
	var req changePasswordReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	uid := middleware.CurrentUserID(c)
	user, err := s.Q.GetUserByID(c, uid)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	}
	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.CurrentPassword)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "wrong current password"})
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(req.NewPassword), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "hash failed"})
		return
	}
	if err := s.Q.UpdatePassword(c, db.UpdatePasswordParams{ID: uid, PasswordHash: string(hash)}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "update failed"})
		return
	}
	c.Status(http.StatusNoContent)
}

type recoverReq struct {
	Email string `json:"email" binding:"required,email"`
}

type recoverResp struct {
	Token string `json:"token"`
}

func (s *Server) RequestPasswordRecovery(c *gin.Context) {
	var req recoverReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := s.Q.GetUserByEmail(c, &req.Email)
	if err != nil {
		c.Status(http.StatusNoContent)
		return
	}

	token, err := randomToken()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "token error"})
		return
	}
	expiresAt := time.Now().Add(1 * time.Hour)
	if err := s.Q.SetRecoveryToken(c, db.SetRecoveryTokenParams{
		ID:                     user.ID,
		RecoveryToken:          &token,
		RecoveryTokenExpiresAt: &expiresAt,
	}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "db error"})
		return
	}

	// TODO: send token via email. For now we return it directly so the
	// flow is wired end-to-end.
	c.JSON(http.StatusOK, recoverResp{Token: token})
}

type resetReq struct {
	Token       string `json:"token" binding:"required"`
	NewPassword string `json:"new_password" binding:"required,min=8"`
}

func (s *Server) ResetPassword(c *gin.Context) {
	var req resetReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := s.Q.GetUserByRecoveryToken(c, &req.Token)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid or expired token"})
		return
	}

	hash, err := bcrypt.GenerateFromPassword([]byte(req.NewPassword), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "hash failed"})
		return
	}
	if err := s.Q.UpdatePassword(c, db.UpdatePasswordParams{ID: user.ID, PasswordHash: string(hash)}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "update failed"})
		return
	}
	if err := s.Q.ClearRecoveryToken(c, user.ID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "update failed"})
		return
	}
	c.Status(http.StatusNoContent)
}

func writeSession(c *gin.Context, userID string) error {
	sess := sessions.Default(c)
	sess.Set(middleware.SessionUserIDKey, userID)
	return sess.Save()
}

func randomToken() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}
