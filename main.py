"""Main orchestrator for OpenReview Conference Email Outreach."""
import os
import yaml
from dotenv import load_dotenv

from src.scraper.openreview_scraper import OpenReviewScraper
from src.research.venue_researcher import VenueResearcher
from src.email.generator import EmailGenerator
from src.email.sender import EmailSender
from src.utils.csv_handler import save_to_csv, read_from_csv


def load_config():
    """Load configuration from YAML files and environment variables."""
    load_dotenv()

    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    with open('config/user_profile.yaml', 'r') as f:
        user_profile = yaml.safe_load(f)

    return config, user_profile


def phase1_scrape_conferences(config):
    """Phase 1: Scrape OpenReview for conferences and emails."""
    print("=" * 60)
    print("PHASE 1: Scraping OpenReview Conferences")
    print("=" * 60)

    scraper = OpenReviewScraper()
    conferences = scraper.scrape_open_submissions()

    save_to_csv(
        conferences,
        config['output']['conferences_csv'],
        fieldnames=['name', 'url', 'email']
    )

    print(f"✓ Scraped {len(conferences)} conferences")
    print(f"✓ Saved to {config['output']['conferences_csv']}")
    return conferences


def phase2_research_venues(config, conferences):
    """Phase 2: Research venues using Exa.ai."""
    print("\n" + "=" * 60)
    print("PHASE 2: Researching Venues with Exa.ai")
    print("=" * 60)

    exa_api_key = os.getenv('EXA_API_KEY')
    if not exa_api_key:
        print("ERROR: EXA_API_KEY not found in environment variables")
        return []

    researcher = VenueResearcher(exa_api_key)

    venue_research = []
    for idx, conf in enumerate(conferences, 1):
        print(f"[{idx}/{len(conferences)}] {conf['name']}")

        research_data = researcher.research_venue(conf['name'], conf['url'])

        # Format highlights and topics for CSV storage
        highlights_text = " | ".join(research_data['highlights'][:5])  # Max 5 highlights
        if len(highlights_text) > 500:
            highlights_text = highlights_text[:497] + "..."

        topics_text = ", ".join(research_data['key_topics'])

        venue_research.append({
            'name': conf['name'],
            'url': conf['url'],
            'email': conf['email'],
            'key_topics': topics_text,
            'highlights': highlights_text
        })

    save_to_csv(
        venue_research,
        config['output']['venue_research_csv'],
        fieldnames=['name', 'url', 'email', 'key_topics', 'highlights']
    )

    print(f"\n✓ Researched {len(venue_research)} venues")
    print(f"✓ Saved to {config['output']['venue_research_csv']}")
    return venue_research


def phase3_generate_emails(config, user_profile, venue_research):
    """Phase 3: Generate personalized emails using OpenAI."""
    print("\n" + "=" * 60)
    print("PHASE 3: Generating Personalized Emails")
    print("=" * 60)

    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return []

    # Pass email generation config to generator
    email_config = config['email_generation']
    generator = EmailGenerator(openai_api_key, user_profile, email_config)

    emails = []
    skipped = 0
    for idx, venue in enumerate(venue_research, 1):
        print(f"[{idx}/{len(venue_research)}] {venue['name']}")

        email_content = generator.generate_email(venue, venue)

        if email_content:
            emails.append({
                'venue_name': venue['name'],
                'to_email': venue['email'],
                'subject': f"Reviewer Opportunity - {venue['name']}",
                'body': email_content
            })
        else:
            # No matching interests - skip this venue
            skipped += 1
            emails.append({
                'venue_name': venue['name'],
                'to_email': venue['email'],
                'subject': f"Reviewer Opportunity - {venue['name']}",
                'body': 'No match - interests do not align'
            })

    save_to_csv(
        emails,
        config['output']['emails_csv'],
        fieldnames=['venue_name', 'to_email', 'subject', 'body']
    )

    print(f"\n✓ Generated {len(emails) - skipped} personalized emails")
    print(f"✓ Skipped {skipped} venues (no matching interests)")
    print(f"✓ Saved to {config['output']['emails_csv']}")
    return emails


def phase4_send_emails(config, user_profile, emails):
    """Phase 4: Send emails via SMTP."""
    print("\n" + "=" * 60)
    print("PHASE 4: Sending Emails")
    print("=" * 60)

    smtp_config = {
        'host': config['smtp']['host'],
        'port': config['smtp']['port'],
        'use_tls': config['smtp']['use_tls'],
        'username': os.getenv('EMAIL_ADDRESS'),
        'password': os.getenv('EMAIL_PASSWORD')
    }

    sender = EmailSender(smtp_config)
    from_email = user_profile['email']

    sent_count = 0
    for email in emails:
        success = sender.send_email(
            email['to_email'],
            email['subject'],
            email['body'],
            from_email
        )
        if success:
            sent_count += 1

    print(f"✓ Sent {sent_count}/{len(emails)} emails successfully")


def main():
    """Main execution flow."""
    print("\n🚀 OpenReview Conference Email Outreach Tool\n")

    # Load configuration
    config, user_profile = load_config()

    # Phase 1: Scrape conferences
    conferences = phase1_scrape_conferences(config)

    # Phase 2: Research venues
    venue_research = phase2_research_venues(config, conferences)

    # Phase 3: Generate emails
    emails = phase3_generate_emails(config, user_profile, venue_research)

    # Phase 4: Send emails
    response = input("\n⚠️  Ready to send emails? (yes/no): ")
    if response.lower() == 'yes':
        phase4_send_emails(config, user_profile, emails)
    else:
        print("✓ Emails not sent. Review emails.csv and run phase 4 manually.")

    print("\n✅ All phases completed!\n")


if __name__ == "__main__":
    main()
