package main

import (
	"fmt"
	"math/rand"
	"net/url"
	"strings"
	"time"

	"github.com/gomodule/redigo/redis"
)

const (
	truncateAt        = 256
	zetMaxSize        = 100
	zetTrimEveryCalls = 100
	loglinesKeep      = 30
)

var (
	fieldsZet  = []string{"lang", "ref", "loc", "page"}
	fieldsHash = []string{"date", "weekday", "platform", "hour", "browser", "device", "country", "screen"}
)

// ScreenResolutions is a set of known screen resolutions.
var ScreenResolutions = map[string]bool{
	"1280x720": true, "1280x800": true, "1366x768": true,
	"1440x900": true, "1536x864": true, "1600x900": true,
	"1920x1080": true, "360x640": true, "360x720": true,
	"360x740": true, "360x760": true, "360x780": true,
	"375x667": true, "375x812": true, "412x846": true,
	"412x869": true, "412x892": true, "414x736": true,
	"414x896": true, "768x1024": true,
}

// Visit holds parsed tracking data for a single request.
type Visit struct {
	Lang     string
	Ref      string
	Loc      string
	Page     string
	Date     string
	Weekday  string
	Hour     string
	Platform string
	Browser  string
	Device   string
	Country  string
	Screen   string
}

// VisitItemKey represents a Redis key for visit data.
type VisitItemKey struct {
	TimeRange string
	ID        string
	Origin    string
	Field     string
}

func (k VisitItemKey) String() string {
	return fmt.Sprintf("v:%s,%s,%s,%s",
		url.QueryEscape(k.Origin),
		url.QueryEscape(k.ID),
		url.QueryEscape(k.Field),
		url.QueryEscape(k.TimeRange))
}

// NewVisitItemKey parses a VisitItemKey from its string representation.
func NewVisitItemKey(key string) (VisitItemKey, error) {
	parts := strings.Split(strings.TrimPrefix(key, "v:"), ",")
	if len(parts) != 4 {
		return VisitItemKey{}, fmt.Errorf("malformed key: %s", key)
	}
	origin, err := url.QueryUnescape(parts[0])
	if err != nil {
		return VisitItemKey{}, err
	}
	id, err := url.QueryUnescape(parts[1])
	if err != nil {
		return VisitItemKey{}, err
	}
	field, err := url.QueryUnescape(parts[2])
	if err != nil {
		return VisitItemKey{}, err
	}
	timeRange, err := url.QueryUnescape(parts[3])
	if err != nil {
		return VisitItemKey{}, err
	}
	return VisitItemKey{Origin: origin, ID: id, Field: field, TimeRange: timeRange}, nil
}

// RedisType returns whether this field is stored as a zet (sorted set) or hash.
func (k VisitItemKey) RedisType() string {
	for _, f := range fieldsHash {
		if f == k.Field {
			return "hash"
		}
	}
	for _, f := range fieldsZet {
		if f == k.Field {
			return "zet"
		}
	}
	return ""
}

// Site represents a tracked website for a user.
type Site struct {
	conn   redis.Conn
	origin string
	id     string
}

// NewSite creates a Site for the given connection, id (from id/site param) and origin.
func NewSite(conn redis.Conn, id, origin string) Site {
	return Site{conn: conn, origin: origin, id: truncate(id)}
}

// SaveVisit persists a visit to Redis at multiple time granularities.
func (s Site) SaveVisit(v Visit, at time.Time) {
	expireTolerance := 14 * time.Hour

	nextYear := time.Date(at.Year(), time.January, 1, 0, 0, 0, 0, at.Location()).AddDate(1, 0, 0)
	nextMonth := time.Date(at.Year(), at.Month(), 1, 0, 0, 0, 0, at.Location()).AddDate(0, 1, 0)
	inTwoDays := time.Date(at.Year(), at.Month(), at.Day(), 0, 0, 0, 0, at.Location()).AddDate(0, 0, 2)

	s.saveVisitPart(at.Format("2006"), v, nextYear.Add(expireTolerance))
	s.saveVisitPart(at.Format("2006-01"), v, nextMonth.Add(expireTolerance))
	s.saveVisitPart(at.Format("2006-01-02"), v, inTwoDays.Add(expireTolerance))
	s.saveVisitPart("all", v, time.Time{})
}

// Log appends a log line for the site.
func (s Site) Log(line string) {
	key := fmt.Sprintf("log:%s:%s", s.origin, s.id)
	s.conn.Send("ZADD", key, time.Now().Unix(), truncate(line))
	s.conn.Send("ZREMRANGEBYRANK", key, 0, -loglinesKeep)
}

func (s Site) saveVisitPart(timeRange string, v Visit, expireAt time.Time) {
	for _, field := range fieldsZet {
		val := visitField(v, field)
		if val == "" {
			continue
		}
		key := VisitItemKey{TimeRange: timeRange, Field: field, Origin: s.origin, ID: s.id}.String()
		s.conn.Send("ZINCRBY", key, 1, truncate(val))
		if rand.Intn(zetTrimEveryCalls) == 0 {
			s.conn.Send("ZREMRANGEBYRANK", key, 0, -zetMaxSize)
		}
		if !expireAt.IsZero() {
			s.conn.Send("EXPIREAT", key, expireAt.Unix())
		}
	}

	for _, field := range fieldsHash {
		val := visitField(v, field)
		if val == "" {
			continue
		}
		key := VisitItemKey{TimeRange: timeRange, Field: field, Origin: s.origin, ID: s.id}.String()
		s.conn.Send("HINCRBY", key, truncate(val), 1)
		if !expireAt.IsZero() {
			s.conn.Send("EXPIREAT", key, expireAt.Unix())
		}
	}
}

func visitField(v Visit, field string) string {
	switch field {
	case "lang":
		return v.Lang
	case "ref":
		return v.Ref
	case "loc":
		return v.Loc
	case "page":
		return v.Page
	case "date":
		return v.Date
	case "weekday":
		return v.Weekday
	case "hour":
		return v.Hour
	case "platform":
		return v.Platform
	case "browser":
		return v.Browser
	case "device":
		return v.Device
	case "country":
		return v.Country
	case "screen":
		return v.Screen
	}
	return ""
}

func truncate(s string) string {
	if len(s) > truncateAt {
		return s[:truncateAt]
	}
	return s
}
