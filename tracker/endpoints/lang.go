package endpoints

import (
	"github.com/ihucos/counter.dev/lob"
)

func init() {
	lob.Endpoint(lob.EndpointName(), func(ctx *lob.Ctx) {
		country := ctx.R.Header.Get("CF-IPCountry")
		ctx.Return(country, 200)
	})
}
