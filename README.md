# Everyday Scripts

A collection of small scripts for personal media workflows.

## Usage with Docker

Build the runtime image and run any script inside the container. Docker works on Linux, macOS and Windows.

```bash
# build image
docker build -t everyday-scripts .

# Linux / macOS
docker run --rm -v "$PWD":/work everyday-scripts \
  python3 /work/scripts/make_shuffle_clips/make_shuffle_clips.py --help

# Windows PowerShell
docker run --rm -v ${PWD}:/work everyday-scripts \
  python3 /work/scripts/make_shuffle_clips/make_shuffle_clips.py --help
```

## Development

Use the dev container to run formatting and test checks. Locally you can
execute:

```bash
./check.sh
```

The `agents-check.sh` helper installs the required tooling and runs the same
checks in a clean environment.

## License

MIT
