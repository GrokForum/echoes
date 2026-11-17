/* Minimal 64-bit ELF header + single PT_LOAD program header (120 bytes). */
.section .hdr,"ax"
.globl __ehdr
__ehdr:
 .byte 0x7f,'E','L','F',2,1,1,0
 .quad 0
 .short 2,62            /* ET_EXEC, x86-64 */
 .long 1
 .quad _start           /* e_entry */
 .quad 64               /* e_phoff */
 .quad 0                /* e_shoff */
 .long 0
 .short 64,56,1,0,0,0   /* ehsize, phentsize, phnum, shentsize, shnum, shstrndx */
 /* Phdr */
 .long 1,7              /* PT_LOAD, RWX */
 .quad 0                /* offset */
 .quad __ehdr,__ehdr    /* vaddr, paddr */
 .quad __filesz,__memsz
 .quad 0x1000
