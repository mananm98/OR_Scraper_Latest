"""Scraper for OpenReview.net conferences."""
import re
import time
import requests
from bs4 import BeautifulSoup


class OpenReviewScraper:
    """Scrapes conference information from OpenReview.net."""

    def __init__(self, delay=1.5):
        """
        Initialize the scraper.

        Args:
            delay: Delay in seconds between requests (default: 1.5)
        """
        self.base_url = "https://openreview.net"
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def scrape_open_submissions(self):
        """
        Scrape all conferences from the 'Open for Submissions' section.

        Returns:
            list: List of conference dictionaries with name, url, and email
        """
        print(f"Fetching homepage: {self.base_url}")

        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching homepage: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the "Open for Submissions" section
        open_submissions_section = None
        for section in soup.find_all('section'):
            h1 = section.find('h1')
            if h1 and 'Open for Submissions' in h1.get_text():
                open_submissions_section = section
                break

        if not open_submissions_section:
            print("Could not find 'Open for Submissions' section")
            return []

        # Extract all conference links
        conference_links = open_submissions_section.find_all('a', href=re.compile(r'/group\?id='))
        print(f"Found {len(conference_links)} conferences")

        conferences = []
        for idx, link in enumerate(conference_links, 1):
            conference_name = link.get_text(strip=True)
            conference_path = link.get('href')
            conference_url = self.base_url + conference_path if conference_path.startswith('/') else conference_path

            print(f"[{idx}/{len(conference_links)}] Processing: {conference_name}")

            # Get email from conference page
            email = self.get_conference_email(conference_url)

            conferences.append({
                'name': conference_name,
                'url': conference_url,
                'email': email if email else 'Not found'
            })

            # Rate limiting
            if idx < len(conference_links):
                time.sleep(self.delay)

        return conferences

    def get_conference_email(self, conference_url):
        """
        Extract email from a specific conference page.

        Args:
            conference_url: URL of the conference page

        Returns:
            str: Email address or None if not found
        """
        try:
            response = self.session.get(conference_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  Error fetching {conference_url}: {e}")
            return None

        # Extract all emails from the page
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        matches = re.findall(email_pattern, response.text)

        if matches:
            # Filter out OpenReview system emails
            excluded_domains = ['openreview.net']
            excluded_keywords = ['noreply', 'notification', 'no-reply']

            # Track unique emails to avoid duplicates
            seen_emails = set()

            for email in matches:
                email_lower = email.lower()

                # Skip if already seen
                if email_lower in seen_emails:
                    continue

                # Skip system emails
                if any(domain in email_lower for domain in excluded_domains):
                    continue
                if any(keyword in email_lower for keyword in excluded_keywords):
                    continue

                seen_emails.add(email_lower)
                print(f"  Found email: {email}")
                return email

        print(f"  No valid email found")
        return None
