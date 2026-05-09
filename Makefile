.PHONY: tidy generate migrate migrate-down run build test

tidy:
	go mod tidy

generate:
	sqlc generate

migrate:
	tern migrate --migrations sql/migrations --config tern.conf

migrate-down:
	tern migrate --migrations sql/migrations --config tern.conf --destination -1

run:
	go run .

build:
	go build -o bin/server .

test:
	go test ./...
