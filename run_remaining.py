"""Run the remaining pipeline steps after you manually update missing emails.

Usage:
  - Edit `missing_emails.csv` with corrected emails (columns: name,url,email).
  - From project root run: python run_remaining.py [--send]

By default the script will perform a dry-run for sending emails. Pass
`--send` to actually attempt sending (will use creds from your environment).
"""
import argparse
import sys
from src.utils.csv_handler import read_from_csv, save_to_csv

import main as app


def merge_fixed_emails(conferences, fixes):
    """Merge fixed emails from `fixes` into `conferences`.

    Matching preference: url -> name. Works with lists of dicts from CSV.
    """
    # Build lookup by url and by name (lowercased)
    url_map = {f.get('url', '').strip(): f.get('email', '').strip() for f in fixes if f.get('email')}
    name_map = {f.get('name', '').strip().lower(): f.get('email', '').strip() for f in fixes if f.get('email')}

    updated = []
    for c in conferences:
        orig_email = c.get('email', '').strip()
        updated_email = orig_email

        url = c.get('url', '').strip()
        name = c.get('name', '').strip()

        if url and url in url_map and url_map[url]:
            updated_email = url_map[url]
        elif name and name.lower() in name_map and name_map[name.lower()]:
            updated_email = name_map[name.lower()]

        updated.append({'name': name, 'url': url, 'email': updated_email or 'Not found'})

    return updated


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--send', action='store_true', help='Actually send emails (not a dry-run)')
    parser.add_argument('--conferences', default=None, help='Path to conferences CSV (overrides config)')
    parser.add_argument('--missing', default=None, help='Path to missing emails CSV (overrides default)')
    args = parser.parse_args(argv)

    # Load config and user profile
    config, user_profile = app.load_config()

    conf_path = args.conferences or config['output'].get('conferences_csv', 'conferences.csv')
    missing_path = args.missing or config['output'].get('missing_emails_csv', 'missing_emails.csv')

    try:
        conferences = read_from_csv(conf_path)
    except FileNotFoundError:
        print(f"Conferences CSV not found at {conf_path}. Run phase 1 first or set the correct path.")
        sys.exit(1)

    try:
        fixes = read_from_csv(missing_path)
    except FileNotFoundError:
        print(f"Missing emails CSV not found at {missing_path}. Nothing to merge. Exiting.")
        sys.exit(1)

    updated_confs = merge_fixed_emails(conferences, fixes)

    # Overwrite conferences CSV with updated emails
    save_to_csv(updated_confs, conf_path, fieldnames=['name', 'url', 'email'])
    print(f"Merged fixed emails into {conf_path} ({len(updated_confs)} rows)")

    # Run the remaining phases
    venue_research = app.phase2_research_venues(config, updated_confs)
    emails = app.phase3_generate_emails(config, user_profile, venue_research)

    # Phase 4: send emails (default: dry-run)
    app.phase4_send_emails(config, user_profile, emails, dry_run=(not args.send))


if __name__ == '__main__':
    main()
