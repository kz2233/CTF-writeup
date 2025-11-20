# Initial finding 
At the beginning i am trying to udnerstand what does the program do with my input

<pre>
v9 = 0;
  while ( v9 <= 27 )
  {
    printf("> ");
    do
      v8 = getchar();
    while ( v8 == 10 );
    switch ( v8 )
    {
      case 'w':
        --byte_555555558051;
        v3 = off_555555558038;
        off_555555558038 = (_UNKNOWN *)((char *)off_555555558038 + 1);
        *v3 = 0;
        goto LABEL_12;
      case 'a':
        --byte_555555558050;
        v4 = off_555555558038;
        off_555555558038 = (_UNKNOWN *)((char *)off_555555558038 + 1);
        *v4 = 1;
        goto LABEL_12;
      case 's':
        ++byte_555555558051;
        v5 = off_555555558038;
        off_555555558038 = (_UNKNOWN *)((char *)off_555555558038 + 1);
        *v5 = 2;
        goto LABEL_12;
      case 'd':
        ++byte_555555558050;
        v6 = off_555555558038;
        off_555555558038 = (_UNKNOWN *)((char *)off_555555558038 + 1);
        *v6 = 3;
LABEL_12:
        byte_555555558050 &= 7u;
        byte_555555558051 &= 7u;
        byte_555555558010[(unsigned __int8)byte_555555558051] ^= 1 << byte_555555558050;
        ++v9;
        break;
    }
  }
</pre>

From it takes my input either w, a, s or d, and interpret them into position 8050 and 8051 like the graph (x,y)

w = down

a = left 

s = up 

d = right

seemingly to be an upside-down grid

there is 2 interesting line here 

<pre>
byte_555555558050 &= 7u;
byte_555555558051 &= 7u;
</pre>

Turning the 8x8 grid into a Toroidal Geometry (a donut shape).
1. If you are at **x=7** and move right (d), you wrap to **x=0**.
2. If you are at **x=0** and move left (a), you wrap to **x=7**.
3. The same applies vertically for **y=7** and **y=0**.

ALSO, when each input is done, it updates the array in 8010 by this line of code (the 8010 array is predefined)

<pre>
.data:0000555555558010 unk_555555558010 db  8Bh                ; DATA XREF: main+12E↑o
.data:0000555555558010                                         ; main+162↑o ...
.data:0000555555558011                 db 0C9h
.data:0000555555558012                 db  92h
.data:0000555555558013                 db    8
.data:0000555555558014                 db 0F9h
.data:0000555555558015                 db  91h
.data:0000555555558016                 db 0D6h
.data:0000555555558017                 db 0C8h
</pre>
(this can be seen in IDA via View > Open SubView > Disassembly)

C:
<pre>
byte_555555558010[(unsigned __int8)byte_555555558051] ^= 1 << byte_555555558050;
</pre>

Python:
<pre>
lava_map[current_y] ^= (1 << current_x)
</pre>

## Detailed Breakdown

The line lava_map[current_y] ^= (1 << current_x) consists of three distinct steps:

1. The Bit Shift (1 << current_x)

    This creates a Bitmask.
    It takes the number 1 (binary ...0001) and shifts it to the left by x positions.
    
    If x = 0: 0000 0001
    
    If x = 2: 0000 0100
    
    If x = 7: 1000 0000

2. The Selection (lava_map[current_y])

    The code uses the Y-coordinate as an index into an array. In an 8x8 grid implemented with bytes, every byte represents a specific Row.

3. The XOR Operation (^=)

    The ^ (Exclusive OR) operator compares the current row's bits with the mask.
    
    0 ^ 1 = 1 (Flips 0 to 1)
    
    1 ^ 1 = 0 (Flips 1 to 0)
    
    X ^ 0 = X (Unchanged)

Since our mask only has a 1 at the specific x column, only that specific cell is flipped.


# Verification part 
this is the part of code I find that determine that "I fell into lava"
<pre>
  for ( i = 0; i <= 7; ++i )
  {
    srand(4919 * i - 559038737);
    if ( (unsigned __int8)rand() != byte_555555558010[i] )
    {
      puts("you fell into lava");
      return 0;
    }
  }
</pre>

This piece of code is done after the 28 input of the program

It uses the value from 0 to 7 in each iteration to generate a seed with srand, which then use with rand() for Random Number Generation (RNG)

but this value generate everytime the program re-run will actually be the same due the fixed seed generated 

and most important is that it is checked one by one during runtime


# How to actually solve it?
Since the program generate the CORRECT answer for comparison with rand(), so I can firstly find what is generated from the loop in "Verification part":

<pre>
Correct Lava Map Values (Hex):
------------------------------
Row 0: 0xE1
Row 1: 0xE7
Row 2: 0xA2
Row 3: 0xD1
Row 4: 0xB6
Row 5: 0xE1
Row 6: 0xCA
Row 7: 0xC4
</pre>
(this is the output from the code "generator.py")             


## Calculation
Since the final once are already revealed, and it is known that the transforming of initial byte to final byte is done with bit shift

we can use XOR difference to identify which position is being shifted, for example:

from 8B to E1 at the first position of the array

<pre>
Row 0 (Y = 0): 
  8B XOR E1 = 6A
  6A = 01101010

Position flipped:
  1, 3, 5, 6

Forming the position: 
  (1, 0), (3, 0), (5, 0), (6, 0)

Row 1 (Y = 0): 
  C9 XOR E7 = 2E
  2E = 00101110

Position flipped:
  1, 2, 3, 5

Forming the position: 
  (1, 1), (2, 1), (3, 1), (5, 1)
  
</pre> 

After getting all the coordinate by using XOR difference and finding the bit shifted, it shows these coordinate 

[(1, 0), (3, 0), (5, 0), (6, 0), (1, 1), (2, 1), (3, 1), (5, 1), (4, 2), (5, 2), (0, 3), (3, 3), (4, 3), (6, 3), (7, 3), (0, 4), (1, 4), (2, 4), (3, 4), (6, 4), (4, 5), (5, 5), (6, 5), (2, 6), (3, 6), (4, 6), (2, 7), (3, 7)]

<pre>
y\x  0 1 2 3 4 5 6 7
0:   · █ · █ · █ █ ·
1:   · █ █ █ · █ · ·
2:   · · · · █ █ · ·
3:   █ · · █ █ · █ █
4:   █ █ █ █ · · █ ·
5:   · · · · █ █ █ ·
6:   · · █ █ █ · · ·
7:   · · █ █ · · · ·

y\x  0  1  2  3  4  5  6  7
0:   .. 01 .. 05 .. 27 28 ..
1:   .. 02 03 04 .. 26 .. ..
2:   .. .. .. .. 24 25 .. ..
3:   17 .. .. 22 23 .. 15 16
4:   18 19 20 21 .. .. 14 ..
5:   .. .. .. .. 11 12 13 ..
6:   .. .. 08 09 10 .. .. ..
7:   .. .. 07 06 .. .. .. ..
</pre>

by highlighting out the correct path and since this is a "Toroidal Geometry", starting from (0, 0), it ends at (6, 0)

forming the path: dsddwwawddwddwwddsdddwdwdwwd

after entering the path, the flag is revealed

Flag: amateursCTF{l4va_r3v_05f0d4ff51fb}
