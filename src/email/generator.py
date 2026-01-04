"""Email generation using OpenAI API."""
import time
from typing import Dict, Optional
from openai import OpenAI
from openai import (
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIError,
    APITimeoutError
)


class EmailGenerator:
    """Generates personalized emails using OpenAI."""

    def __init__(self, api_key: str, user_profile: Dict, config: Optional[Dict] = None):
        """
        Initialize the email generator.

        Args:
            api_key: OpenAI API key
            user_profile: Dictionary with user interests and capabilities
            config: Optional configuration dict with model settings
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.user_profile = user_profile

        # Configuration with defaults
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-5')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_tokens', 450)
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)

        print(f"Initialized EmailGenerator with model: {self.model}")

    def _build_system_message(self) -> str:
        """
        Build the system message that defines AI behavior.

        Returns:
            str: System message content
        """
        return """You are a professional Academic Peer. You write with brevity, confidence, and zero fluff. You do not use "AI-isms" like "I hope this finds you well" or "I am writing to."

Your emails are:
- Professional but approachable (not overly formal or salesy)
- Concise (200-300 words maximum)
- Personalized based on conference topics and researcher interests
- Action-oriented with clear next steps

Tone: Collegial academic professional - enthusiastic but respectful.
Focus on genuine interest and fit, not flattery."""

    def _build_user_message(self, venue_info: Dict) -> str:
        """
        Build the user message with venue and researcher details.

        Args:
            venue_info: Dictionary with venue information

        Returns:
            str: Formatted user message
        """
        # Extract researcher info
        researcher_name = self.user_profile.get('name', 'the researcher')
        affiliation = self.user_profile.get('affiliation', '')

        # Extract new profile fields
        identity = self.user_profile.get('identity', '')
        publications = self.user_profile.get('publications', [])
        expertise = self.user_profile.get('expertise', [])

        # Format publications as a string
        if isinstance(publications, list):
            publications_str = ' '.join(publications)
        else:
            publications_str = str(publications)

        # Format expertise as domain/focus pairs
        if isinstance(expertise, list):
            expertise_str = ', '.join([f"{e.get('domain', '')} ({e.get('focus', '')})"
                                       for e in expertise if isinstance(e, dict)])
        else:
            expertise_str = str(expertise)

        # Extract venue info
        venue_name = venue_info.get('name', 'the conference')
        key_topics = venue_info.get('key_topics', '')
        highlights = venue_info.get('highlights', '')

        # Truncate highlights if too long
        if len(highlights) > 500:
            highlights = highlights[:497] + "..."

        prompt = f"""Write a direct proposal to the {venue_name} organizers to serve as a reviewer.

CONFERENCE DETAILS:
- Name: {venue_name}
- Key Topics: {key_topics}
- Conference Highlights: {highlights}

USER CONTEXT:
- My Identity: {researcher_name}, {affiliation}. {identity}
- Relevant Proof: {publications_str}
- My Expertise: {expertise_str}

CONSTRAINTS:
1. MATCHING: Identify exactly 2 intersections between the venue's topics ({key_topics}) and my expertise ({expertise_str}).
2. TONE: Write as a peer offering a service, not a student asking for a spot.
3. BREVITY: Max 150 words.
4. STRUCTURE: 
   - Sentence 1: Direct statement of intent.
   - Sentence 2-3: Evidence of specific expertise matching their track.
   - Sentence 4: The value I provide (e.g., "I can provide rigorous reviews for papers involving [Topic]").
5. NO SIGN-OFF: End the text immediately after the last content sentence. Do NOT include "Sincerely," "Thank you," or your name.

NEGATIVE CONSTRAINTS:
- DO NOT use the phrase "I hope this message finds you well."
- DO NOT list full paper titles in quotes; describe the contribution instead.
- DO NOT use the word "passionate" or "keen."

Email Body:"""

        return prompt

    def _call_openai_api(self, messages: list) -> str:
        """
        Call OpenAI API with retry logic.

        Args:
            messages: List of message dicts

        Returns:
            str: Generated email content

        Raises:
            ValueError: Invalid API key
            RuntimeError: API errors after retries
        """
        retry_delay = 1

        for attempt in range(self.max_retries):
            try:
                # Use max_completion_tokens for newer models (gpt-4o, gpt-4o-mini, etc.)
                # Fall back to max_tokens for older models
                completion_params = {
                    'model': self.model,
                    'messages': messages,
                    'temperature': self.temperature,
                    'timeout': self.timeout
                }

                # Newer models use max_completion_tokens
                if 'gpt-4o' in self.model or 'gpt-5' in self.model or 'o1' in self.model:
                    completion_params['max_completion_tokens'] = self.max_tokens
                else:
                    completion_params['max_tokens'] = self.max_tokens

                response = self.client.chat.completions.create(**completion_params)

                email_content = response.choices[0].message.content
                return email_content.strip()

            except AuthenticationError as e:
                raise ValueError(f"Invalid OpenAI API key: {e}")

            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    print(f"  Rate limit hit, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise RuntimeError(f"Rate limit exceeded after {self.max_retries} attempts: {e}")

            except APIConnectionError as e:
                if attempt < self.max_retries - 1:
                    print(f"  Connection error, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise RuntimeError(f"Connection failed after {self.max_retries} attempts: {e}")

            except APITimeoutError as e:
                raise RuntimeError(f"Request timeout after {self.timeout}s: {e}")

            except APIError as e:
                raise RuntimeError(f"OpenAI API error: {e}")

        raise RuntimeError("Failed to generate email after retries")

    def generate_email(self, venue_info: Dict, research_data: Dict = None) -> Optional[str]:
        """
        Generate personalized email for a venue.

        Args:
            venue_info: Dictionary with venue information
            research_data: Optional additional research data (unused)

        Returns:
            str: Generated email content, or None if no matching interests
        """
        # Validate inputs
        if not venue_info:
            raise ValueError("venue_info is required")

        if not venue_info.get('name'):
            raise ValueError("venue_info must contain 'name'")

        # Build messages
        system_message = self._build_system_message()
        user_message = self._build_user_message(venue_info)

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        # Generate email
        print(f"  Generating email for {venue_info.get('name')}...")
        email_content = self._call_openai_api(messages)

        # Check if response is NULL (no matching interests)
        if email_content.strip().upper() == "NULL":
            print(f"    No matching interests - skipping")
            return None

        # Add signature (use provided signature or generate default)
        signature = self.user_profile.get('signature', '')
        if not signature:
            # Generate default signature from name
            researcher_name = self.user_profile.get('name', 'the researcher')
            signature = f"Best regards,\n{researcher_name}"

        email_content = f"{email_content}\n\n{signature}"

        return email_content
