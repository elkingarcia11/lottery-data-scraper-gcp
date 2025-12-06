import json
import os
from lottery_scraper import scrape_lottery_data, get_latest_draws, download_from_gcs, upload_to_gcs
from calculate_stats import calculate_lottery_stats
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get bucket name from environment variable or use default
BUCKET_NAME = os.getenv('LOTTERY_DATA_SCRAPER_BUCKET', 'jackpot-iq')

def main():
    """
    Main function to scrape lottery data and save to JSON files
    """
    print("Starting lottery data scraping...")
    
    # Try to download existing data from GCS (non-blocking - continues if it fails)
    print("Attempting to download files from GCS bucket:", BUCKET_NAME)
    try:
        download_from_gcs()
    except Exception as e:
        print(f"Note: GCS download failed ({e}). Continuing with local files.")
        # Ensure local files exist
        os.makedirs("data", exist_ok=True)
        if not os.path.exists("data/mm.json"):
            with open("data/mm.json", "w") as f:
                json.dump([], f)
        if not os.path.exists("data/pb.json"):
            with open("data/pb.json", "w") as f:
                json.dump([], f)
    
    # Get latest draws from files
    latest_draws = get_latest_draws()
    latest_pb_date = latest_draws['powerball']
    latest_mm_date = latest_draws['mega-millions']
    
    print("\nLatest Powerball draw:", latest_pb_date)
    print("Latest Mega Millions draw:", latest_mm_date)
    print("\n")
    
    # Scrape new lottery data (always saves locally, regardless of GCS)
    print("Scraping new lottery data...")
    scrape_lottery_data()
    
    # Calculate and save statistics (always saves locally)
    print("\nUpdating statistics based on new draws...")
    try:
        mm_stats, pb_stats = calculate_lottery_stats()
        
        # Save stats to local files (always happens, regardless of GCS)
        os.makedirs("data", exist_ok=True)
        with open("data/mm-stats.json", "w") as f:
            json.dump(mm_stats, f, indent=2)
        print("Saved mm-stats.json locally")
        
        with open("data/pb-stats.json", "w") as f:
            json.dump(pb_stats, f, indent=2)
        print("Saved pb-stats.json locally")
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        print("Note: Data files may still have been updated. Check data/ directory.")
    
    # Try to upload all files to GCS (non-blocking - files already saved locally)
    print("\nAttempting to upload files to GCS bucket:", BUCKET_NAME)
    try:
        upload_to_gcs()
    except Exception as e:
        print(f"Note: GCS upload failed ({e}). All files saved locally in data/ directory.")
    
    print("\n✓ Scrape and stats update completed successfully")
    print(f"✓ All data saved locally in data/ directory")

if __name__ == "__main__":
    main() 