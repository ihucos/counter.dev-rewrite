package models

import (
	"fmt"

	"github.com/gomodule/redigo/redis"
	"gorm.io/gorm"
)

// uuid2id is a simple in-memory cache mapping UUIDs to user IDs
var uuid2id = map[string]string{}

type User struct {
	redis        redis.Conn
	db           *gorm.DB
	Id           string
	passwordSalt string
}

func NewUser(conn redis.Conn, userId string, db *gorm.DB, passwordSalt []byte) User {
	return User{redis: conn, Id: userId, passwordSalt: string(passwordSalt), db: db}
}

func NewUserByCachedUUID(conn redis.Conn, uuid string, db *gorm.DB, passwordSalt []byte) (User, error) {
	var err error
	var id string
	var ok bool
	id, ok = uuid2id[uuid]
	if !ok {
		id, err = redis.String(conn.Do("HGET", "uuid2id", uuid))
		if err == redis.ErrNil {
			return User{}, fmt.Errorf("No such user with uuid: %s", uuid)
		} else if err != nil {
			return User{}, err
		}

		uuid2id[uuid] = id
	}
	return NewUser(conn, id, db, passwordSalt), nil
}

func (user User) NewSite(Id string) Site {
	return Site{redis: user.redis, userId: user.Id, id: Id, db: user.db}
}

func (user User) IncrSiteLink(siteId string) {
	user.redis.Send("HINCRBY", fmt.Sprintf("sites:%s", user.Id), siteId, 1)
}

func (user User) Signal() {
	user.redis.Send("PUBLISH", fmt.Sprintf("user:%s", user.Id), "")
}
