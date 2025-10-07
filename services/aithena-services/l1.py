import math

def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    if n == 3:
        return True
    if n % 3 == 0:
        return False
    # Check divisors from 5 up to sqrt(n), with 6k±1 optimization
    i = 5
    w = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += w
        w = 6 - w
    return True

def next_prime(x):
    if x < 2:
        return 2
    candidate = x + 1
    while not is_prime(candidate):
        candidate += 1
    return candidate

def process_string_fast(s: str):
    print(f"Input string: '{s}'")
    
    # Step 1: Extract letter values (A=1, B=2, etc.), ignore non-letters
    values = []
    for char in s.upper():
        if 'A' <= char <= 'Z':
            val = ord(char) - ord('A') + 1
            values.append(val)
    
    if not values:
        print("No valid letters found.")
        return None

    print(f"Letter values: {values}")

    # Step 2: Compute components
    total_sum = sum(values)
    min_value = min(values)
    # Use math.prod for Python 3.8+ (very fast)
    try:
        product = math.prod(values)
    except AttributeError:
        # Fallback for older Python versions
        product = 1
        for v in values:
            product *= v

    print(f"Sum: {total_sum}")
    print(f"Min value: {min_value}")
    print(f"Product: {product}")

    # Step 3: Compute (sum ^ min) - product
    try:
        power_result = total_sum ** min_value
        print(f"Sum ^ Min = {total_sum}^{min_value} = {power_result}")
    except OverflowError:
        print("Error: Sum^Min is too large to compute.")
        return None

    final_value = power_result - product
    print(f"(Sum ^ Min) - Product = {power_result} - {product} = {final_value}")

    if final_value < 0:
        print("Result is negative. Finding next prime after 0...")
        final_value = 0

    # Step 4: Find next prime
    result = next_prime(final_value)
    print(f"Next prime after {final_value} is {result}")

    return result

if __name__ == "__main__":
    process_string_fast("zllozy, Wzzzorl!")