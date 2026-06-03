package endpoints

import "github.com/ihucos/counter.dev/lob"

func init() {
	lob.Endpoint(lob.EndpointName(), func(ctx *lob.Ctx) {
		user := ctx.ForceUser()
		err := user.DeleteToken()
		ctx.CatchError(err)
		user.Signal()
	})
}
