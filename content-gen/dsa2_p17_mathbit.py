from dsa2_common import P

INTRO = r"""
Math and bit-manipulation questions are usually short, but they test whether you know a handful of tricks. Learn the tricks once and these become free points.

**Bit operators in Java**
- `&` AND, `|` OR, `^` XOR, `~` NOT, `<<` left shift, `>>` arithmetic right shift (keeps sign), `>>>` logical right shift (fills with 0 — use it for unsigned logic).

**Tricks worth memorising**
```java
x ^ x == 0;  x ^ 0 == x;          // XOR cancels pairs → find the odd one out
(x >> i) & 1                       // i-th bit of x
x | (1 << i)                       // set bit i
x & ~(1 << i)                      // clear bit i
x & (x - 1)                        // drop the lowest set bit (count bits, power of 2 check)
x & (-x)                           // isolate the lowest set bit
Integer.bitCount(x)                // library popcount (know how to write it yourself)
```
**Power of two:** `x > 0 && (x & (x - 1)) == 0`.

**How to recognize bit problems**
- "Every element appears twice except one" → XOR.
- "Without using + or −" → XOR for sum-without-carry, AND<<1 for carry.
- "Count set bits for every number 0..n" → DP on bits: `bits[i] = bits[i >> 1] + (i & 1)`.

**Math patterns**
- **Fast exponentiation**: `x^n = (x^(n/2))^2`, multiply an extra x when n is odd → O(log n).
- **Gauss sum** `n(n+1)/2` to find a missing number (or XOR to avoid overflow).
- **Cycle detection on numbers** (Happy Number) → Floyd's slow/fast pointers or a HashSet.
- **Digit manipulation**: `x % 10` gives the last digit, `x / 10` drops it; carry handling for array-of-digits addition.

**Pitfalls**
- `n = Integer.MIN_VALUE`: `-n` overflows. Convert to `long` first (Pow(x, n)).
- Java has no unsigned int: use `>>>` and treat the value as raw 32 bits (Reverse Bits).
- Operator precedence: `x & 1 == 0` parses as `x & (1 == 0)` — always parenthesise `(x & 1) == 0`.
"""

PROBLEMS = [
P("single-number", "Single Number", "Easy", ["Amazon", "Google", "Microsoft", "Adobe", "Paytm"],
"""Every element in a non-empty array appears twice except for one. Find that one in linear time and constant extra space. `[4,1,2,1,2]` → 4.""",
"""**Brute force:** HashMap of counts → O(n) space. Sorting → O(n log n).

**Key insight — XOR:** `a ^ a = 0` and `a ^ 0 = a`, and XOR is commutative/associative. XOR-ing all numbers cancels every pair, leaving the single number. O(n) time, O(1) space.""",
r"""
class Solution {
    public int singleNumber(int[] nums) {
        int x = 0;
        for (int v : nums) x ^= v;
        return x;
    }
}
""", "O(n)", "O(1)", True),

P("counting-bits", "Counting Bits", "Easy", ["Amazon", "Google", "Microsoft", "Adobe"],
"""For every number i from 0 to n, return how many 1 bits it has in binary. n = 5 → `[0,1,1,2,1,2]`.""",
"""**Naive:** popcount each number → O(n log n).

**DP on bits (O(n)):** `i >> 1` is i with its last bit removed, and we've already computed it. So `bits[i] = bits[i >> 1] + (i & 1)`.

Equivalent recurrence: `bits[i] = bits[i & (i − 1)] + 1` (drop the lowest set bit).""",
r"""
class Solution {
    public int[] countBits(int n) {
        int[] bits = new int[n + 1];
        for (int i = 1; i <= n; i++) {
            bits[i] = bits[i >> 1] + (i & 1);
        }
        return bits;
    }
}
""", "O(n)", "O(1) extra (output excluded)", False),

P("number-of-1-bits", "Number of 1 Bits", "Easy", ["Amazon", "Microsoft", "Oracle", "Adobe"],
"""Return the number of set bits (1s) in the binary representation of a positive integer (the Hamming weight). 11 = `1011` → 3.""",
"""**Approach 1:** check the last bit with `n & 1` and shift right 32 times.

**Approach 2 (Brian Kernighan):** `n & (n − 1)` clears the lowest set bit. Loop until n becomes 0; the number of iterations equals the number of set bits — faster when few bits are set. Use `!= 0` (not `> 0`) so it also works if the sign bit is set.""",
r"""
class Solution {
    public int hammingWeight(int n) {
        int count = 0;
        while (n != 0) {
            n &= (n - 1); // drop lowest set bit
            count++;
        }
        return count;
    }
}
""", "O(number of set bits) ≤ O(32)", "O(1)", False),

P("reverse-bits", "Reverse Bits", "Easy", ["Amazon", "Microsoft", "Oracle", "Adobe"],
"""Reverse the order of the 32 bits of a given integer (treat it as unsigned). The bit at position 0 moves to position 31, position 1 to 30, and so on.""",
"""Build the result bit by bit, 32 times: shift `result` left to make room, OR in the lowest bit of n (`n & 1`), then shift n right with **`>>>`** so the sign bit doesn't get copied in.

Follow-up (called many times): cache reversed values for each byte and combine four lookups.""",
r"""
public class Solution {
    // you need treat n as an unsigned value
    public int reverseBits(int n) {
        int result = 0;
        for (int i = 0; i < 32; i++) {
            result = (result << 1) | (n & 1);
            n >>>= 1;
        }
        return result;
    }
}
""", "O(1) (32 iterations)", "O(1)", False),

P("missing-number", "Missing Number", "Easy", ["Amazon", "Microsoft", "Google", "Oracle", "Paytm"],
"""An array contains n distinct numbers taken from `0..n`, so exactly one value in that range is missing. Find it. `[3,0,1]` → 2.""",
"""**Approach 1 — Gauss:** expected sum `n(n+1)/2` minus actual sum.

**Approach 2 — XOR (no overflow risk):** XOR all indices `0..n` with all values. Every present number cancels with its index, leaving the missing one.

Both O(n) time, O(1) space. (Sorting or a HashSet also work but are worse.)""",
r"""
class Solution {
    public int missingNumber(int[] nums) {
        int x = nums.length; // include n itself
        for (int i = 0; i < nums.length; i++) {
            x ^= i ^ nums[i];
        }
        return x;
    }
}
""", "O(n)", "O(1)", True),

P("sum-of-two-integers", "Sum of Two Integers", "Medium", ["Amazon", "Microsoft", "Google", "Adobe"],
"""Return the sum of two integers without using the `+` or `-` operators. `a = 2, b = 3` → 5; negative numbers must work too.""",
"""**How addition works in binary:**
- `a ^ b` = sum of the bits **ignoring carries**.
- `(a & b) << 1` = the **carries**, moved to the next position.

Repeat with `a = a ^ b`, `b = carry` until there's no carry. Java ints are 32-bit two's complement and overflow wraps, so negatives work automatically and the loop ends within 32 iterations (the carry shifts out of the left end).""",
r"""
class Solution {
    public int getSum(int a, int b) {
        while (b != 0) {
            int carry = (a & b) << 1;
            a = a ^ b;
            b = carry;
        }
        return a;
    }
}
""", "O(1) (at most 32 iterations)", "O(1)", False),

P("powx-n", "Pow(x, n)", "Medium", ["Amazon", "Google", "Microsoft", "Goldman Sachs", "Uber"],
"""Implement `x` raised to the power `n` (n may be negative). `pow(2.0, 10)` → 1024.0, `pow(2.0, -2)` → 0.25.""",
"""**Brute force:** multiply n times → O(n), too slow for n ≈ 2^31.

**Fast exponentiation (binary exponentiation):** walk the bits of n. Keep `base = x`; for each bit, if it's set, multiply the result by `base`; then square `base` and shift n right. O(log n).

**Negative n:** compute with `1/x` and `-n`. Convert n to `long` first, because `-Integer.MIN_VALUE` overflows an int.""",
r"""
class Solution {
    public double myPow(double x, int n) {
        long e = n;
        if (e < 0) {
            x = 1 / x;
            e = -e;
        }
        double result = 1.0, base = x;
        while (e > 0) {
            if ((e & 1) == 1) result *= base;
            base *= base;
            e >>= 1;
        }
        return result;
    }
}
""", "O(log n)", "O(1)", True),

P("happy-number", "Happy Number", "Easy", ["Amazon", "Google", "Microsoft", "Adobe", "Paytm"],
"""Repeatedly replace a number by the sum of the squares of its digits. If this process reaches 1, the number is happy; if it loops forever without reaching 1, it isn't. 19 → 82 → 68 → 100 → 1, so 19 is happy.""",
"""**Key insight:** the sequence either hits 1 or enters a cycle (values quickly drop below a few hundred, so they must repeat). Detecting the cycle is the whole problem.

- **HashSet:** store seen numbers; a repeat means a cycle.
- **Floyd's cycle detection (O(1) space):** slow moves one step, fast moves two; if they meet at a value other than 1, it's a cycle. Same idea as Linked List Cycle.""",
r"""
class Solution {
    public boolean isHappy(int n) {
        int slow = n, fast = next(n);
        while (fast != 1 && slow != fast) {
            slow = next(slow);
            fast = next(next(fast));
        }
        return fast == 1;
    }

    private int next(int n) {
        int sum = 0;
        while (n > 0) {
            int d = n % 10;
            sum += d * d;
            n /= 10;
        }
        return sum;
    }
}
""", "O(log n)", "O(1)", False),

P("plus-one", "Plus One", "Easy", ["Amazon", "Google", "Microsoft", "Adobe", "Paytm"],
"""A non-negative integer is stored as an array of digits (most significant first). Add one and return the resulting digit array. `[1,2,9]` → `[1,3,0]`; `[9,9]` → `[1,0,0]`.""",
"""Walk from the last digit: if it's less than 9, increment it and return — no carry. If it's 9, set it to 0 and continue to the left (carry).

If the loop finishes, every digit was 9 (e.g. `999`), so the answer is `1` followed by zeros: allocate a new array of length n+1 and set index 0 to 1 (Java initialises the rest to 0).""",
r"""
class Solution {
    public int[] plusOne(int[] digits) {
        for (int i = digits.length - 1; i >= 0; i--) {
            if (digits[i] < 9) {
                digits[i]++;
                return digits;
            }
            digits[i] = 0;
        }
        int[] res = new int[digits.length + 1];
        res[0] = 1;
        return res;
    }
}
""", "O(n)", "O(1) (O(n) only when all digits are 9)", False),
]

PATTERN = {"id": "math-bit", "name": "Math & Bit Manipulation", "order": 17, "intro": INTRO.strip(), "problems": PROBLEMS}
