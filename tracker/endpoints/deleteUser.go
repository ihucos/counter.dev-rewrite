package endpoints

import (
	"net/http"

	"github.com/ihucos/counter.dev/lob"
)

func init() {
	lob.Endpoint(lob.EndpointName(), func(ctx *lob.Ctx) {
		ctx.CheckMethod("POST")
		confirmUser := ctx.R.FormValue("confirmUser")
		user := ctx.ForceUser()
		if user.Id != confirmUser {
			ctx.ReturnBadRequest("Confirmation failed")
		}
		ctx.Logout()
		err := user.DelAllSites()
		ctx.CatchError(err)
		user.Disable()
		http.Redirect(ctx.W, ctx.R, "/", http.StatusTemporaryRedirect)
	})
}
