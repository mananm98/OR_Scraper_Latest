# OpenReview Conference Email Outreach Tool

Automated pipeline to scrape academic conferences from OpenReview.net, research venues with AI, and generate personalized reviewer opportunity emails.

## What It Does

1. **Scrapes** conferences from OpenReview.net "Open for Submissions"
2. **Researches** each venue using Exa.ai for context and topics
3. **Generates** personalized emails with OpenAI (matches your expertise to conference topics)
4. **Outputs** ready-to-send emails to CSV

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up API Keys

Create `.env` file:
```bash
cp .env.example .env
```

Add your API keys:
```
OPENAI_API_KEY=sk-...
EXA_API_KEY=...
EMAIL_ADDRESS=your@email.com
EMAIL_PASSWORD=your_app_password
```

### 3. Configure Your Profile

Edit `config/user_profile.yaml`:
- **Basic Info**: name, email, affiliation
- **Expertise**: List your research domains and focus areas
- **Publications**: Key research contributions (impact, not just titles)
- **Identity**: Brief career stage description

Example:
```yaml
expertise:
  - domain: "Generative AI & LLMs"
    focus: "RLHF, Alignment, and Agentic Systems"
  - domain: "Computer Vision"
    focus: "Medical imaging and Robustness"
```

## Usage

Run the full pipeline:
```bash
python main.py
```

**Output files:**
- `conferences.csv` - Scraped conferences with emails
- `venue_research.csv` - Conference topics and highlights
- `emails.csv` - Generated personalized emails

**Test individual phases:**
```bash
python test_scraper.py          # Test Phase 1 (scraping)
python test_researcher.py       # Test Phase 2 (Exa.ai research)
python test_email_generator.py  # Test Phase 3 (email generation)
python test_sender_dry_run.py   # Test Phase 4 (dry-run mode)
python test_phase4_integration.py # Test Phase 4 (integration with CSV)
```

## How It Works

### Phase 1: Scrape Conferences
- Fetches from OpenReview.net "Open for Submissions"
- Extracts conference name, URL, and contact email
- Saves to `conferences.csv`

### Phase 2: Research Venues
- Uses Exa.ai to find relevant information about each conference
- Extracts key topics and highlights
- Saves to `venue_research.csv`

### Phase 3: Generate Emails
- Matches your expertise to conference topics
- Generates concise (75-150 word) reviewer opportunity emails
- Only generates emails if there is a genuine expertise match
- Saves to `emails.csv`

### Phase 4: Send Emails (Optional)
- SMTP integration for sending emails via Gmail
- Requires Gmail app password or other SMTP credentials
- Manual confirmation with three options:
  - `yes` - Send emails for real
  - `dry-run` - Simulate sending without transmitting (safe testing)
  - `no` - Skip sending
- Features:
  - Rate limiting (1.5s delay between emails)
  - Detailed logging (success/failure with error details)
  - Input validation (email format, required fields)
  - Automatic skipping of "no match" emails

## Configuration

**Email Settings** (`config/config.yaml`):
```yaml
email_generation:
  model: gpt-4o
  temperature: 0.7
  max_tokens: 450
```

**Gmail App Password Setup**:
1. Enable 2-factor authentication
2. Generate app password: https://myaccount.google.com/apppasswords
3. Add to `.env` file

## Project Structure

```
src/
├── scraper/openreview_scraper.py    # OpenReview scraping
├── research/venue_researcher.py     # Exa.ai research
├── email/generator.py               # OpenAI email generation
├── email/sender.py                  # SMTP sending
└── utils/csv_handler.py             # CSV utilities

config/
├── user_profile.yaml                # Your expertise and publications
└── config.yaml                      # App settings

main.py                              # Main orchestrator
```

## Cost Estimate

- **OpenAI**: ~$0.003 per email (~$0.30 for 100 conferences)
- **Exa.ai**: ~$0.05-0.10 per conference (~$5-10 for 100 conferences)

## Safety

- ✓ Review generated emails before sending
- ✓ Tool prompts for confirmation before any emails are sent
- ✓ Start with a small test batch
- ✓ Emails only generated if expertise genuinely matches conference topics
# OR_Scraper_Latest
