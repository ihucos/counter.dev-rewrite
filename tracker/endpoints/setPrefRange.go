package endpoints

import "github.com/ihucos/counter.dev/lob"

func init() {
	lob.Endpoint(lob.EndpointName(), func(ctx *lob.Ctx) {
		ctx.SetPref("range", ctx.R.URL.RawQuery)

	})
}
