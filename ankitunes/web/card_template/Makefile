default: tsc bundle

tsc:
	../node_modules/.bin/tsc -noEmit

bundle:
	../node_modules/.bin/esbuild \
		--bundle \
		--outfile=../dist/card_template/template.js \
		--sourcemap \
		--minify=false \
		src/template.ts
