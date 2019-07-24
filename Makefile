BUILD_NUMBER:=latest
SERVICE_NAME:=monitor
TEMPLATE_NAME:=$(SERVICE_NAME)-template:$(BUILD_NUMBER)


build: build-template build-rest build-checker


build-template:
	docker build docker_image/docker_template \
      -t $(TEMPLATE_NAME) \
      --build-arg TIME=$(shell date +%s)


build-checker:
	docker build docker_image/docker_checker \
	  -t monitor-checker:$(BUILD_NUMBER)


build-rest:
	docker build docker_image/docker_rest \
	  -t monitor-rest:$(BUILD_NUMBER)