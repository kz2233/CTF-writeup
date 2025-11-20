import ctypes
import time
import sys

# Load libc to replicate the C-style rand() exactly
libc = ctypes.CDLL("libc.so.6")

# --- DATA EXTRACTION ---
# Source: .data:0000555555558010
# Note: While the array is 28 bytes long, the Y-coordinate is masked by 7.
# This means user input ONLY modifies the first 8 bytes (indices 0-7).
# We only need to solve for these first 8 bytes.
initial_map_bytes = [
    0x8B, 0xC9, 0x92, 0x08, 0xF9, 0x91, 0xD6, 0xC8
]

# Source: .data:0000555555558020
encrypted_flag = [
    0xD6, 0xB2, 0x05, 0x20, 0x95, 0x5B, 0x1A, 0xBE,
    0x4E, 0x70, 0x5F, 0x60, 0xF9, 0x74, 0x51, 0xEE,
    0x69, 0x56, 0x8C, 0x6A, 0xC1
]

# --- STEP 1: CALCULATE TARGET STATE ---
target_map_bytes = []
# We only care about the first 8 bytes for the solver because
# the game logic limits Y coordinates to 0-7.
# Indices 8-27 are static checks that must pass automatically.
for i in range(8):
    seed_val = (i * 0x1337) - 0x21524111
    libc.srand(ctypes.c_uint(seed_val))
    rand_byte = libc.rand() & 0xFF
    target_map_bytes.append(rand_byte)

# --- STEP 2: DETERMINE REQUIRED VISITS (XOR MAP) ---
required_flips = {} 
for y in range(8):
    initial = initial_map_bytes[y]
    target = target_map_bytes[y]
    diff = initial ^ target
    
    for x in range(8):
        # Check if the bit at column x is flipped
        if (diff >> x) & 1:
            required_flips[(x, y)] = True

print(f"[+] Required Coordinate Flips: {len(required_flips)}")
print(f"[+] Target bits to flip: {[k for k in required_flips.keys()]}")

# --- STEP 3: PATHFINDING (DFS) ---
moves_map = {
    0: (0, -1), # w (y-1)
    1: (-1, 0), # a (x-1)
    2: (0, 1),  # s (y+1)
    3: (1, 0)   # d (x+1)
}

# Global counters for progress tracking
visited_nodes = 0
start_time = time.time()

def print_progress(depth, steps_remaining, current_flips):
    global visited_nodes, start_time
    visited_nodes += 1
    
    if visited_nodes % 200000 == 0:
        elapsed = time.time() - start_time
        speed = visited_nodes / elapsed
        sys.stdout.write(
            f"\r[INFO] Depth: {28 - steps_remaining:02d}/28 | "
            f"Remaining Flips: {len(current_flips):02d} | "
            f"Nodes: {visited_nodes:,} | "
            f"Speed: {speed:.0f} nodes/sec"
        )
        sys.stdout.flush()

def solve_path(current_x, current_y, steps_remaining, current_flips, path_history):
    # Progress Tracker
    print_progress(len(path_history), steps_remaining, current_flips)

    # PRUNING OPTIMIZATION: 
    # If we have more bits to flip than steps remaining, this branch is impossible.
    # (One step can flip at most one bit).
    if len(current_flips) > steps_remaining:
        return None

    # Base Case: No steps left
    if steps_remaining == 0:
        if not current_flips:
            return path_history
        return None
    
    # Prioritize moves that hit a required flip (Heuristic)
    # We create a list of moves, sorting "good" moves first to find the solution faster
    candidate_moves = []
    for move_val, (dx, dy) in moves_map.items():
        nx, ny = (current_x + dx) & 7, (current_y + dy) & 7
        is_needed = (nx, ny) in current_flips
        candidate_moves.append((is_needed, move_val, nx, ny))
    
    # Sort so moves that flip a needed bit are checked first (True > False)
    candidate_moves.sort(key=lambda x: x[0], reverse=True)

    for _, move_val, nx, ny in candidate_moves:
        # Update flip state
        new_flips = current_flips.copy()
        coord = (nx, ny)
        
        if coord in new_flips:
            del new_flips[coord] # We fixed this bit
        else:
            new_flips[coord] = True # We toggled a bit that didn't need it (oops) or un-fixed it
            
        result = solve_path(nx, ny, steps_remaining - 1, new_flips, path_history + [move_val])
        if result:
            return result
    
    return None

print("\n[*] Calculating path... (Pruning enabled)")
valid_path = solve_path(0, 0, 28, required_flips, [])
print("\n") # Newline after progress bar

if not valid_path:
    print("[-] No path found.")
    exit()

# Convert numeric moves back to 'wasd' for display
move_chars = {0: 'w', 1: 'a', 2: 's', 3: 'd'}
path_str = "".join([move_chars[m] for m in valid_path])
print(f"[+] Path Found: {path_str}")

# --- STEP 4: DECRYPT THE FLAG ---
accumulator = 0
for move in valid_path:
    accumulator = (accumulator << 2) | move

lower_32 = accumulator & 0xFFFFFFFF
upper_32 = (accumulator >> 32) & 0xFFFFFFFF
decryption_seed = lower_32 ^ upper_32

print(f"[+] Decryption Seed: {decryption_seed}")

libc.srand(ctypes.c_uint(decryption_seed))
decrypted_chars = []

for enc_byte in encrypted_flag:
    key_byte = libc.rand() & 0xFF
    decrypted_chars.append(chr(enc_byte ^ key_byte))

print(f"\n[SUCCESS] Flag: amateursCTF{{{''.join(decrypted_chars)}}}")
