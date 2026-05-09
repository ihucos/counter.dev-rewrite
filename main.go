package main

import (
	"context"
	"log"
	"net/http"

	"github.com/gin-contrib/cors"
	"github.com/gin-contrib/sessions"
	"github.com/gin-contrib/sessions/cookie"
	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"

	"app.counter.dev/internal/config"
	"app.counter.dev/internal/db"
	"app.counter.dev/internal/handlers"
	"app.counter.dev/internal/middleware"
)

func main() {
	cfg := config.Load()

	pool, err := pgxpool.New(context.Background(), cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("db connect: %v", err)
	}
	defer pool.Close()

	if err := pool.Ping(context.Background()); err != nil {
		log.Fatalf("db ping: %v", err)
	}

	srv := &handlers.Server{
		Q:    db.New(pool),
		Pool: pool,
		Cfg:  cfg,
	}

	r := gin.Default()

	r.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.AllowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization", "X-Ingest-Secret"},
		AllowCredentials: true,
	}))

	store := cookie.NewStore([]byte(cfg.SessionSecret))
	store.Options(sessions.Options{
		Path:     "/",
		Domain:   cfg.CookieDomain,
		MaxAge:   60 * 60 * 24 * 30,
		Secure:   cfg.CookieSecure,
		HttpOnly: true,
		SameSite: http.SameSiteNoneMode,
	})
	r.Use(sessions.Sessions("counter_session", store))

	r.GET("/health", func(c *gin.Context) { c.JSON(200, gin.H{"ok": true}) })

	api := r.Group("/api")
	{
		api.POST("/auth/signup", srv.Signup)
		api.POST("/auth/login", srv.Login)
		api.POST("/auth/logout", srv.Logout)
		api.POST("/auth/password/recover", srv.RequestPasswordRecovery)
		api.POST("/auth/password/reset", srv.ResetPassword)

		api.POST("/ingest", middleware.RequireIngestSecret(cfg.IngestSecret), srv.Ingest)

		authed := api.Group("")
		authed.Use(middleware.RequireSession())
		{
			authed.GET("/me", srv.GetMe)
			authed.POST("/auth/password/change", srv.ChangePassword)
			authed.POST("/account/email", srv.ChangeEmail)
			authed.POST("/account/timezone", srv.UpdateTimezone)
			authed.POST("/account/prefs", srv.UpdatePrefs)
			authed.DELETE("/account", srv.DeleteAccount)

			authed.GET("/sites", srv.ListSites)
			authed.POST("/sites", srv.CreateSite)
			authed.PUT("/sites/:id/allowed-domains", srv.UpdateSiteAllowedDomains)
			authed.DELETE("/sites/:id", srv.DeleteSite)

			authed.GET("/query", srv.Query)
		}
	}

	addr := ":" + cfg.Port
	log.Printf("listening on %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatal(err)
	}
}
