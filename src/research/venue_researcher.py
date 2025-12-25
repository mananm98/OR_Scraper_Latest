"""Venue research using Exa.ai API."""
from exa_py import Exa


class VenueResearcher:
    """Researches venue information using Exa.ai."""

    def __init__(self, api_key):
        """
        Initialize the researcher.

        Args:
            api_key: Exa.ai API key
        """
        self.api_key = api_key
        self.client = Exa(api_key=api_key)

    def research_venue(self, venue_name, venue_url, num_results=5):
        """
        Research venue using Exa.ai to gather highlights and key topics.

        Args:
            venue_name: Name of the venue
            venue_url: URL of the venue
            num_results: Number of search results (default: 5)

        Returns:
            dict: Venue research information with highlights and key_topics
        """
        print(f"  Researching: {venue_name}")

        # Build search query
        query = self._build_search_query(venue_name)

        # Search with highlights
        highlights = self._search_with_highlights(query, num_results)

        # Extract key topics from highlights
        key_topics = self._extract_key_topics(highlights)

        # Print highlights
        if highlights:
            print(f"    Highlights:")
            for i, highlight in enumerate(highlights[:5], 1):  # Show first 5
                print(f"      {i}. {highlight}")
        else:
            print(f"    No highlights found")

        return {
            'highlights': highlights,
            'key_topics': key_topics
        }

    def _build_search_query(self, venue_name):
        """
        Build optimized search query for the venue.

        Args:
            venue_name: Name of the venue

        Returns:
            str: Search query
        """
        # Focus on finding conference topics and scope
        return f"{venue_name} call for papers research topics scope"

    def _search_with_highlights(self, query, num_results):
        """
        Perform Exa search and extract highlights.

        Args:
            query: Search query
            num_results: Number of results to retrieve

        Returns:
            list: List of highlight strings
        """
        try:
            response = self.client.search_and_contents(
                query,
                type="neural",
                num_results=num_results,
                highlights={
                    "highlights_per_url": 3,
                    "num_sentences": 2,
                    "query": query
                }
            )

            # Collect all highlights
            all_highlights = []
            for result in response.results:
                if hasattr(result, 'highlights') and result.highlights:
                    all_highlights.extend(result.highlights)

            return all_highlights

        except Exception as e:
            print(f"    Error during Exa search: {str(e)}")
            return []

    def _extract_key_topics(self, highlights):
        """
        Extract key topics from highlights using keyword matching.

        Args:
            highlights: List of highlight strings

        Returns:
            list: List of key topic strings
        """
        topics = set()

        # Combine all highlights into one text
        all_text = " ".join(highlights).lower()

        # Topic keywords to look for
        topic_keywords = {
            "Machine Learning": ["machine learning", "ml", "deep learning", "neural network"],
            "Natural Language Processing": ["nlp", "natural language", "language model", "text mining"],
            "Computer Vision": ["computer vision", "image processing", "visual", "cv"],
            "AI": ["artificial intelligence", "ai"],
            "Theory": ["theory", "theoretical", "algorithm"],
            "Data Science": ["data science", "data mining", "analytics"],
            "Robotics": ["robotics", "robot", "autonomous"],
            "Healthcare": ["healthcare", "medical", "clinical", "health"],
            "Security": ["security", "privacy", "cryptography"],
            "Systems": ["systems", "distributed", "cloud", "infrastructure"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                topics.add(topic)

        return list(topics) if topics else ["General Computer Science"]
