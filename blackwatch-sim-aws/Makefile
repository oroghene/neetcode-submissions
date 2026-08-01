PROTOC ?= protoc
GOBIN := $(shell go env GOPATH)/bin

.PHONY: gen build demo clean

gen:
	$(PROTOC) -Iproto \
	  --plugin=protoc-gen-go=$(GOBIN)/protoc-gen-go \
	  --plugin=protoc-gen-go-grpc=$(GOBIN)/protoc-gen-go-grpc \
	  --go_out=control-plane/gen/bwsimv1 --go_opt=paths=source_relative \
	  --go-grpc_out=control-plane/gen/bwsimv1 --go-grpc_opt=paths=source_relative \
	  bwsim.proto
	python3 -m grpc_tools.protoc -Iproto \
	  --python_out=gen/python --grpc_python_out=gen/python bwsim.proto

build:
	cd control-plane && go build -o ../bin/control-plane .

demo: build
	./scripts/demo.sh

clean:
	rm -rf bin
