#!/bin/sh
# Build tools only. FS-UAE is installed separately.
set -eu
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p bin build/toolchain
if [ ! -d build/toolchain/vasm/.git ]; then
    git clone https://github.com/StarWolf3000/vasm-mirror.git build/toolchain/vasm
fi
git -C build/toolchain/vasm checkout --detach a13e7e728a3dd5a9ba468bf479119e0bc23e70fd
make -C build/toolchain/vasm CPU=m68k SYNTAX=mot
cp build/toolchain/vasm/vasmm68k_mot bin/vasmm68k_mot
