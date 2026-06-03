package main

import (
	"time"
)

// LocalTime returns the current time adjusted by utcOffset hours.
func LocalTime(utcOffset int) time.Time {
	return time.Now().UTC().Add(time.Duration(utcOffset) * time.Hour)
}
