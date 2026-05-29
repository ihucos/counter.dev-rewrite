package models

import (
	"fmt"
	"math/rand"
	"net/url"
	"time"

	"github.com/gomodule/redigo/redis"
	"gorm.io/gorm"
)

// set needs to overgrow sometimes so it does allow for "trending" new entries
// to catch up with older ones and replace them at some point.
const zetMaxSize = 100
const zetTrimEveryCalls = 100
const truncateAt = 256
const loglinesKeep = 30

var fieldsZet = []string{"lang", "ref", "loc", "page"}
var fieldsHash = []string{"date", "weekday", "platform", "hour", "browser", "device", "country", "screen"}

type Visit map[string]string

type VisitItemKey struct {
	TimeRange string
	UserId    string
	Origin    string
	Field     string
}

func (vik VisitItemKey) String() string {
	return fmt.Sprintf("v:%s,%s,%s,%s",
		url.QueryEscape(vik.Origin),
		url.QueryEscape(vik.UserId),
		url.QueryEscape(vik.Field),
		url.QueryEscape(vik.TimeRange))

}

type Site struct {
	redis  redis.Conn
	id     string
	userId string
	db     *gorm.DB
}

// taken from here at August 2020:
// https://gs.statcounter.com/screen-resolution-stats
var ScreenResolutions = map[string]bool{
	"1280x720":  true,
	"1280x800":  true,
	"1366x768":  true,
	"1440x900":  true,
	"1536x864":  true,
	"1600x900":  true,
	"1920x1080": true,
	"360x640":   true,
	"360x720":   true,
	"360x740":   true,
	"360x760":   true,
	"360x780":   true,
	"375x667":   true,
	"375x812":   true,
	"412x846":   true,
	"412x869":   true,
	"412x892":   true,
	"414x736":   true,
	"414x896":   true,
	"768x1024":  true}

func truncate(stri string) string {
	if len(stri) > truncateAt {
		return stri[:truncateAt]
	}
	return stri
}

func (site Site) saveVisitPart(timeRange string, data Visit, expireAt time.Time) {
	var redisKey string
	for _, field := range fieldsZet {
		redisKey = VisitItemKey{TimeRange: timeRange, Field: field, Origin: site.id, UserId: site.userId}.String()
		val := data[field]
		if val != "" {
			site.redis.Send("ZINCRBY", redisKey, 1, truncate(val))
			if rand.Intn(zetTrimEveryCalls) == 0 {
				site.redis.Send("ZREMRANGEBYRANK", redisKey, 0, -zetMaxSize)
			}
			if !expireAt.IsZero() {
				site.redis.Send("EXPIREAT", redisKey, expireAt.Unix())
			}
		}
	}

	for _, field := range fieldsHash {
		redisKey = VisitItemKey{TimeRange: timeRange, Field: field, Origin: site.id, UserId: site.userId}.String()
		val := data[field]
		if val != "" {
			site.redis.Send("HINCRBY", redisKey, truncate(val), 1)
			if !expireAt.IsZero() {
				site.redis.Send("EXPIREAT", redisKey, expireAt.Unix())
			}
		}
	}
}

func (site Site) SaveVisit(visit Visit, at time.Time) {

	// Tolerance for handling time zones and all that nasty stuff
	expireTolerance := time.Hour * 14

	nextYear := time.Date(at.Year(), time.January, 1,
		0, 0, 0, 0,
		at.Location()).AddDate(1, 0, 0)

	nextMonth := time.Date(at.Year(), at.Month(), 1,
		0, 0, 0, 0,
		at.Location()).AddDate(0, 1, 0)

	inTwoDays := time.Date(at.Year(), at.Month(), at.Day(),
		0, 0, 0, 0,
		at.Location()).AddDate(0, 0, 2)

	// This Year
	site.saveVisitPart(
		at.Format("2006"),
		visit,
		nextYear.Add(expireTolerance))

	// This Month
	site.saveVisitPart(
		at.Format("2006-01"),
		visit,
		nextMonth.Add(expireTolerance))

	// Today / Yesterday
	site.saveVisitPart(
		at.Format("2006-01-02"),
		visit,
		// we expire in two days for the yesterday entry
		inTwoDays.Add(expireTolerance))

	// all
	site.saveVisitPart(
		"all",
		visit,
		time.Time{})
}

func (site Site) Log(logLine string) {
	redisKey := fmt.Sprintf("log:%s:%s", site.id, site.userId)
	site.redis.Send("ZADD", redisKey, time.Now().Unix(), truncate(logLine))
	site.redis.Send("ZREMRANGEBYRANK", redisKey, 0, -loglinesKeep)
}
