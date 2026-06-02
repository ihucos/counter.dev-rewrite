package endpoints

import (
	"github.com/ihucos/counter.dev/lib"
	"github.com/ihucos/counter.dev/models"
	"github.com/ihucos/counter.dev/utils"
)

func init() {
	lib.Endpoint(lib.EndpointName(), func(ctx *lib.Ctx) {
		visit := make(models.Visit)

		user, err := ctx.UserByCachedUUID(ctx.R.FormValue("id"))
		if err != nil {
			ctx.ReturnBadRequest(err.Error())
		}
		now := utils.TimeNow(ctx.ParseUTCOffset("utcoffset"))

		visit["page"] = ctx.R.FormValue("page")
		visit["count"] = "pageview"

		origin := ctx.R.Header.Get("Origin")
		if origin == "" || origin == "null" {
			ctx.ReturnBadRequest("Origin header can not be empty, not set or \"null\"")
		}
		siteId := Origin2SiteId(origin)
		visits := user.NewSite(siteId)
		visits.SaveVisit(visit, now)

		ctx.W.Header().Set("Access-Control-Allow-Origin", "*")

		ctx.Return("", 204)

	})
}
