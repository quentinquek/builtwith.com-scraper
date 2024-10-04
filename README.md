# Builtwith.com Scraper
This Python script is designed to scrape domain relationships from BuiltWith by recursively following links from one domain to another. The script extracts the domains associated with a given start domain, tracks the connections between them, and stores the results in an Excel file. It is useful for analyzing domain relationships, tagging domains based on certain criteria (e.g., piracy-related or legitimate), and understanding network infrastructure.

The script handles network issues with a retry mechanism, uses random pauses to avoid rate-limiting, and rotates user-agent strings to reduce the chances of being blocked.

## Features
- Recursive Domain Scraping: Scrapes domains up to a specified number of levels (default: 3 levels deep).
> Level 0 is the starting domain(s), Level 1 is the domain(s) gotten from Level 0, and so on and so forth.
- Retry Mechanism: Automatically retries failed requests up to 3 times, handling temporary issues like network problems.
- Rate-Limiting Avoidance: Implements random delays between requests to mimic human browsing behavior and avoid being flagged as a bot.
- Duplicate Tag and Domain Prevention: Tracks processed domains and tags to avoid duplicating entries.
- User-Agent Rotation: Rotates between multiple user-agent strings to reduce the risk of being blocked by the target site.
- Logging: Provides detailed logging to track progress and any issues encountered during scraping.

## Installation
To use the script, you need to have [Python 3.x](https://www.python.org/downloads/) installed, along with several required libraries.

You can install the required dependencies using the following command:
```
pip install requests beautifulsoup4 pandas retrying openpyxl
```
OR for Python 3:
```
pip3 install requests beautifulsoup4 pandas retrying openpyxl
```

### Usage
1. Prepare Input Excel File
- Duplicate the `template.xlsx` Excel file.
- Rename it to `process.xlsx`.
- Input all the domain(s) to be processed in the `Domain` column, which should have the list of domains you want to start scraping from.

2. Run the Script
- To execute the script, run the following command:
```
python process.xlsx.py
```
OR Python 3:
```
python3 process.xlsx.py
```

3. The results will be saved in an Excel file (result.xlsx). Here's an example output:

![image](https://github.com/user-attachments/assets/20a5e738-f648-4b34-8bcb-0d1e82c5e35a)
