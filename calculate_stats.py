#!/usr/bin/env python3

import json
import argparse
import os

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

def get_existing_combinations(draws):
    """
    Extract all existing number combinations from draws
    
    Args:
        draws (list): List of draw dictionaries
    
    Returns:
        set: Set of tuples representing existing combinations (numbers + specialBall)
    """
    existing = set()
    for draw in draws:
        if isinstance(draw, dict):
            numbers = draw.get('numbers', [])
            special_ball = draw.get('specialBall')
            if isinstance(numbers, list) and len(numbers) == 5 and isinstance(special_ball, int):
                # Store as tuple: (num1, num2, num3, num4, num5, specialBall)
                combo = tuple(sorted(numbers)) + (special_ball,)
                existing.add(combo)
    return existing

def optimized_by_general_frequency_repeat(frequency, special_frequency):
    """
    Find top 5 numbers and 1 special ball with highest general frequency (can repeat)
    
    Args:
        frequency (dict): Dictionary of number frequencies across all positions
        special_frequency (dict): Dictionary of special ball frequencies
    
    Returns:
        list: [5 regular numbers + 1 special ball] sorted
    """
    # Sort by frequency (descending)
    sorted_regular = sorted(frequency.items(), key=lambda x: int(x[1]), reverse=True)
    sorted_special = sorted(special_frequency.items(), key=lambda x: int(x[1]), reverse=True)
    
    # Get top 5 regular numbers
    optimized_regular = [int(num) for num, _ in sorted_regular[:5]]
    optimized_regular.sort()
    
    # Get most frequent special ball
    best_special = int(sorted_special[0][0]) if sorted_special else 1
    
    return optimized_regular + [best_special]

def optimized_by_general_frequency_no_repeat(frequency, special_frequency, existing_combinations, max_regular, max_special):
    """
    Find top 5 numbers and 1 special ball with highest general frequency that hasn't been drawn yet
    
    Args:
        frequency (dict): Dictionary of number frequencies across all positions
        special_frequency (dict): Dictionary of special ball frequencies
        existing_combinations (set): Set of existing combinations
        max_regular (int): Maximum regular number
        max_special (int): Maximum special ball number
    
    Returns:
        list: [5 regular numbers + 1 special ball] that hasn't been drawn
    """
    # Sort by frequency (descending)
    sorted_regular = sorted(frequency.items(), key=lambda x: int(x[1]), reverse=True)
    sorted_special = sorted(special_frequency.items(), key=lambda x: int(x[1]), reverse=True)
    
    # Try combinations until we find one that hasn't been drawn
    max_attempts = 1000
    attempts = 0
    
    for i in range(min(20, len(sorted_regular))):  # Try top 20 regular numbers
        for j in range(min(10, len(sorted_regular))):
            for k in range(min(10, len(sorted_regular))):
                for l in range(min(10, len(sorted_regular))):
                    for m in range(min(10, len(sorted_regular))):
                        if attempts >= max_attempts:
                            break
                        attempts += 1
                        
                        # Get 5 different numbers from top frequent ones
                        candidates = [sorted_regular[i][0], sorted_regular[j][0], 
                                     sorted_regular[k][0], sorted_regular[l][0], sorted_regular[m][0]]
                        candidates = [int(c) for c in candidates]
                        
                        # Check if all numbers are unique
                        if len(set(candidates)) != 5:
                            continue
                        
                        # Try each special ball
                        for special_item in sorted_special[:10]:
                            special_ball = int(special_item[0])
                            candidates_sorted = sorted(candidates)
                            combo = tuple(candidates_sorted) + (special_ball,)
                            
                            if combo not in existing_combinations:
                                return candidates_sorted + [special_ball]
    
    # Fallback: return top 5 with top special ball (even if it's a repeat)
    return optimized_by_general_frequency_repeat(frequency, special_frequency)

def optimized_by_position_frequency_repeat(position_frequency, special_frequency):
    """
    Find top number at each position and 1 special ball with highest frequency (can repeat)
    
    Args:
        position_frequency (dict): Dictionary of position -> number frequencies
        special_frequency (dict): Dictionary of special ball frequencies
    
    Returns:
        list: [number at pos0, pos1, pos2, pos3, pos4, special ball] (preserves position order)
    """
    optimized = []
    
    # Get most frequent number at each position (preserve position order)
    for pos in range(5):
        pos_key = f"position{pos}"
        if pos_key in position_frequency:
            sorted_pos = sorted(position_frequency[pos_key].items(), 
                              key=lambda x: int(x[1]), reverse=True)
            if sorted_pos:
                optimized.append(int(sorted_pos[0][0]))
            else:
                optimized.append(1)
        else:
            optimized.append(1)
    
    # Get most frequent special ball
    sorted_special = sorted(special_frequency.items(), key=lambda x: int(x[1]), reverse=True)
    best_special = int(sorted_special[0][0]) if sorted_special else 1
    
    return optimized + [best_special]

def optimized_by_position_frequency_no_repeat(position_frequency, special_frequency, existing_combinations, max_regular, max_special):
    """
    Find top number at each position and 1 special ball with highest frequency that hasn't been drawn yet
    
    Args:
        position_frequency (dict): Dictionary of position -> number frequencies
        special_frequency (dict): Dictionary of special ball frequencies
        existing_combinations (set): Set of existing combinations
        max_regular (int): Maximum regular number
        max_special (int): Maximum special ball number
    
    Returns:
        list: [number at pos0, pos1, pos2, pos3, pos4, special ball] that hasn't been drawn (preserves position order)
    """
    # Get top candidates for each position
    position_candidates = []
    for pos in range(5):
        pos_key = f"position{pos}"
        if pos_key in position_frequency:
            sorted_pos = sorted(position_frequency[pos_key].items(), 
                              key=lambda x: int(x[1]), reverse=True)
            # Get top 10 candidates for this position
            candidates = [int(num) for num, _ in sorted_pos[:10]]
            position_candidates.append(candidates if candidates else [1])
        else:
            position_candidates.append([1])
    
    # Get top special ball candidates
    sorted_special = sorted(special_frequency.items(), key=lambda x: int(x[1]), reverse=True)
    special_candidates = [int(num) for num, _ in sorted_special[:10]] if sorted_special else [1]
    
    # Try combinations until we find one that hasn't been drawn
    max_attempts = 1000
    attempts = 0
    
    for pos0 in position_candidates[0][:5]:
        for pos1 in position_candidates[1][:5]:
            for pos2 in position_candidates[2][:5]:
                for pos3 in position_candidates[3][:5]:
                    for pos4 in position_candidates[4][:5]:
                        # Check if all positions have unique numbers
                        numbers = [pos0, pos1, pos2, pos3, pos4]
                        if len(set(numbers)) != 5:
                            continue
                        
                        for special in special_candidates[:5]:
                            if attempts >= max_attempts:
                                break
                            attempts += 1
                            
                            # Preserve position order (don't sort)
                            combo = tuple(sorted(numbers)) + (special,)
                            
                            if combo not in existing_combinations:
                                return numbers + [special]
    
    # Fallback: return top by position (even if it's a repeat)
    return optimized_by_position_frequency_repeat(position_frequency, special_frequency)

def calculate_standardized_residuals(frequency_dict, total_draws, max_number, actual_draws=None, percent_multiplier=1.0):
    """
    Calculate standardized residuals for frequency data
    
    Args:
        frequency_dict (dict): Dictionary of number frequencies
        total_draws (int): Total number of draws (for expected calculation)
        max_number (int): Maximum possible number
        actual_draws (int): Actual number of draws for percent calculation (defaults to total_draws)
        percent_multiplier (float): Multiplier for percent calculation (defaults to 1.0)
    
    Returns:
        dict: Dictionary of standardized residuals
    """
    residuals = {}
    
    # Use actual_draws for percent calculation, default to total_draws
    if actual_draws is None:
        actual_draws = total_draws
    
    # Handle case where there are no draws
    if total_draws == 0:
        expected = 0.0
        for number, observed in frequency_dict.items():
            percent = (observed / actual_draws * percent_multiplier * 100) if actual_draws > 0 else 0.0
            residuals[number] = {
                "observed": observed,
                "expected": expected,
                "residual": 0.0,
                "significant": False,
                "percent": percent
            }
        return residuals
    
    expected = total_draws / max_number
    
    # Avoid division by zero if expected is 0
    if expected == 0:
        for number, observed in frequency_dict.items():
            percent = (observed / actual_draws * percent_multiplier * 100) if actual_draws > 0 else 0.0
            residuals[number] = {
                "observed": observed,
                "expected": expected,
                "residual": 0.0,
                "significant": False,
                "percent": percent
            }
        return residuals
    
    for number, observed in frequency_dict.items():
        residual = (observed - expected) / (expected ** 0.5)
        percent = (observed / actual_draws * percent_multiplier * 100) if actual_draws > 0 else 0.0
        residuals[number] = {
            "observed": observed,
            "expected": expected,
            "residual": residual,
            "significant": abs(residual) > 2.0,  # 95% confidence interval
            "percent": percent
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
    # Get existing combinations for no-repeat strategies
    existing_combinations = get_existing_combinations(draws)
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
        optimized_general_repeat = [1, 2, 3, 4, 5, 1]
        optimized_general_no_repeat = [1, 2, 3, 4, 5, 1]
        optimized_position_repeat = [1, 2, 3, 4, 5, 1]
        optimized_position_no_repeat = [1, 2, 3, 4, 5, 1]
    else:
        # Calculate all four optimization strategies
        optimized_general_repeat = optimized_by_general_frequency_repeat(frequency, special_frequency)
        optimized_general_no_repeat = optimized_by_general_frequency_no_repeat(
            frequency, special_frequency, existing_combinations, max_regular, max_special)
        optimized_position_repeat = optimized_by_position_frequency_repeat(position_frequency, special_frequency)
        optimized_position_no_repeat = optimized_by_position_frequency_no_repeat(
            position_frequency, special_frequency, existing_combinations, max_regular, max_special)
    
    # Calculate standardized residuals
    # For regular numbers: percent = observed / total_draws * 5
    regular_residuals = calculate_standardized_residuals(frequency, valid_draws * 5, max_regular, 
                                                         actual_draws=valid_draws, percent_multiplier=5.0)
    # For special ball: percent = observed / total_draws
    special_residuals = calculate_standardized_residuals(special_frequency, valid_draws, max_special,
                                                         actual_draws=valid_draws, percent_multiplier=1.0)
    
    # Calculate position-specific residuals
    # For positionX: percent = observed / total_draws
    position_residuals = {}
    for pos, pos_freq in position_frequency.items():
        position_residuals[pos] = calculate_standardized_residuals(pos_freq, valid_draws, max_regular,
                                                                   actual_draws=valid_draws, percent_multiplier=1.0)
    
    # Create the final statistics object with new structure
    stats = {
        "type": lottery_type,
        "totalDraws": valid_draws,
        "optimizedByGeneralFrequencyRepeat": optimized_general_repeat,
        "optimizedByGeneralFrequencyNoRepeat": optimized_general_no_repeat,
        "optimizedByPositionFrequencyRepeat": optimized_position_repeat,
        "optimizedByPositionFrequencyNoRepeat": optimized_position_no_repeat,
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