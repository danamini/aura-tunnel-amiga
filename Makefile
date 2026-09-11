PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
VASM = bin/vasmm68k_mot

all: build/aura-tunnel-amiga.adf

build/assets.i: tools/gen_assets.py tools/runner_bodies.py tools/hires_font.py $(wildcard assets/reference/build/*) assets/reference/tools/gen_font.py assets/reference/tools/gen_ay128.py assets/reference/tools/mocap_runner.py assets/reference/assets/mocap/09_01.bvh assets/fighters/mustermann.gif
	$(PYTHON) tools/gen_assets.py

build/demo.bin: src/main.asm build/assets.i
	$(VASM) -m68000 -Fbin -quiet -L build/demo.lst -o $@ src/main.asm

build/aura-tunnel-amiga.adf: build/demo.bin src/boot.asm tools/build_disk.py
	$(PYTHON) tools/build_disk.py

emu: all
	$(PYTHON) tools/emulate.py

test: all
	$(PYTHON) tools/test_artifacts.py

setup:
	sh tools/bootstrap.sh

package: test
	$(PYTHON) tools/package.py

.PHONY: all emu test setup package
