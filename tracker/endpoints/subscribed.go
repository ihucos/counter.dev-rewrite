package endpoints

import (
	"github.com/ihucos/counter.dev/lob"
)

func init() {
	lob.Endpoint(lob.EndpointName(), func(ctx *lob.Ctx) {
		subID := ctx.R.FormValue("subscription_id")
		user := ctx.ForceUser()
		err := user.RegisterSubscriptionID(subID)
		ctx.CatchError(err)
	})
}
