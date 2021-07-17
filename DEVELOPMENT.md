# AnkiTunes

AnkiTunes is written in Python using Anki's add-on API. Most things are done with hooks (great) and one thing is done with an inherited dialog class (not so bad) so it should be reasonably reliable.

## Contributing

Please feel free to raise PRs! If it's a behaviour change, then maybe open an issue to check with me first before spending a lot of time on something - I can be a bit pedantic on how I want things to behave.

## Dependencies

AnkiTunes has no runtime dependencies (Anki has no mechanism for this so I'd have to build my own bundling system, which I'd rather not do), but there are a few dev dependencies: these are managed with Poetry. After installing Poetry, just run

```sh
cd the/place/where/you/checked/out/ankitunes
make deps
```

You'll also need Make (use Git Bash if you're on Windows), and NodeJS and NPM (the frontend bits are built with Typescript). You can probably hack on the python stuff without needing these though.

## Running Locally

Make a symlink to this directory in `your anki profile/addons21`. The `./install_addon` script in the root of the repo will do this for you if you're on Linux (I expect Mac location will be different, and this definitely won't work on Windows.. patches welcome). Remove the Anki Add-Ons version if you've installed it previously. Run Anki.

## Building

To build the frontend, run
`make typescript`

To build the whole thing into a zip file to manually distribute, just run `make`.

## Testing

Tests are done with Pytest: to run them, run `make test` or `poetry run pytest`. All non-UI functionality should be covered with headless tests (see `tests/headless`), big features should also have a single UI journey test (`tests/ui`).

## Linting

The project is subject to two lints: tan (code formatter: black but with tabs) (sorry), and mypy (double sorry). To run checks, run `make lint`. You'll probably want to set your editor to format with `tan` (point it at `.venv/bin/tan`) on save or you'll go nuts.

## CI/CD

All commits run linting and tests against Anki 2.1.41 and Anki latest, on Linux, with CircleCI. The UI tests run with `xvfb`, this is orchestrated in-project (see the horrible `tests/ui/conftest.py` for details). You don't have to do anything here but bitch when you get a red cross on your PR.

Releases are also done by CircleCI, on any commits/merges to master.

Because everything in master goes straight to users (am I crazy??) I will be pretty anal about asking PRs to include tests.