.PHONY: install build clean lock publish

install:
	uv pip install -e .

build:
	uv build

lock:
	uv pip compile

clean:
	rm -rf dist/ *.egg-info __pycache__ build/ uv.lock

publish:
	uv publish --token $$(cat .pypi_token)