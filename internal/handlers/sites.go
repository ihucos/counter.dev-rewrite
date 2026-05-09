package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"app.counter.dev/internal/db"
	"app.counter.dev/internal/middleware"
)

func (s *Server) ListSites(c *gin.Context) {
	uid := middleware.CurrentUserID(c)
	sites, err := s.Q.ListSitesByUser(c, uid)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "db error"})
		return
	}
	c.JSON(http.StatusOK, sites)
}

type createSiteReq struct {
	Domain string `json:"domain" binding:"required"`
}

func (s *Server) CreateSite(c *gin.Context) {
	var req createSiteReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	uid := middleware.CurrentUserID(c)
	site, err := s.Q.CreateSite(c, db.CreateSiteParams{UserID: uid, Domain: req.Domain})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "create failed"})
		return
	}
	c.JSON(http.StatusCreated, site)
}

type allowedDomainsReq struct {
	AllowedDomains       []string `json:"allowed_domains"`
	FilterAllowedDomains bool     `json:"filter_allowed_domains"`
}

func (s *Server) UpdateSiteAllowedDomains(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}
	var req allowedDomainsReq
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if req.AllowedDomains == nil {
		req.AllowedDomains = []string{}
	}
	uid := middleware.CurrentUserID(c)
	if err := s.Q.UpdateSiteAllowedDomains(c, db.UpdateSiteAllowedDomainsParams{
		ID:                   id,
		AllowedDomains:       req.AllowedDomains,
		FilterAllowedDomains: req.FilterAllowedDomains,
		UserID:               uid,
	}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "update failed"})
		return
	}
	c.Status(http.StatusNoContent)
}

func (s *Server) DeleteSite(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}
	uid := middleware.CurrentUserID(c)
	if err := s.Q.DeleteSite(c, db.DeleteSiteParams{ID: id, UserID: uid}); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "delete failed"})
		return
	}
	c.Status(http.StatusNoContent)
}
