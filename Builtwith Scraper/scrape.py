import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from retrying import retry
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the base URL for BuiltWith relationships
BASE_URL = "https://builtwith.com/relationships/"

# User-Agent list for rotating to avoid being blocked
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
]

# Define a function to perform a retryable request with error handling
@retry(wait_fixed=2000, stop_max_attempt_number=3)
def make_request(url):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers)

        # Check for forbidden access
        if response.status_code == 403:
            logging.warning(f"Forbidden to lookup {url}. Skipping this URL.")
            return None
        
        # Handle other unsuccessful status codes
        if response.status_code != 200:
            logging.error(f"Failed to retrieve {url}. Status Code: {response.status_code}")
            raise Exception(f"Failed to retrieve {url}")

        # Return the response content if the request is successful
        return response
    except Exception as e:
        # Log the exception and return None to skip the URL
        logging.error(f"Error occurred when making request to {url}: {str(e)}. Skipping this URL.")
        return None

# Define a function to scrape the domains associated with a tag
def scrape_domains(domain, level, processed_tag_ids, all_results):
    url = f"{BASE_URL}{domain}"
    
    # Request the page with retry mechanism
    response = make_request(url)
    if response is None:
        return pd.DataFrame()  # Return an empty dataframe if forbidden or error
    
    # Parse the HTML response using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Look for the "Forbidden" message and handle it
    if "The website says we are forbidden to do a lookup on it." in soup.text:
        logging.warning(f"Forbidden to lookup domain: {domain}")
        return pd.DataFrame()
    
    # Find all table rows with class "tbomb"
    rows = soup.find_all('td', class_='hbomb')
    
    # Initialize a list to hold the results
    result = []
    track_tag_ids = set()  # Track processed tag_ids
    
    # Iterate through the rows and extract relevant information
    for row in rows:

        # Extract the domain from the <a> tag
        a_tag = row.find('a')
        if a_tag is None:
            continue # Skip if no <a> tag is found

        domain_name = a_tag.text.strip()

        # Extract the relationships attribute
        tag_id = row.get('relationships')

        # Skip processing if this tag_id has been processed before
        if tag_id in processed_tag_ids:
            # logging.info(f"{domain}: Skipping tag_id {tag_id} since it has been processed before.")
            continue  # Skip all domains associated with this tag_id

        # Check if this domain already exists in all_results
        if not all_results[all_results['Domain'] == domain_name].empty:
            logging.info(f"<{domain}> Domain {domain_name} already exists in all_results. Appending tag.")
            
            # If the domain already exists, append the tag info to its 'Connection' or create a 'Tags' field
            all_results.loc[all_results['Domain'] == domain_name, 'Connection'] += f", {tag_id}"
        else:
            logging.info(f"<{domain}> Adding: {domain_name}: {tag_id}")
            # If the domain doesn't exist, add it to the results
            result.append({
                'Domain': domain_name,
                'Relationship': domain,
                'Connection': tag_id,
                'Level': level
            })

        # After processing, mark the tag_id as processed
        track_tag_ids.add(tag_id)
    
    # Add the tag_ids to the processed_tag_ids set
    processed_tag_ids.update(track_tag_ids)
    return pd.DataFrame(result)

# Define a function to pause between requests to avoid rate limiting
def rate_limit_pause(min_time=3, max_time=10):
    time_to_sleep = random.uniform(min_time, max_time)
    logging.info(f"Sleeping for {time_to_sleep:.2f} seconds to avoid rate limiting.")
    time.sleep(time_to_sleep)

# Define the recursive scrape function
def recursive_scrape(start_domains, max_level=3):
    # Initialize a dataframe to store all results
    all_results = pd.DataFrame(columns=['Domain', 'Type', 'Relationship', 'Connection', 'Level', 'Comment'])

    # Initialize a set to track processed domains and avoid duplicates
    processed_domains = set()
    processed_tag_ids = set()  # Track processed tag_ids
    
    # Define a list to hold domains for processing at each level
    domains_to_process = {1: start_domains}
    
    # Loop through levels
    for level in range(1, max_level + 1):
        logging.info(f"Processing level {level}...")
        new_domains = []
        for domain in domains_to_process[level]:
            # Skip domains that have already been processed
            if domain in processed_domains:
                logging.info(f"Skipping already processed domain: {domain}")
                continue
            
            # Scrape the domains for the current domain
            df = scrape_domains(domain, level=level, processed_tag_ids=processed_tag_ids, all_results=all_results)


            if df is not None and not df.empty:
                # Append the new data, ensuring that all_results stays unique
                all_results = pd.concat([all_results, df], ignore_index=True).drop_duplicates(subset='Domain')
                # Add the new domains to be processed at the next level
                new_domains.extend(df['Domain'].unique())
                
            # Mark the domain as processed
            processed_domains.add(domain)
            logging.info(f"Updated new processed domains: {processed_domains}")
            
            # Sleep for a short time to avoid rate-limiting
            rate_limit_pause()
        
        # Prepare for the next level
        if level + 1 <= max_level:
            domains_to_process[level + 1] = new_domains
    
    # Add the start domains to the results as level 0 (after)
    start_data = pd.DataFrame({
        'Domain': start_domains,
        'Type': 'Streaming',
        'Relationship': '',
        'Connection': '',
        'Level': 0,
        'Comment': ''
    })
    all_results = pd.concat([all_results, start_data], ignore_index=True)

    return all_results

# Load domains from the Excel file
file_path = 'process.xlsx'
excel_data = pd.read_excel(file_path)

# Extract domains from the 'Domain' column
start_domains = excel_data['Domain'].dropna().unique()

# Perform the recursive scrape
final_df = recursive_scrape(start_domains, max_level=3)

# Save the results to a CSV file
final_df.to_excel('result.xlsx', index=False)

# Output final dataframe
print(final_df)
