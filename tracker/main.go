package main

import (
	_ "github.com/ihucos/counter.dev/endpoints"
	"github.com/ihucos/counter.dev/lob"
)

func main() {
	app := lob.NewApp()
	app.ConnectEndpoints()
	app.Logger.Println("Start")
	app.Serve()
}
