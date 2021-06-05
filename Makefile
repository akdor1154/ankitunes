.PHONY: all
all: build

.PHONY: webdeps
webdeps:
	$(MAKE) -C ankitunes/web deps

.PHONY: pythondeps
pythondeps:
	poetry install

.PHONY: deps
deps: webdeps pythondeps

.PHONY: typescript
typescript:
	$(MAKE) -C ankitunes/web

.PHONY: build
build: dist/ankitunes.ankiaddon

dist/ankitunes.ankiaddon: typescript
	rm -rf dist/*
	poetry build
	mkdir dist/wheel
	cd dist/wheel; unzip ../ankitunes-*.whl
	cd dist/wheel/ankitunes; zip -r ../../ankitunes.ankiaddon *
