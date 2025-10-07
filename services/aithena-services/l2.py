import math  # For square root in prime checking

def get_value(char):
    """Convert a letter to its corresponding value (A=1, B=2, ..., Z=26)."""
    if char.isalpha():
        return ord(char.upper()) - ord('A') + 1
    return None  # Non-alphabetic characters are ignored

def is_prime(n):
    """Check if a number is prime. Optimized for speed."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6  # Check only multiples of 6k ± 1
    return True

def next_prime(n):
    """Find the smallest prime greater than n."""
    if n < 2:
        return 2  # 2 is the smallest prime
    candidate = n + 1
    while not is_prime(candidate):
        candidate += 1
    return candidate

def process_string(input_str):
    """Main function to process the input string as per the requirements.
    
    Steps:
    1. Extract values for each alphabetic character.
    2. Compute the sum of values.
    3. Find the lowest value.
    4. Elevate the sum to the power of the lowest value.
    5. Compute the product of all values.
    6. Subtract the product from the elevated sum.
    7. Find and return the next prime after the result.
    
    Prints traceable info at each step.
    """
    # Step 1: Get values for alphabetic characters
    values = [get_value(char) for char in input_str if get_value(char) is not None]
    
    if not values:
        print("Error: No alphabetic characters found in the input string.")
        return None  # Early return for empty or non-alphabetic strings
    
    print(f"Input string: '{input_str}'")
    print(f"Extracted values (A=1, B=2, ..., Z=26): {values}")
    
    # Step 2: Compute the sum of values
    sum_values = sum(values)
    print(f"Sum of values: {sum_values}")
    
    # Step 3: Find the lowest value
    lowest_value = min(values)
    print(f"Lowest value in the string: {lowest_value}")
    
    # Step 4: Elevate the sum to the power of the lowest value
    elevated_sum = sum_values ** lowest_value
    print(f"Elevated sum ({sum_values} raised to the power of {lowest_value}): {elevated_sum}")
    
    # Step 5: Compute the product of all values
    product_values = 1
    for val in values:
        product_values *= val  # Manual multiplication for compatibility
    print(f"Product of all values: {product_values}")
    
    # Step 6: Subtract the product from the elevated sum
    result = elevated_sum - product_values
    print(f"Result after subtraction ({elevated_sum} - {product_values}): {result}")
    
    # Step 7: Find the next prime after the result
    final_prime = next_prime(result)
    print(f"Next prime after {result}: {final_prime}")
    
    return final_prime  # Return the final result

# Example usage:
if __name__ == "__main__":
    input_string = input("Enter a string: ")  # Get input from user
    result = process_string(input_string)
    if result is not None:
        print(f"\nFinal output: {result}")