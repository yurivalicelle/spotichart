from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup

class ScraperStrategy(ABC):
    @abstractmethod
    def scrape(self, url: str, limit: int) -> list:
        pass
    
    @abstractmethod
    def get_supported_domains(self) -> list:
        pass

class KworbScraperStrategy(ScraperStrategy):
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def get_supported_domains(self) -> list:
        return ['kworb.net', 'www.kworb.net']

    def scrape(self, url: str, limit: int) -> list:
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table')
            if not table:
                return []
            
            tracks = []
            # Search for rows directly in the table, not tbody
            rows = table.find_all('tr', limit=limit) 
            
            for row in rows:
                # Find a link that contains 'track/' in its href
                link = row.find('a', href=lambda href: href and 'track/' in href)
                if link:
                    href = link.get('href', '')
                    # Handle both relative and absolute URLs
                    track_id = href.split('track/')[-1].replace('.html', '')
                    tracks.append(track_id)
            return tracks
        except Exception:
            return []
