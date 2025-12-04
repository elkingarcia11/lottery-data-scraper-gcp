#!/usr/bin/env python3

import json
import argparse
import os
from collections import defaultdict

# Ensure data directory exists
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def verify_frequency_stats(stats):
    """
    Verify that frequency statistics are consistent
    
    Args:
        stats (dict): Statistics object to verify
    
    Returns:
        bool: True if verification passes
    """
    # Handle case where there are no draws
    if stats.get('totalDraws', 0) == 0:
        print("  No draws to verify (totalDraws = 0)")
        return True
    
    # Get the residuals for regular numbers by position
    position_residuals = stats['byPosition']
    
    if not position_residuals:
        print("  No position data to verify")
        return True
    
    # Calculate total draws from the first position's frequency
    first_position = list(position_residuals.keys())[0]  # Get first position key
    total_draws = sum(res['observed'] for res in position_residuals[first_position].values())
    
    if total_draws == 0:
        print("  No draws found in position data")
        return True
    
    # Verify each position has the correct number of draws
    for pos_key in position_residuals.keys():
        pos_sum = sum(res['observed'] for res in position_residuals[pos_key].values())
        if pos_sum != total_draws:
            print(f"  Position {pos_key}: Frequency sum check failed (got {pos_sum}, expected {total_draws})")
            return False
        print(f"  Position {pos_key}: Frequency sum check passed ({pos_sum})")
    
    # Verify special ball frequencies
    special_residuals = stats['specialBallNumbers']
    special_sum = sum(res['observed'] for res in special_residuals.values())
    if special_sum != total_draws:
        print(f"  Special ball validation: Failed (sum={special_sum}, expected={total_draws})")
        return False
    print(f"  Special ball validation: Passed (sum={special_sum}, expected={total_draws})")
    
    return True

def calculate_lottery_stats(mm_input="data/mm.json", 
                           pb_input="data/pb.json",
                           mm_output="data/mm-stats.json", 
                           pb_output="data/pb-stats.json"):
    """
    Calculate comprehensive statistics for lottery draws
    
    Args:
        mm_input (str): Path to the Mega Millions draws JSON file
        pb_input (str): Path to the Powerball draws JSON file
        mm_output (str): Path to save Mega Millions statistics
        pb_output (str): Path to save Powerball statistics
        
    Returns:
        tuple: (mm_stats, pb_stats) - The calculated statistics for both lottery types
    """
    try:
        # Read the Mega Millions file
        print(f"Reading Mega Millions draws from {mm_input}...")
        with open(mm_input, 'r') as f:
            mm_draws = json.load(f)
        
        # Read the Powerball file
        print(f"Reading Powerball draws from {pb_input}...")
        with open(pb_input, 'r') as f:
            pb_draws = json.load(f)
        
        print(f"Found {len(mm_draws)} Mega Millions draws and {len(pb_draws)} Powerball draws")
        
        # Calculate statistics for Mega Millions
        mm_stats = calculate_stats_for_type(mm_draws, "mega-millions", 
                                           max_regular=70, max_special=25)
        
        # Calculate statistics for Powerball
        pb_stats = calculate_stats_for_type(pb_draws, "powerball", 
                                           max_regular=69, max_special=26)
        
        # Verify all frequency statistics (only if there are draws)
        if mm_stats['totalDraws'] > 0 or pb_stats['totalDraws'] > 0:
            print("\nVerifying all frequency statistics...")
            mm_verified = verify_frequency_stats(mm_stats) if mm_stats['totalDraws'] > 0 else True
            pb_verified = verify_frequency_stats(pb_stats) if pb_stats['totalDraws'] > 0 else True
            
            if mm_verified and pb_verified:
                print("\nAll frequency statistics verified successfully!")
            else:
                print("\nWARNING: Some frequency statistics verification failed. Check the logs above.")
        else:
            print("\nNo draws found. Statistics initialized with default values.")
        
        # Save the statistics to separate files
        with open(mm_output, 'w') as f:
            json.dump(mm_stats, f, indent=2)
        print(f"Saved Mega Millions statistics to {mm_output}")
        
        with open(pb_output, 'w') as f:
            json.dump(pb_stats, f, indent=2)
        print(f"Saved Powerball statistics to {pb_output}")
        
        return mm_stats, pb_stats
        
    except Exception as e:
        print(f"Error calculating lottery statistics: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def sort_frequency_dict(freq_dict):
    """
    Sort a frequency dictionary by frequency (descending)
    
    Args:
        freq_dict (dict): Dictionary of number -> frequency
        
    Returns:
        dict: Sorted dictionary with most frequent numbers first
    """
    # Convert to list of tuples, sort by frequency (descending)
    sorted_items = sorted(freq_dict.items(), key=lambda x: int(x[1]), reverse=True)
    
    # Convert back to dictionary (maintaining order in Python 3.7+)
    return {k: v for k, v in sorted_items}

def find_optimized_numbers(frequency_dict, special_frequency):
    """
    Find optimized winning numbers based on frequency data
    
    Args:
        frequency_dict (dict): Dictionary of number frequencies
        special_frequency (dict): Dictionary of special ball frequencies
    
    Returns:
        list: List of optimized numbers [5 regular numbers + 1 special ball]
    """
    # Sort regular numbers by frequency
    sorted_regular = sorted(frequency_dict.items(), 
                          key=lambda x: x[1], 
                          reverse=True)
    
    # Get top 5 regular numbers
    optimized_regular = [int(num) for num, _ in sorted_regular[:5]]
    optimized_regular.sort()  # Sort in ascending order
    
    # Get most frequent special ball
    sorted_special = sorted(special_frequency.items(), 
                          key=lambda x: x[1], 
                          reverse=True)
    best_special_ball = int(sorted_special[0][0])
    
    return optimized_regular + [best_special_ball]

def find_optimized_numbers_by_general_frequency(frequency, special_ball_frequency, existing_combinations, max_regular):
    """
    Find optimized numbers based on general frequency (not position-specific)
    
    Args:
        frequency (dict): Dictionary of number frequencies across all positions
        special_ball_frequency (dict): Dictionary of special ball frequencies
        existing_combinations (set): Set of existing combinations
        max_regular (int): Maximum regular number value
        
    Returns:
        list: Optimized winning numbers [regular1, regular2, regular3, regular4, regular5, special]
    """
    # Convert frequency dict to list of tuples and sort by frequency (descending)
    freq_list = [(int(num), int(freq)) for num, freq in frequency.items()]
    freq_list.sort(key=lambda x: x[1], reverse=True)
    
    # Convert special ball frequency dict to list and sort
    special_freq_list = [(int(num), int(freq)) for num, freq in special_ball_frequency.items()]
    special_freq_list.sort(key=lambda x: x[1], reverse=True)
    
    # Take the top 5 most frequent regular numbers
    optimized_regular = [freq_list[i][0] for i in range(min(5, len(freq_list)))]
    
    # Always take the most frequent special ball
    best_special_ball = special_freq_list[0][0] if special_freq_list else 1
    
    # Sort the regular numbers
    optimized_regular.sort()
    
    # Create a set of just the regular number combinations (without special ball)
    # to check if this exact set of 5 regular numbers has appeared before
    existing_regular_sets = set()
    for combo in existing_combinations:
        existing_regular_sets.add(tuple(sorted(combo[:5])))
    
    # Check if this set of regular numbers already exists
    regular_set = tuple(optimized_regular)
    
    attempts = 0
    max_attempts = 100  # Limit to prevent infinite loops
    
    while regular_set in existing_regular_sets and attempts < max_attempts:
        # Try replacing one of the regular numbers with the next most frequent
        if attempts < len(freq_list) - 5:
            # Replace the least frequent number in our current set with the next most frequent
            # from our overall frequency list that we haven't used yet
            next_best_index = 5 + attempts
            if next_best_index < len(freq_list):
                next_best_number = freq_list[next_best_index][0]
                
                # Find the least frequent number in our current selection
                least_frequent_idx = 0
                least_frequent_val = float('inf')
                
                for i, num in enumerate(optimized_regular):
                    # Find this number's frequency
                    num_freq = next((f for n, f in freq_list if n == num), 0)
                    if num_freq < least_frequent_val:
                        least_frequent_val = num_freq
                        least_frequent_idx = i
                
                # Replace it with our next best number
                optimized_regular[least_frequent_idx] = next_best_number
            else:
                # If we've exhausted our frequency list, try a random new number
                available_numbers = set(range(1, max_regular + 1)) - set(optimized_regular)
                if available_numbers:
                    # Replace the least frequent number with a random available one
                    least_frequent_idx = 0
                    least_frequent_val = float('inf')
                    
                    for i, num in enumerate(optimized_regular):
                        num_freq = next((f for n, f in freq_list if n == num), 0)
                        if num_freq < least_frequent_val:
                            least_frequent_val = num_freq
                            least_frequent_idx = i
                    
                    # Get the first available number (any would do)
                    new_number = next(iter(available_numbers))
                    optimized_regular[least_frequent_idx] = new_number
        else:
            # We've tried all regular number combinations from frequency list
            # Try generating a random combination that isn't in existing_combinations
            used_numbers = set()
            while len(used_numbers) < 5:
                # Pick the next available frequent number we haven't tried
                for num, _ in freq_list:
                    if num not in used_numbers and len(used_numbers) < 5:
                        used_numbers.add(num)
            
            optimized_regular = sorted(list(used_numbers))
        
        # Sort the regular numbers again
        optimized_regular.sort()
        
        # Recalculate the regular set
        regular_set = tuple(optimized_regular)
        attempts += 1
    
    # Always use the most frequent special ball
    # Return the optimized 5 regular numbers + best special ball
    return optimized_regular + [best_special_ball]

def calculate_standardized_residuals(frequency_dict, total_draws, max_number):
    """
    Calculate standardized residuals for frequency data
    
    Args:
        frequency_dict (dict): Dictionary of number frequencies
        total_draws (int): Total number of draws
        max_number (int): Maximum possible number
    
    Returns:
        dict: Dictionary of standardized residuals
    """
    residuals = {}
    
    # Handle case where there are no draws
    if total_draws == 0:
        expected = 0.0
        for number, observed in frequency_dict.items():
            residuals[number] = {
                "observed": observed,
                "expected": expected,
                "residual": 0.0,
                "significant": False
            }
        return residuals
    
    expected = total_draws / max_number
    
    # Avoid division by zero if expected is 0
    if expected == 0:
        for number, observed in frequency_dict.items():
            residuals[number] = {
                "observed": observed,
                "expected": expected,
                "residual": 0.0,
                "significant": False
            }
        return residuals
    
    for number, observed in frequency_dict.items():
        residual = (observed - expected) / (expected ** 0.5)
        residuals[number] = {
            "observed": observed,
            "expected": expected,
            "residual": residual,
            "significant": abs(residual) > 2.0  # 95% confidence interval
        }
    
    return residuals

def calculate_position_specific_residuals(frequency_at_position, total_draws, k):
    """
    Calculate standardized residuals for each position, taking into account the valid range of numbers
    
    Args:
        frequency_at_position (dict): Dictionary of position -> number frequencies
        total_draws (int): Total number of draws
        k (int): Number of possible numbers (70 for Mega Millions, 69 for Powerball)
    
    Returns:
        dict: Dictionary with standardized residuals and significance flags for each position
    """
    # Each position has k-4 possible numbers
    possible_numbers_per_position = k - 4
    expected_frequency = total_draws / possible_numbers_per_position if total_draws > 0 else 0.0
    
    position_residuals = {}
    
    # Handle case where there are no draws
    if total_draws == 0 or expected_frequency == 0:
        for pos in range(5):
            pos_str = str(pos)
            pos_freq = frequency_at_position[pos_str]
            residuals = {}
            for num, observed in pos_freq.items():
                residuals[num] = {
                    "frequency": observed,
                    "expected": expected_frequency,
                    "standardized_residual": 0.0,
                    "significant": False,
                    "verySignificant": False
                }
            position_residuals[pos_str] = residuals
        return position_residuals
    
    # Calculate residuals for each position (0-4 for regular numbers)
    for pos in range(5):
        pos_str = str(pos)
        pos_freq = frequency_at_position[pos_str]
        
        residuals = {}
        for num, observed in pos_freq.items():
            # Calculate standardized residual
            zi = (int(observed) - expected_frequency) / (expected_frequency ** 0.5)
            
            # Determine significance levels
            # 95% confidence (|z| > 1.96)
            is_significant = abs(zi) > 1.96
            # 99% confidence (|z| > 2.576)
            is_very_significant = abs(zi) > 2.576
            
            residuals[num] = {
                "frequency": observed,
                "expected": expected_frequency,
                "standardized_residual": zi,
                "significant": is_significant,
                "verySignificant": is_very_significant
            }
        
        position_residuals[pos_str] = residuals
    
    return position_residuals

def calculate_stats_for_type(draws, lottery_type, max_regular, max_special):
    """
    Calculate statistics for a specific lottery type
    
    Args:
        draws (list): List of draw dictionaries
        lottery_type (str): Type of lottery ("powerball" or "mega-millions")
        max_regular (int): Maximum regular number (69 for Powerball, 70 for Mega Millions)
        max_special (int): Maximum special ball number (26 for Powerball, 25 for Mega Millions)
    
    Returns:
        dict: Calculated statistics
    """
    # Initialize counters
    valid_draws = 0
    frequency = {str(i): 0 for i in range(1, max_regular + 1)}
    special_frequency = {str(i): 0 for i in range(1, max_special + 1)}
    position_frequency = {f"position{i}": {str(j): 0 for j in range(1, max_regular + 1)} for i in range(5)}
    
    # Process each draw
    for draw in draws:
        if not isinstance(draw, dict):
            continue
            
        numbers = draw.get('numbers', [])
        special_ball = draw.get('specialBall')
        
        # Skip if not a valid draw structure
        if not isinstance(numbers, list) or len(numbers) != 5 or not isinstance(special_ball, int):
            continue
        
        # Validate all regular numbers are within range
        valid_regular_numbers = True
        for num in numbers:
            if not isinstance(num, int) or num < 1 or num > max_regular:
                valid_regular_numbers = False
                break
        
        # Validate special ball is within range
        valid_special_ball = isinstance(special_ball, int) and 1 <= special_ball <= max_special
        
        # Only count if all numbers are valid
        if valid_regular_numbers and valid_special_ball:
            valid_draws += 1
            
            # Count regular numbers
            for i, num in enumerate(numbers):
                num_str = str(num)
                frequency[num_str] += 1
                position_frequency[f"position{i}"][num_str] += 1
            
            # Count special ball
            special_frequency[str(special_ball)] += 1
    
    # Validate frequency counts
    total_regular = sum(frequency.values())
    total_special = sum(special_frequency.values())
    
    if valid_draws > 0:
        if total_regular != valid_draws * 5:
            print(f"Warning: Total regular number frequency ({total_regular}) does not match expected ({valid_draws * 5})")
        
        if total_special != valid_draws:
            print(f"Warning: Total special ball frequency ({total_special}) does not match expected ({valid_draws})")
    
    # Calculate optimized numbers (handle empty case)
    if valid_draws == 0:
        # Return default values when there are no draws
        optimized_by_position = [1, 2, 3, 4, 5, 1]
        optimized_by_general_frequency = [1, 2, 3, 4, 5, 1]
    else:
        optimized_by_position = find_optimized_numbers(frequency, special_frequency)
        optimized_by_general_frequency = find_optimized_numbers(frequency, special_frequency)
    
    # Calculate standardized residuals
    regular_residuals = calculate_standardized_residuals(frequency, valid_draws * 5, max_regular)
    special_residuals = calculate_standardized_residuals(special_frequency, valid_draws, max_special)
    
    # Calculate position-specific residuals
    position_residuals = {}
    for pos, pos_freq in position_frequency.items():
        position_residuals[pos] = calculate_standardized_residuals(pos_freq, valid_draws, max_regular)
    
    # Create the final statistics object with simplified structure
    stats = {
        "type": lottery_type,
        "totalDraws": valid_draws,
        "optimizedByPosition": optimized_by_position,
        "optimizedByGeneralFrequency": optimized_by_general_frequency,
        "regularNumbers": regular_residuals,
        "specialBallNumbers": special_residuals,
        "byPosition": position_residuals
    }
    
    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate lottery statistics")
    parser.add_argument("--mm-input", default="data/mm.json", help="Input JSON file with Mega Millions draws")
    parser.add_argument("--pb-input", default="data/pb.json", help="Input JSON file with Powerball draws") 
    parser.add_argument("--mm-output", default="data/mm-stats.json", help="Output file for Mega Millions statistics")
    parser.add_argument("--pb-output", default="data/pb-stats.json", help="Output file for Powerball statistics")
    args = parser.parse_args()
    
    calculate_lottery_stats(args.mm_input, args.pb_input, args.mm_output, args.pb_output)