import abcjs from 'abcjs';

var ANKITUNES_DONE_ATTR = 'x-ankitunes-done';

function replaceABC() {
	const elems = document.querySelectorAll<HTMLElement>('.abcSource');
	for (const sourceElem of elems) {
		const sourceId = sourceElem.id
		const abcDests = document.querySelectorAll(`.renderedAbc.${sourceId}`)!;
		if (abcDests.length > 1) {
			throw new Error('Non-unique abc destination!');
		} else if (abcDests.length == 0) {
			throw new Error('Couldn\'t find abc destination!');
		}
		const abcDest = abcDests[0] as HTMLElement;

		// if already done;
		if (abcDest.hasAttribute(ANKITUNES_DONE_ATTR)) {
			// skip
			continue;
		}

		var abc = sourceElem.innerText;

		abc = (
			abc
			.split('\n') // split lines
			.map(s => s.trim()) // trim whitespace from each line
			.filter(s => s) // exclude empty lines
			.join('\n') // rejoin
		)

		abcjs.renderAbc(abcDest, abc);

		sourceElem.style.display = 'none';
		abcDest.setAttribute(ANKITUNES_DONE_ATTR, ANKITUNES_DONE_ATTR);
	}
}

replaceABC()
