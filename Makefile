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
	mkdir dist/addon
	cd dist/addon; unzip ../ankitunes-*.whl
	cp ankiweb_manifest.json dist/addon/ankitunes/manifest.json
	cd dist/addon/ankitunes; zip -r ../../ankitunes.ankiaddon *
