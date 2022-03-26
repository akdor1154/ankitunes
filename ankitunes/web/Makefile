.PHONY: all
all: typescript card_template

.PHONY: typescript
typescript:
	npm run tsc

.PHONY: card_template
card_template:
	$(MAKE) -C card_template

.PHONY: deps
deps:
	npm ci

.PHONY: clean
clean:
	rm -r dist
