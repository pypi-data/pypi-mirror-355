import sys


def dump_binary_as_c_array(file_path, array_name='binary_data'):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return

    print(f'static unsigned char {array_name}[] = {{')

    # Print hex values in a formatted way, adjust ROW_SIZE if you need
    ROW_SIZE = 40
    for i, byte in enumerate(data):
        if i % ROW_SIZE == 0:
            print('    ', end='')  # Indent for readability
        print(f'0x{byte:02x},', end='')
        if (i + 1) % ROW_SIZE == 0 or i == len(data) - 1:
            print()

    print('};')
    print(f'const unsigned int {array_name}_len = {len(data)};')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 dumpbin.py <binary_file>')
    else:
        dump_binary_as_c_array(sys.argv[1])
