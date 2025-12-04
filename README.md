# Jackpot IQ Updater

A Python application that scrapes lottery data (Powerball and Mega Millions), calculates statistical significance, and stores the results locally and optionally in Google Cloud Storage.

## Features

- **Local-first approach**: All data is always saved locally, even if GCS is unavailable
- **Resilient to failures**: Continues operation even if GCS connection fails or credentials are missing
- **Handles empty data**: Gracefully handles cases with no draws (no division by zero errors)
- **Automatic statistics**: Calculates frequency analysis and statistical significance
- **Incremental updates**: Only scrapes new draws since the last run

## Project Structure

```
lottery_data_scraper_gcp/
├── main.py                 # Main script orchestrating the workflow
├── lottery_scraper.py       # Handles data scraping and GCS operations
├── calculate_stats.py      # Calculates lottery statistics and significance
├── requirements.txt        # Python dependencies
├── data/                   # Local storage for JSON files
│   ├── mm.json             # Mega Millions draw history
│   ├── pb.json             # Powerball draw history
│   ├── mm-stats.json       # Mega Millions statistics
│   └── pb-stats.json       # Powerball statistics
├── gcs_credentials.json    # Google Cloud Storage credentials (optional)
├── .env                    # Environment variables (optional)
└── venv/                   # Python virtual environment
```

## Data Formats

### Draw History Format (mm.json, pb.json)

```json
[
    {
        "date": "YYYY-MM-DD",
        "numbers": [int, int, int, int, int],
        "specialBall": int,
        "type": "mega-millions" or "powerball"
    },
    ...
]
```

### Statistics Format (mm-stats.json, pb-stats.json)

```json
{
    "type": "powerball" or "mega-millions",
    "totalDraws": int,
    "optimizedByPosition": [int, int, int, int, int, int],
    "optimizedByGeneralFrequency": [int, int, int, int, int, int],
    "regularNumbers": {
        "1": {
            "observed": int,
            "expected": float,
            "residual": float,
            "significant": boolean
        },
        ...
    },
    "specialBallNumbers": {
        "1": {
            "observed": int,
            "expected": float,
            "residual": float,
            "significant": boolean
        },
        ...
    },
    "byPosition": {
        "position0": {
            "1": {
                "observed": int,
                "expected": float,
                "residual": float,
                "significant": boolean
            },
            ...
        },
        ...
    }
}
```

## Statistical Analysis

### Frequency Analysis

- Regular numbers: Counts frequency of each number across all positions
- Special ball: Counts frequency of each special ball number
- Position-specific: Counts frequency of each number at each position (0-4)

### Statistical Significance

- Calculates standardized residuals for each number
- A number is considered statistically significant if |residual| > 2.0 (95% confidence)
- Expected frequencies are calculated assuming uniform distribution

### Optimized Numbers

- `optimizedByPosition`: Most frequent numbers at each position
- `optimizedByGeneralFrequency`: Most frequent numbers overall

## Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Set up Google Cloud Storage:

   - Create a `.env` file with your GCS bucket name:

     ```
     GCS_BUCKET=your-bucket-name
     ```

   - Place GCS credentials in `gcs_credentials.json` at the root of the project

   - Set the credentials environment variable:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="gcs_credentials.json"
     ```

   **Note**: GCS is optional. The script will work perfectly fine without it, saving all data locally in the `data/` directory.

## Usage

Run the main script:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

If you have GCS credentials set up, the script will:

- Attempt to download existing data from GCS
- Scrape new lottery data
- Save everything locally
- Attempt to upload updated data to GCS

If GCS is unavailable or not configured, the script will:

- Use local files (or create empty ones if they don't exist)
- Scrape new lottery data
- Save everything locally
- Continue operation without errors

## Workflow

1. **Download existing data** (if GCS is available):

   - Attempts to download existing data from GCS
   - Falls back to local files if GCS is unavailable
   - Creates empty files if no data exists

2. **Scrape latest lottery draws**:

   - Scrapes from lottery.net for current year
   - Only fetches draws newer than the latest local draw
   - Validates and filters draws:
     - Regular numbers must be within valid range (1-70 for MM, 1-69 for PB)
     - Special ball must be within valid range (1-25 for MM, 1-26 for PB)

3. **Save data locally**:

   - Always saves all draw data to `data/mm.json` and `data/pb.json`
   - Updates existing files with new draws (no duplicates)

4. **Calculate statistics**:

   - Frequency counts for each number
   - Statistical significance (standardized residuals)
   - Optimized number recommendations
   - Handles empty data gracefully (no errors with 0 draws)

5. **Save statistics locally**:

   - Always saves statistics to `data/mm-stats.json` and `data/pb-stats.json`

6. **Upload to GCS** (if available):
   - Attempts to upload all files to GCS
   - Continues without error if upload fails
   - All data remains safely stored locally

## Error Handling

The script is designed to be resilient and handle various error conditions:

- **GCS Connection Failures**: If GCS is unavailable, the script continues with local files only
- **Missing Credentials**: Works without GCS credentials, saving everything locally
- **Empty Data**: Handles cases with no draws gracefully (no division by zero errors)
- **Network Issues**: Continues operation even if scraping temporarily fails
- **Invalid Data**: Validates and filters out invalid draws automatically

## Validation

The script performs several validations:

- **Draw structure validation**: Ensures each draw has the correct format
- **Number range validation**:
  - Regular numbers must be within valid range (1-70 for MM, 1-69 for PB)
  - Special ball must be within valid range (1-25 for MM, 1-26 for PB)
- **Frequency sum checks** (when data exists):
  - Each position should sum to totalDraws
  - Special ball frequencies should sum to totalDraws
  - Regular number frequencies should sum to totalDraws × 5

## Local-First Architecture

This application follows a **local-first** approach:

- ✅ All data is **always** saved locally in the `data/` directory
- ✅ GCS is optional and used only for backup/sync
- ✅ Script continues operation even if GCS fails
- ✅ No data loss if GCS is unavailable
- ✅ Works offline (except for initial scraping)

This ensures your data is always safe and accessible, regardless of cloud connectivity.
