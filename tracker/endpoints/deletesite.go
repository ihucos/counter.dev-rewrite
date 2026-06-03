package endpoints

import "github.com/ihucos/counter.dev/lob"

func init() {
	lob.Endpoint(lob.EndpointName(), func(ctx *lob.Ctx) {
		user := ctx.ForceUser()
		site := ctx.R.FormValue("site")
		confirmSite := ctx.R.FormValue("confirmSite")
		if site != confirmSite {
			ctx.ReturnBadRequest("Confirmation failed")
		}
		err := user.NewSite(site).Del()
		ctx.CatchError(err)
		deleted, err := user.DelSiteLink(site)
		ctx.CatchError(err)
		if !deleted {
			ctx.ReturnBadRequest("Logged in user does not have such a site")
		}
		user.Signal()
	})
}
