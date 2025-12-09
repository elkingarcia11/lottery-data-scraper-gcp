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
            "significant": boolean,
            "percent": float
        },
        ...
    },
    "specialBallNumbers": {
        "1": {
            "observed": int,
            "expected": float,
            "residual": float,
            "significant": boolean,
            "percent": float
        },
        ...
    },
    "byPosition": {
        "position0": {
            "1": {
                "observed": int,
                "expected": float,
                "residual": float,
                "significant": boolean,
                "percent": float
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

**Position-Specific Ranges:**

**Note: Positions are 0-indexed (0, 1, 2, 3, 4) where position 0 is the first (lowest) number and position 4 is the last (highest) number.**

- Each position has a different valid range of numbers due to the constraint that numbers must be in ascending order:
  - **Mega Millions**: Each position has 66 possible numbers
    - Position 0: 1 to 66
    - Position 1: 2 to 67
    - Position 2: 3 to 68
    - Position 3: 4 to 69
    - Position 4: 5 to 70
  - **Powerball**: Each position has 65 possible numbers
    - Position 0: 1 to 65
    - Position 1: 2 to 66
    - Position 2: 3 to 67
    - Position 3: 4 to 68
    - Position 4: 5 to 69

### Statistical Significance

- Calculates standardized residuals (z-scores) for each number using **exact binomial standard deviation**
- A number is considered statistically significant if |residual| > 2.0 (95% confidence interval)
- Expected frequencies are calculated assuming uniform distribution

**Mathematical Foundation for General Frequency:**

For general frequency (how often a specific number appears anywhere in the 5 white balls), the probability calculation is:

For any specific number k (where k is between 1 and max_number):

- **Total combinations with k**: C(max_number-1, 4) — because if k is in the draw, you choose the other 4 numbers from the remaining (max_number-1)
- **Total possible combinations**: C(max_number, 5)

**Probability that number k appears:**

```
P(k appears) = C(max_number-1, 4) / C(max_number, 5)
             = 5 / max_number
```

**The result:**

- **Mega Millions**: Every number from 1 to 70 has exactly the same probability: `5/70 = 1/14 ≈ 7.14%`
- **Powerball**: Every number from 1 to 69 has exactly the same probability: `5/69 ≈ 7.25%`

This makes intuitive sense: you're drawing 5 balls out of max_number, so each ball has a `5/max_number` chance of being selected.

**Mathematical Foundation for Position-Specific Frequency:**

For position-based frequency (how often a specific number appears in a specific position when the 5 white balls are sorted in ascending order), the probability calculation is:

**Note: Positions are 0-indexed. Position 0 = first (lowest) number, Position 4 = last (highest) number.**

For number k to appear in position p (where p = 0, 1, 2, 3, 4):

**Number of combinations:**

```
Combinations = C(k-1, p) × C(max_number - k, 4-p)
```

**What each part means:**

- `C(k-1, p)` = Number of ways to choose the p numbers that come before k (from numbers 1 to k-1)
- `C(max_number - k, 4-p)` = Number of ways to choose the (4-p) numbers that come after k (from numbers k+1 to max_number)

**Probability:**

```
P(k in position p) = C(k-1, p) × C(max_number - k, 4-p) / C(max_number, 5)
```

**Key insight:** The formula automatically handles dependencies (e.g., for 2 to be in position 1, the number 1 must be in position 0). Different numbers have different probabilities at the same position.

**Examples (Mega Millions, max_number = 70):**

- Number 1 in position 0: `C(0,0) × C(69,4) / C(70,5) = 1 × 864,501 / 12,103,014 ≈ 7.14%`
- Number 2 in position 1: `C(1,1) × C(68,3) / C(70,5) = 1 × 50,116 / 12,103,014 ≈ 0.41%`
- Number 35 in position 2: `C(34,2) × C(35,2) / C(70,5) = 561 × 595 / 12,103,014 ≈ 2.76%`

**Step-by-Step Method for Position-Specific Statistics (Exact Method):**

1. **Calculate the Expected Probability:**

   ```
   Expected probability = C(k-1, p) × C(max_number - k, 4-p) / C(max_number, 5)
   ```

   Example: For number 2 in position 1 (Mega Millions): `50,116 / 12,103,014 ≈ 0.00414` or `0.414%`

2. **Calculate Expected Count:**

   ```
   Expected count = Expected probability × Total drawings
   ```

   Example: If there have been 1,000 drawings: `Expected count = 0.00414 × 1,000 ≈ 4.14`

3. **Compare to Observed Count:**

   ```
   Observed percentage = (Observed count / Total drawings) × 100%
   ```

   Example: If 2 appeared in position 1 exactly 8 times: `Observed percentage = 8/1,000 = 0.8%`

4. **Test for Statistical Significance (Z-test):**

   ```
   z = (Observed - Expected) / √(n × p × (1-p))
   ```

   Where:

   - `n` = number of drawings
   - `p` = expected probability
   - `Observed` = observed count
   - `Expected` = n × p

   Example:

   - `n = 1,000` drawings
   - `p = 0.00414`
   - `Expected = 4.14`
   - `Observed = 8`
   - `z = (8 - 4.14) / √(1000 × 0.00414 × 0.99586) ≈ 1.90`

5. **Interpret the Z-score:**

   - `|z| < 1.96`: Not statistically significant (95% confidence)
   - `|z| > 1.96`: Statistically significant at 95% level
   - `|z| > 2.58`: Statistically significant at 99% level

   In the example above, `z ≈ 1.90`, so it's not quite a significant outlier at the 95% level.

**Important Caveats:**

⚠️ **Multiple Comparison Problem:** If you're checking all numbers across all positions (e.g., 70 numbers × 5 positions = 350 tests), you'd expect some "outliers" by chance alone. Use Bonferroni correction: divide your significance level (0.05) by number of tests (350) = `0.000143` for true significance.

⚠️ **Sample Size Matters:** Need enough drawings for the test to be reliable. Generally want expected count ≥ 5.

**Note:** The current implementation uses a simplified uniform approximation where each position has `(max_number - 4)` possible numbers, giving each number an equal probability of `1/(max_number - 4)` at that position. This approximation simplifies calculations while still providing useful statistical insights, though the true probabilities vary by number and position as shown above. The exact method described here could be implemented for more precise position-specific statistics.

**Calculation Method:**

For each number, the standardized residual is calculated as:

```
residual = (observed - expected) / standard_deviation
```

Where:

- **Expected frequency**:
  - Regular numbers: `(total_draws × 5) / max_number` (exact combinatorial result)
  - Position-specific: `total_draws / (max_number - 4)` (simplified uniform approximation; true probability varies by number and position as `C(k-1, p) × C(max_number - k, 4-p) / C(max_number, 5)`)
  - Special ball: `total_draws / max_number`
- **Standard deviation**: Uses exact binomial formula: `√(n × p × (1-p))`
  - `n` = number of draws
  - `p` = probability of number being selected in a single draw
  - For regular numbers: `p = 5/70` (Mega Millions) or `p = 5/69` (Powerball)
  - For position-specific: `p = 1/66` (Mega Millions) or `p = 1/65` (Powerball) - simplified uniform approximation (true probability is `C(k-1, p) × C(max_number - k, 4-p) / C(max_number, 5)`)
  - For special ball: `p = 1/25` (Mega Millions) or `p = 1/26` (Powerball)

This binomial approach is more accurate than Poisson approximation, especially for smaller sample sizes, as it accounts for the fixed number of selections per draw.

**Example (Regular Numbers, 1,000 draws):**

- Expected: `(1000 × 5) / 70 = 71.43` appearances
- Standard deviation: `√(1000 × (5/70) × (65/70)) ≈ 8.14`
- Normal range (95% confidence): `71.43 ± 16.28` (approximately 55-87 appearances)
- Numbers outside this range are statistically significant

**Example (Special Ball, 1,000 draws):**

- Expected: `1000 / 25 = 40` appearances
- Standard deviation: `√(1000 × (1/25) × (24/25)) ≈ 6.20`
- Normal range (95% confidence): `40 ± 12.4` (approximately 28-52 appearances)

### Percent Field

The `percent` field represents the percentage frequency of each number:

- **Regular numbers**: `percent = (observed / total_slots) * 100` where `total_slots = number_of_draws * 5`

  - Since each draw has 5 regular numbers, this shows the percentage of all regular number slots that this number occupies
  - Example: If a number appears 50 times out of 100 draws (500 total slots), percent = (50 / 500) \* 100 = 10%

- **Position-specific (byPosition)**: `percent = (observed / total_draws) * 100`

  - Shows the percentage of draws where this number appeared at this specific position
  - Note: Expected frequency accounts for the fact that each position has fewer possible numbers (66 for Mega Millions, 65 for Powerball)
  - Example: If a number appears 30 times at position 0 out of 100 draws, percent = (30 / 100) \* 100 = 30%

- **Special ball**: `percent = (observed / total_draws) * 100`
  - Shows the percentage of draws where this special ball number appeared
  - Example: If a special ball number appears 5 times out of 100 draws, percent = (5 / 100) \* 100 = 5%

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

**Method 1: Manual HTTP Request**

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe lottery-scraper --region us-central1 --format 'value(status.url)')

# Trigger the scraper via HTTP
curl -X POST $SERVICE_URL
```

**Method 2: Cloud Scheduler (Automated Daily at 11:59 PM)**

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe lottery-scraper --region us-central1 --format 'value(status.url)')

# Create a scheduled job to run daily at 11:59 PM UTC
gcloud scheduler jobs create http lottery-scraper-daily \
  --location=us-central1 \
  --schedule="59 23 * * *" \
  --uri="$SERVICE_URL" \
  --http-method=POST \
  --time-zone="UTC"

# To use a different timezone (e.g., US Eastern Time)
gcloud scheduler jobs create http lottery-scraper-daily \
  --location=us-central1 \
  --schedule="59 23 * * *" \
  --uri="$SERVICE_URL" \
  --http-method=POST \
  --time-zone="America/New_York"
```

**Method 3: From Cloud Console**

1. Go to Cloud Run in Google Cloud Console
2. Click on your `lottery-scraper` service
3. Click "TESTING" tab
4. Click "TRIGGER" button to send a test request

**Health check:**

```bash
curl $SERVICE_URL/health
```

**Notes for Cloud Run:**

- The service listens on the `PORT` environment variable (default 8080, Cloud Run provides this)
- Data is saved to GCS (configured via `LOTTERY_DATA_SCRAPER_BUCKET`)
- The service responds to HTTP requests and runs the scraper on each POST/GET to `/`
- **Recommended**: Use Cloud Scheduler (Method 2 above) to automatically run daily at 11:59 PM
- Each trigger runs the scraper once and returns a JSON response

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
