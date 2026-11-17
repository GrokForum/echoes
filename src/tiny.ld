ENTRY(_start)
SECTIONS {
  . = 0x400000;
  .all : { KEEP(*(.hdr)) *(.text*) *(.rodata*) *(.data*) }
  __filesz = . - 0x400000;
  .bss (NOLOAD) : { *(.bss*) *(COMMON) }
  __memsz = . - 0x400000;
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
