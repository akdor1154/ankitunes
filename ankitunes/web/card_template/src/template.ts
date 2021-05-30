import abcjs from 'abcjs';

function replaceABC() {
	const _abcElem = document.getElementById('abcSource')!;
	var _abc = _abcElem.innerText;
	_abc = _abc.split('\n').map(s => s.trim()).filter(s => s).join('\n')

	const abcDest = document.getElementById('renderedAbc')!;
	abcjs.renderAbc(abcDest, _abc);
	_abcElem.style.display = 'none';
}

replaceABC()
