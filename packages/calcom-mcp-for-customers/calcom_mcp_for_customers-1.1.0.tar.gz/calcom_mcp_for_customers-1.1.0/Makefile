.PHONY: install build clean lock publish

install:
	uv pip install -e .

build:
	uv build

lock:
	uv pip compile pyproject.toml

clean:
	rm -rf dist/ *.egg-info __pycache__ build/ uv.lock

publish:
	uv publish --token $$(cat .pypi_token)