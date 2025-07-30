
# Unit Testing Input Binary

This project includes a minimal binary used for unit testing, based on a simple assembly file called `tiny.asm`.

If you need to modify this binary (e.g., to cover new edge cases), simply update `tiny.asm` and follow the steps below to regenerate the byte dump used in tests.

---

## Rebuilding the Test Binary

To compile the test binary from the assembly source:

1. Assemble using **NASM**:
   ```bash
   nasm -f elf64 tiny.asm -o tiny.o
   ```

2. (Optional) Link the object file using **ld**:
   ```bash
   ld tiny.o -o tiny
   ```
---

## Generating a Binary Dump for Tests

Once the `tiny.o` file is ready, convert it into a raw binary dump using the provided script:

```bash
python3 dumpbin.py tiny.o
```

This will output a byte array that you need to copy/paste in both the C++ and Python unit test suites.
