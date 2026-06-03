package main

import (
	"fmt"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"

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

func handleTrack(pool *redis.Pool) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn := pool.Get()
		defer conn.Close()

		// Resolve id value
		idVal := r.FormValue("id")
		if idVal == "" {
			idVal = r.FormValue("user")
			if idVal == "" {
				idVal = r.FormValue("site")
				if idVal == "" {
					http.Error(w, "missing site param", http.StatusBadRequest)
					return
				}
			}
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
		originSiteID := originToSiteID(origin)

		site := NewSite(conn, idVal, originSiteID)
		site.SaveVisit(v, now)
		site.Log(logLine)

		conn.Flush()

		w.Header().Set("Content-Type", "text/plain")
		w.Header().Set("Cache-Control", "public, immutable")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "OK")
	}
}

func handleTrackPage(pool *redis.Pool) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		conn := pool.Get()
		defer conn.Close()

		// id param is required for handleTrackPage
		idVal := r.FormValue("id")
		if idVal == "" {
			http.Error(w, "missing id param", http.StatusBadRequest)
			return
		}

		now := LocalTime(parseUTCOffset(r, "utcoffset"))

		v := Visit{
			Page: r.FormValue("page"),
			Date: now.Format("2006-01-02"),
			Hour: fmt.Sprintf("%d", now.Hour()),
		}

		origin := r.Header.Get("Origin")
		if origin == "" || origin == "null" {
			http.Error(w, "Origin header can not be empty, not set or \"null\"", http.StatusBadRequest)
			return
		}

		originSiteID := originToSiteID(origin)

		site := NewSite(conn, idVal, originSiteID)
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

// LocalTime returns the current time adjusted by utcOffset hours.
func LocalTime(utcOffset int) time.Time {
	return time.Now().UTC().Add(time.Duration(utcOffset) * time.Hour)
}
