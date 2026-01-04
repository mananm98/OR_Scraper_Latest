"""Live run of the full pipeline with 7 conferences - SENDS REAL EMAILS."""
import os
import yaml
from dotenv import load_dotenv

from src.scraper.openreview_scraper import OpenReviewScraper
from src.research.venue_researcher import VenueResearcher
from src.email.generator import EmailGenerator
from src.email.sender import EmailSender
from src.utils.csv_handler import save_to_csv

# Number of conferences to process
NUM_CONFERENCES = 7

def main():
    """Run the full pipeline with 7 conferences and send real emails."""
    print("\n" + "=" * 60)
    print(f"LIVE RUN - {NUM_CONFERENCES} CONFERENCES")
    print("⚠️  THIS WILL SEND REAL EMAILS ⚠️")
    print("=" * 60)

    # Load configuration
    load_dotenv()
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    with open('config/user_profile.yaml', 'r') as f:
        user_profile = yaml.safe_load(f)

    # ========== PHASE 1: Scrape Conferences ==========
    print("\n" + "=" * 60)
    print("PHASE 1: Scraping OpenReview Conferences")
    print("=" * 60)

    scraper = OpenReviewScraper()
    all_conferences = scraper.scrape_open_submissions()

    # Limit to NUM_CONFERENCES for this run
    conferences = all_conferences[:NUM_CONFERENCES]

    print(f"\n✓ Scraped {len(all_conferences)} total conferences")
    print(f"✓ Processing first {len(conferences)} conferences")

    save_to_csv(
        conferences,
        'live_conferences.csv',
        fieldnames=['name', 'url', 'email']
    )

    # ========== PHASE 2: Research Venues ==========
    print("\n" + "=" * 60)
    print("PHASE 2: Researching Venues with Exa.ai")
    print("=" * 60)

    exa_api_key = os.getenv('EXA_API_KEY')
    researcher = VenueResearcher(exa_api_key)

    venue_research = []
    for idx, conf in enumerate(conferences, 1):
        print(f"\n[{idx}/{len(conferences)}] {conf['name']}")

        research_data = researcher.research_venue(conf['name'], conf['url'])

        highlights_text = " | ".join(research_data['highlights'][:5])
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
        'live_research.csv',
        fieldnames=['name', 'url', 'email', 'key_topics', 'highlights']
    )
    print(f"\n✓ Researched {len(venue_research)} venues")

    # ========== PHASE 3: Generate Emails ==========
    print("\n" + "=" * 60)
    print("PHASE 3: Generating Personalized Emails")
    print("=" * 60)

    openai_api_key = os.getenv('OPENAI_API_KEY')
    email_config = config['email_generation']
    generator = EmailGenerator(openai_api_key, user_profile, email_config)

    emails = []
    skipped = 0

    for idx, venue in enumerate(venue_research, 1):
        print(f"\n[{idx}/{len(venue_research)}] {venue['name']}")

        email_content = generator.generate_email(venue, venue)

        if email_content:
            emails.append({
                'venue_name': venue['name'],
                'to_email': venue['email'],
                'subject': f"Reviewer Opportunity - {venue['name']}",
                'body': email_content
            })
        else:
            skipped += 1
            emails.append({
                'venue_name': venue['name'],
                'to_email': venue['email'],
                'subject': f"Reviewer Opportunity - {venue['name']}",
                'body': 'No match - interests do not align'
            })

    save_to_csv(
        emails,
        'live_emails.csv',
        fieldnames=['venue_name', 'to_email', 'subject', 'body']
    )
    print(f"\n✓ Generated {len(emails) - skipped} personalized emails")
    print(f"✓ Skipped {skipped} venues (no matching interests)")

    # ========== PREVIEW EMAILS ==========
    print("\n" + "=" * 60)
    print("EMAIL PREVIEW")
    print("=" * 60)

    for idx, email in enumerate(emails, 1):
        if email['body'] == 'No match - interests do not align':
            print(f"\n[{idx}] {email['venue_name']}")
            print(f"    ⊘ SKIPPED - No matching interests")
        else:
            print(f"\n[{idx}] {email['venue_name']}")
            print(f"    TO: {email['to_email']}")
            print(f"    SUBJECT: {email['subject']}")
            preview = email['body'][:150] + "..." if len(email['body']) > 150 else email['body']
            print(f"    BODY: {preview}")

    # ========== CONFIRMATION ==========
    print("\n" + "=" * 60)
    print("⚠️  READY TO SEND REAL EMAILS")
    print("=" * 60)
    print(f"Total emails to send: {len(emails) - skipped}")
    print(f"Skipped (no match): {skipped}")
    print("\nThese emails will be sent to real recipients!")

    response = input("\nProceed with sending? (type 'SEND' to confirm, anything else to cancel): ")

    if response.strip() != 'SEND':
        print("\n❌ Cancelled. No emails sent.")
        print("✓ Generated emails saved to live_emails.csv for review")
        return

    # ========== PHASE 4: Send Emails (LIVE) ==========
    print("\n" + "=" * 60)
    print("PHASE 4: Sending Emails (LIVE MODE)")
    print("=" * 60)

    smtp_config = {
        'host': config['smtp']['host'],
        'port': config['smtp']['port'],
        'use_tls': config['smtp']['use_tls'],
        'username': os.getenv('EMAIL_ADDRESS'),
        'password': os.getenv('EMAIL_PASSWORD')
    }

    # dry_run=False means SEND REAL EMAILS
    sender = EmailSender(smtp_config, dry_run=False)
    from_email = user_profile['email']

    sent_count = 0
    failed_count = 0

    for idx, email in enumerate(emails, 1):
        print(f"\n[{idx}/{len(emails)}]")

        # Skip emails with no matching interests
        if email['body'] == 'No match - interests do not align':
            print(f"  ⊘ Skipping {email['venue_name']} - no matching interests")
            continue

        success = sender.send_email(
            email['to_email'],
            email['subject'],
            email['body'],
            from_email
        )

        if success:
            sent_count += 1
        else:
            failed_count += 1

    # ========== FINAL SUMMARY ==========
    print("\n" + "=" * 60)
    print("LIVE RUN SUMMARY")
    print("=" * 60)
    print(f"✓ Phase 1: Scraped {len(conferences)} conferences")
    print(f"✓ Phase 2: Researched {len(venue_research)} venues")
    print(f"✓ Phase 3: Generated {len(emails) - skipped} emails ({skipped} skipped)")
    print(f"✓ Phase 4: Sent {sent_count} emails successfully")
    if failed_count > 0:
        print(f"✗ Phase 4: {failed_count} emails failed to send")

    print("\nOutput files:")
    print("  - live_conferences.csv")
    print("  - live_research.csv")
    print("  - live_emails.csv")

    print(f"\n✅ Live run completed! {sent_count} emails sent.\n")

if __name__ == "__main__":
    main()
