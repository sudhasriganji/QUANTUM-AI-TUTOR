import requests
from bs4 import BeautifulSoup

def scrape_ibm_quantum_docs(url="https://quantum.cloud.ibm.com/docs/en/guides/tools-intro"):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch documentation page: {response.status_code}")

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Target main content area
    main_content = soup.find('main') or soup.find('body')
    text = main_content.get_text(separator='\n', strip=True) if main_content else ""
    
    with open("scraped_docs.txt", "w", encoding="utf-8") as f:
        f.write(text)
        
    print("Scraping finished. Saved content to scraped_docs.txt")
    return text

if __name__ == "__main__":
    scrape_ibm_quantum_docs()