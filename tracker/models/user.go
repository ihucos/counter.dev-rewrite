package models

import (
	"crypto/sha256"
	"fmt"

	"github.com/gomodule/redigo/redis"
)

var uuid2id = map[string]string{}

type User struct {
	redis        redis.Conn
	Id           string
	passwordSalt string
}

func hash(stri string) string {
	h := sha256.Sum256([]byte(stri))
	return string(h[:])
}

const truncateAt = 256

func truncate(stri string) string {
	if len(stri) > truncateAt {
		return stri[:truncateAt]
	}
	return stri
}

func NewUser(conn redis.Conn, userId string, passwordSalt string) User {
	return User{redis: conn, Id: truncate(userId), passwordSalt: passwordSalt}
}

func NewUserByCachedUUID(conn redis.Conn, uuid string, passwordSalt string) (User, error) {
	var err error
	var id string
	var ok bool
	id, ok = uuid2id[uuid]
	if !ok {
		// hit the redis db
		id, err = redis.String(conn.Do("HGET", "uuid2id", uuid))
		if err == redis.ErrNil {
			return User{}, fmt.Errorf("No such user with uuid: %s", uuid)
		} else if err != nil {
			return User{}, err
		}

		// cache the value in memory
		uuid2id[uuid] = id
	}
	return NewUser(conn, id, passwordSalt), nil
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
