
# Unit Testing Input Binary

This project includes a minimal binary used for unit testing, based on a simple assembly file called `tiny.asm`.

If you need to modify this binary (e.g., to cover new edge cases), simply update `tiny.asm` and follow the steps below to regenerate the byte dump used in tests.

---

## Rebuilding the Test Binary

To compile the test binary from the assembly source:

1. Assemble using **NASM**:
   ```bash
   nasm -f elf64 tiny.asm -o test.bin
   ```
---

## Adding Test Binary to Tests

Once the `test.bin` file is ready, just replace the test.bin under `resources` folder with the new one
