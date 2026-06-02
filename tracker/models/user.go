package models

import (
	"fmt"

	"github.com/gomodule/redigo/redis"
)

func truncate(stri string) string {
	if len(stri) > truncateAt {
		return stri[:truncateAt]
	}
	return stri
}

type User struct {
	redis        redis.Conn
	Id           string
	passwordSalt string
}

func NewUser(conn redis.Conn, userId string, passwordSalt []byte) User {
	return User{redis: conn, Id: truncate(userId), passwordSalt: string(passwordSalt)}
}

func (user User) NewSite(Id string) Site {
	return Site{redis: user.redis, userId: user.Id, id: Id}
}

func (user User) IncrSiteLink(siteId string) {
	user.redis.Send("HINCRBY", fmt.Sprintf("sites:%s", user.Id), siteId, 1)
}

func (user User) Signal() {
	user.redis.Send("PUBLISH", fmt.Sprintf("user:%s", user.Id), "")
}
