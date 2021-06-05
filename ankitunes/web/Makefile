.PHONY: all
all: typescript snowpack

.PHONY: typescript
typescript:
	npm run tsc

.PHONY: snowpack
snowpack:
	$(MAKE) -C card_template

deps:
	npm ci
