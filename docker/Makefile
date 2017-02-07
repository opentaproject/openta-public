port ?= 8000

.PHONY : all clean watch serve image check

all: serve

check:
	@if ! ( docker images | grep -q openta ); then echo "You need to build the docker image first using 'make image'" && exit 1; fi

clean:
	@docker rmi openta
	
watch: check
	@docker run --rm -p 127.0.0.1:${port}:8000 -v ${CURDIR}/..:/openta -i -t openta

serve: check
	@docker run --rm -p 127.0.0.1:${port}:8000 -i -t openta

image:
	@docker build -f Dockerfile -t openta ..

