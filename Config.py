from typing import List, Tuple, Optional

# List of search keywords (strings). Example: ["coffee shop", "pizza"]
KEYWORDS: List[str] = ["clinique"]

LOCATIONS: List[str] = ["algeria draria", "algeria saoula", "algeria birkhadem"]

# Optional categories to append to queries (can be empty)
CATEGORIES: List[str] = [""]

# Output path for results
OUTPUT_PATH: str = "output.xlsx"

# Maximum results to attempt to collect per query
MAX_RESULTS_PER_QUERY: int = 100

# Run browser headless or not (use False for debugging)
HEADLESS: bool = False

# Use Playwright for Google Maps scraping
USE_PLAYWRIGHT: bool = True

# Use proxies (placeholder flag for future use)
USE_PROXIES: bool = False

# Min/max delay between actions (seconds)
DELAY_RANGE: Tuple[int, int] = (2, 5)

# Optional user agent override (None to use default)
USER_AGENT: Optional[str] = None
