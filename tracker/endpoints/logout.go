package endpoints

import (
	"net/http"

	"github.com/ihucos/counter.dev/lob"
)

func init() {
	lob.Endpoint(lob.EndpointName(), func(ctx *lob.Ctx) {
		ctx.Logout()
		next := ctx.R.FormValue("next")
		var redirectURL string
		if next == "login" {
			redirectURL = "/welcome.html?sign-in"
		} else {
			redirectURL = "/"
		}
		http.Redirect(ctx.W, ctx.R, redirectURL, http.StatusTemporaryRedirect)
	})
}
