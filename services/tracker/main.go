package main

import (
	"log"
	"net/http"
	"os"

	"github.com/gomodule/redigo/redis"
)

func main() {
	redisURL := envDefault("WEBSTATS_REDIS_URL", "redis://localhost:6379")
	bind := envDefault("WEBSTATS_BIND", ":8000")

	pool := &redis.Pool{
		Dial: func() (redis.Conn, error) {
			return redis.DialURL(redisURL)
		},
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/track", handleTrack(pool))
	mux.HandleFunc("/trackpage", handleTrackPage(pool))

	addr := bind
	log.Println("Listening on", addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}

func env(key string) string {
	v := os.Getenv(key)
	if v == "" {
		log.Fatalf("empty or missing env: %s", key)
	}
	return v
}

func envDefault(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
