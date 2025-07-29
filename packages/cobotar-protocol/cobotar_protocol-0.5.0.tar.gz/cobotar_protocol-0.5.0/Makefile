#==================================================================================== #
# HELPERS
#==================================================================================== #

## help: print this help message
.PHONY: help
help:
	@echo 'Usage:'
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' |  sed -e 's/^/ /'

.PHONY: confirm
confirm:
	@echo -n 'Are you sure? [y/N] ' && read ans && [ $${ans:-N} = y ]

#==================================================================================== #
# BUF Commands
#==================================================================================== #

## lint: run the buf lint command
.PHONY: lint
lint:
	buf lint

## format: run the buf format command
.PHONY: format
format:
	buf format -d -w

## breaking: run the buf breaking command
.PHONY: breaking
breaking:
	buf breaking --against ".git#branch=main"

## generate: run the buf generate command
.PHONY: generate
generate:
	buf generate

## verify: run lint, format, breaking, and generate command
.PHONY: verify
verify: format lint breaking generate
	@echo 'Remember to check if new files were created!'

## publish bump=$1: run checks, bump version, and publish
.PHONY: publish
publish: verify
	@echo 'Verification complete'
	bump-my-version bump ${bump}
	git push
	git push --tags
	@echo 'New version is published'
