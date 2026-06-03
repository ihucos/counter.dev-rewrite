package main

import (
	"fmt"
	"net/http"
	"net/url"
	"regexp"
	"strings"

	"github.com/gomodule/redigo/redis"
	"github.com/xavivars/uasurfer"
	"golang.org/x/text/language"
	"golang.org/x/text/language/display"
)

var originRe = regexp.MustCompile(`^.*?:\/\/(?:www\.)?(.*)$`)

func originToSiteID(origin string) string {
	m := originRe.FindStringSubmatch(origin)
	if len(m) < 2 {
		return origin
	}
	return m[1]
}

func handleTrack(pool *redis.Pool, cfg Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn := pool.Get()
		defer conn.Close()

		// Resolve user
		var user User
		uuid := r.FormValue("id")
		if uuid != "" {
			var err error
			user, err = NewUserByCachedUUID(conn, uuid, cfg.PasswordSalt)
			if err != nil {
				http.Error(w, err.Error(), http.StatusBadRequest)
				return
			}
		} else {
			userID := r.FormValue("user")
			if userID == "" {
				userID = r.FormValue("site")
				if userID == "" {
					http.Error(w, "missing site param", http.StatusBadRequest)
					return
				}
			}
			user = NewUser(conn, userID, cfg.PasswordSalt)
		}

		now := LocalTime(parseUTCOffset(r, "utcoffset"))
		userAgent := r.Header.Get("User-Agent")
		ua := uasurfer.Parse(userAgent)
		origin := r.Header.Get("Origin")
		if origin == "" || origin == "null" {
			http.Error(w, "Origin header can not be empty, not set or \"null\"", http.StatusBadRequest)
			return
		}

		// Ignore some origins
		if strings.HasSuffix(origin, ".translate.goog") {
			http.Error(w, "Ignoring due origin", http.StatusBadRequest)
			return
		}

		// Set caching headers
		w.Header().Set("Expires", now.Format("Mon, 2 Jan 2006")+" 23:59:59 GMT")
		w.Header().Set("Access-Control-Allow-Origin", "*")

		// Drop bots and localhost
		if ua.IsBot() ||
			strings.Contains(userAgent, " HeadlessChrome/") ||
			strings.Contains(userAgent, "PetalBot;") ||
			strings.Contains(userAgent, "AdsBot") {
			return
		}
		originURL, err := url.Parse(origin)
		if err == nil && (originURL.Hostname() == "localhost" || originURL.Hostname() == "127.0.0.1") {
			return
		}

		// Build visit
		v := Visit{}

		refParam := r.FormValue("referrer")
		if parsedURL, err := url.Parse(refParam); err == nil && parsedURL.Host != "" {
			v.Ref = parsedURL.Host
		}

		ref := r.Header.Get("Referer")
		if parsedURL, err := url.Parse(ref); err == nil && parsedURL.Path != "" {
			v.Loc = parsedURL.Path
		}

		tags, _, err := language.ParseAcceptLanguage(r.Header.Get("Accept-Language"))
		if err == nil && len(tags) > 0 {
			v.Lang = display.English.Languages().Name(tags[0])
		}

		country := r.FormValue("country")
		if country == "" {
			country = r.Header.Get("CF-IPCountry")
		}
		if country != "" && country != "XX" {
			v.Country = strings.ToLower(country)
		}

		screenInput := r.FormValue("screen")
		if screenInput != "" {
			if ScreenResolutions[screenInput] {
				v.Screen = screenInput
			} else {
				v.Screen = "Other"
			}
		}

		v.Date = now.Format("2006-01-02")
		v.Weekday = fmt.Sprintf("%d", now.Weekday())
		v.Hour = fmt.Sprintf("%d", now.Hour())
		v.Browser = ua.Browser.Name.StringTrimPrefix()
		v.Device = ua.DeviceType.StringTrimPrefix()

		if ua.OS.Name == uasurfer.OSAndroid {
			v.Platform = "Android"
		} else {
			v.Platform = ua.OS.Platform.StringTrimPrefix()
		}

		// Persist
		logLine := fmt.Sprintf("[%s] %s %s %s %s", now.Format("2006-01-02 15:04:05"), country, refParam, v.Device, v.Platform)
		siteID := originToSiteID(origin)

		site := user.NewSite(siteID)
		site.SaveVisit(v, now)
		site.Log(logLine)
		user.IncrSiteLink(siteID)
		user.Signal()

		conn.Flush()

		w.Header().Set("Content-Type", "text/plain")
		w.Header().Set("Cache-Control", "public, immutable")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "OK")
	}
}

func handleTrackPage(pool *redis.Pool, cfg Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn := pool.Get()
		defer conn.Close()

		user, err := NewUserByCachedUUID(conn, r.FormValue("id"), cfg.PasswordSalt)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		now := LocalTime(parseUTCOffset(r, "utcoffset"))

		v := Visit{
			Page:  r.FormValue("page"),
			Date:  now.Format("2006-01-02"),
			Hour:  fmt.Sprintf("%d", now.Hour()),
		}
		// Count is stored as "pageview" in the "page" field
		// The original code used visit["count"]="pageview" which was unused in SaveVisit
		// We keep page field for the zet tracking

		origin := r.Header.Get("Origin")
		if origin == "" || origin == "null" {
			http.Error(w, "Origin header can not be empty, not set or \"null\"", http.StatusBadRequest)
			return
		}

		siteID := originToSiteID(origin)
		site := user.NewSite(siteID)
		site.SaveVisit(v, now)

		conn.Flush()

		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.WriteHeader(http.StatusNoContent)
	}
}

func parseUTCOffset(r *http.Request, key string) int {
	val := r.FormValue(key)
	if val == "" {
		return 0
	}
	var offset int
	if _, err := fmt.Sscanf(val, "%d", &offset); err != nil {
		return 0
	}
	if offset > 14 {
		return 14
	}
	if offset < -12 {
		return -12
	}
	return offset
}

// StringTrimPrefix is needed because uasurfer types have this method.
// It's defined on the uasurfer package types. We just reference it.
