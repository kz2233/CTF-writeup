import ctypes
import sys

def generate_safe_values():
    # The binary appears to be a Linux executable (based on 0x55.. addresses).
    # C's rand() implementation varies by OS. We use ctypes to use the 
    # system's native C library to ensure the numbers match the binary.
    
    libc = None
    if sys.platform.startswith('linux'):
        try:
            libc = ctypes.CDLL("libc.so.6")
        except OSError:
            print("Could not load libc.so.6")
    elif sys.platform == 'darwin': # Mac
        try:
            libc = ctypes.CDLL("libc.dylib")
        except OSError:
            print("Could not load libc.dylib")
    elif sys.platform == 'win32':
        # Warning: Windows rand() is different from Linux rand().
        # If the target binary is Linux, running this on Windows will yield WRONG results.
        try:
            libc = ctypes.CDLL("msvcrt")
            print("WARNING: Running on Windows. If the target binary is Linux, these values might be wrong.")
        except OSError:
            print("Could not load msvcrt")

    if not libc:
        print("Error: Could not load C library.")
        return

    print("Correct Lava Map Values (Hex):")
    print("------------------------------")

    # The loop from the code snippet
    for i in range(8):
        # Calculate the seed: 4919 * i - 559038737
        # We mask with 0xFFFFFFFF to ensure it behaves like a 32-bit C integer
        # (Handling negative number representation correctly)
        seed = (4919 * i - 559038737) & 0xFFFFFFFF
        
        # Set the seed
        libc.srand(seed)
        
        # Generate the number
        random_val = libc.rand()
        
        # Cast to unsigned __int8 (byte) just like the C code
        byte_val = random_val & 0xFF
        
        # Print in 2-digit HEX format (1 byte)
        print(f"Row {i}: 0x{byte_val:02X}")

if __name__ == "__main__":
    generate_safe_values()
