# Lottery Data Scraper with Google Cloud Integration

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
    "optimizedByGeneralFrequencyRepeat": [int, int, int, int, int, int],
    "optimizedByGeneralFrequencyNoRepeat": [int, int, int, int, int, int],
    "optimizedByPositionFrequencyRepeat": [int, int, int, int, int, int],
    "optimizedByPositionFrequencyNoRepeat": [int, int, int, int, int, int],
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

**Optimization Strategies:**

- `optimizedByGeneralFrequencyRepeat`: Top 5 numbers and 1 special ball by general frequency (can repeat previous combinations)
- `optimizedByGeneralFrequencyNoRepeat`: Top 5 numbers and 1 special ball by general frequency that hasn't been drawn yet
- `optimizedByPositionFrequencyRepeat`: Top number at each position (0-4) and 1 special ball by position-specific frequency (can repeat)
- `optimizedByPositionFrequencyNoRepeat`: Top number at each position (0-4) and 1 special ball by position-specific frequency that hasn't been drawn yet

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

The statistics include four optimization strategies:

- **`optimizedByGeneralFrequencyRepeat`**: Top 5 numbers and 1 special ball with highest general frequency (allows repeating previous combinations)
- **`optimizedByGeneralFrequencyNoRepeat`**: Top 5 numbers and 1 special ball with highest general frequency that hasn't been drawn yet
- **`optimizedByPositionFrequencyRepeat`**: Top number at each position (0-4) and 1 special ball with highest position-specific frequency (allows repeating)
- **`optimizedByPositionFrequencyNoRepeat`**: Top number at each position (0-4) and 1 special ball with highest position-specific frequency that hasn't been drawn yet

Each strategy returns an array of 6 numbers: `[regular1, regular2, regular3, regular4, regular5, specialBall]`

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
     LOTTERY_DATA_SCRAPER_BUCKET=your-bucket-name
     ```

   - Place GCS credentials in `gcs_credentials.json` at the root of the project

   - Set the credentials environment variable:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="gcs_credentials.json"
     ```

   **Note**: GCS is optional. The script will work perfectly fine without it, saving all data locally in the `data/` directory.

## Usage

### Local Execution

Run the main script:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

### Docker Execution (One-Time Run)

Build and run the application in a Docker container:

```bash
# Build the image
docker build -t lottery-scraper .

# Run once (with data persistence)
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/gcs_credentials.json:/app/gcs_credentials.json:ro \
  -e LOTTERY_DATA_SCRAPER_BUCKET=your-bucket-name \
  lottery-scraper
```

**Simplified run (without GCS):**

```bash
docker run --rm -v $(pwd)/data:/app/data lottery-scraper
```

**Notes**:

- The `data/` directory is mounted as a volume to persist results locally
- GCS credentials are optional - mount them only if you want to sync with GCS
- The container runs once and exits automatically
- To run again, simply execute the `docker run` command again

### Google Cloud Run Deployment

The application includes an HTTP server for Cloud Run deployment:

**Deploy to Cloud Run:**

```bash
# Build and deploy
gcloud run deploy lottery-scraper \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars LOTTERY_DATA_SCRAPER_BUCKET=your-bucket-name
```

**Trigger the scraper:**

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe lottery-scraper --region us-central1 --format 'value(status.url)')

# Trigger the scraper via HTTP
curl -X POST $SERVICE_URL
```

**Health check:**

```bash
curl $SERVICE_URL/health
```

**Notes for Cloud Run:**

- The service listens on the `PORT` environment variable (default 8080, Cloud Run provides this)
- Data is saved to GCS (configured via `LOTTERY_DATA_SCRAPER_BUCKET`)
- The service responds to HTTP requests and runs the scraper on each POST/GET to `/`
- Use Cloud Scheduler to trigger it periodically if needed

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
