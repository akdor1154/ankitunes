.PHONY: all
all: typescript

.PHONY: webdeps
webdeps:
	$(MAKE) -C ankitunes/web deps

.PHONY: pythondeps
pythondeps:
	poetry install

.PHONY: deps
deps: webdeps pythondeps


typescript:
	$(MAKE) -C ankitunes/web
