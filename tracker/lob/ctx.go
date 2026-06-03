package lob

import (
	"fmt"
	"io"
	"net/http"
	"runtime"
	"strconv"

	"github.com/ihucos/counter.dev/models"
)

type Ctx struct {
	W             http.ResponseWriter
	R             *http.Request
	OpenConns     []io.Closer
	App           *App
	noAutoCleanup bool
}

func (ctx *Ctx) Abort() {
	panic(ctx)
}

func (ctx *Ctx) Return(content string, statusCode int) {
	ctx.W.WriteHeader(statusCode)
	ctx.W.Write([]byte(content))
	ctx.Abort()
}

func (ctx *Ctx) Cleanup() {
	for _, conn := range ctx.OpenConns {
		err := conn.Close()
		if err != nil {
			fmt.Println("Error closing connection:", err.Error())
		}
	}
}

func (ctx *Ctx) ReturnBadRequest(message string) {
	ctx.Return(message, 400)
}

func (ctx *Ctx) ReturnInternalErrorWithSkip(err error, skip int) {
	_, file, line, _ := runtime.Caller(skip)
	ctx.App.Logger.Printf("%s:%d %s: %v\n", file, line, ctx.R.URL, err)
	ctx.Return(err.Error(), 500)
}

func (ctx *Ctx) ReturnInternalError(err error) {
	ctx.ReturnInternalErrorWithSkip(err, 2)
}

func (ctx *Ctx) CatchError(err error) {
	if err != nil {
		ctx.ReturnInternalErrorWithSkip(err, 2)
	}
}

func (ctx *Ctx) ParseUTCOffset(key string) int {

	min := func(x, y int) int {
		if x < y {
			return x
		}
		return y
	}

	max := func(x, y int) int {
		if x > y {
			return x
		}
		return y
	}

	utcOffset, err := strconv.Atoi(ctx.R.FormValue(key))
	if err != nil {
		utcOffset = 0
	}
	return max(min(utcOffset, 14), -12)
}

func (ctx *Ctx) User(userId string) models.User {
	conn := ctx.App.RedisPool.Get()
	user := models.NewUser(conn, userId, ctx.App.Config.PasswordSalt)
	ctx.OpenConns = append(ctx.OpenConns, conn)
	return user
}

func (ctx *Ctx) UserByCachedUUID(uuid string) models.User {
	conn := ctx.App.RedisPool.Get()
	user, err := models.NewUserByCachedUUID(conn, uuid, ctx.App.Config.PasswordSalt)
	ctx.CatchError(err)
	ctx.OpenConns = append(ctx.OpenConns, conn)
	return user
}

func (ctx *Ctx) NoAutoCleanup() {
	ctx.noAutoCleanup = true
}
