#!/bin/sh
# Build: no-libc C -> raw image with hand-made 120-byte ELF header -> LZMA -> self-extracting shell launcher.
set -e
cd "$(dirname "$0")"
gcc -Oz -static -nostdlib -nostartfiles -fno-pic -no-pie -fno-asynchronous-unwind-tables \
    -fno-stack-protector -fomit-frame-pointer -fno-ident -fno-builtin -fno-tree-loop-distribute-patterns \
    -T src/tiny.ld -Wl,--oformat=binary,--build-id=none,--no-warn-rwx-segments \
    -o echoes.elf src/elfhdr.S src/echoes.c
chmod +x echoes.elf
xz --format=lzma --lzma1=preset=9e,lc=0,lp=0,pb=0,nice=273 -c echoes.elf > echoes.lzma
cat src/header.sh echoes.lzma > game
chmod +x game
rm -f echoes.lzma
wc -c src/header.sh echoes.elf game
