.PHONY: setup build test clean

setup:
	git config core.hooksPath .githooks

build:
	cargo build -p pil-rust-wasm

test: build
	target/debug/pil-python -m pytest tests/python/

clean:
	cargo clean
