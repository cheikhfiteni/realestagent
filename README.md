# ApartmentFinder

An automated apartment finder that scrapes listings and uses a vLLM to evaluate them based on customizable criteria.

## Features

- Scrapes apartment listings from Craigslist
- Uses Claude 3.5 and Sonnet Models to evaluate listing photos and descriptions
- Scores listings based on customizable criteria like:
  - Price
  - Square footage 
  - Number of bedrooms/bathrooms
  - Visual aesthetics and layout
  - Location and neighborhood
- Stores results in SQLite database
- Deduplicates listings to avoid re-evaluating

## Usage
Install the requirements
```
uv pip install -r requirements.txt
cd frontend
pnpm install
```
Change the `config.py` file to desired craiglist query url, and specify model settings. For those who wish to manage API keys in `.env`, write in following format:

```
ANTHROPIC_API_KEY=<anthropic-key>
OPENAI_API_KEY=<openai-key>
DATABASE_URL=<database-url>
SECRET_KEY=<secret-key>
```
And specifically for (optional) email server functionality:

```
SMTP_HOST=
SMTP_USER=
SMTP_PORT=
SMTP_PASSWORD=
SMTP_FROM=
```

Note that DB secrets point differently in dev and prod. (This is also probably going to happen with running the
scraper as an independent service). 

Run backend through `docker compose up --build`
Run the frontend from the sub-repository using `pnpm dev`

If you want to observe the background task logs run `celery -A app.celery_app worker --loglevel=info`

## Migrations

Use the makefile to generate and apply. Use migrate-init if first time managing migration in dev environment

TODO: Put intial alembic stamp in a fly.io intialization script. Something like:

```
# Check if alembic_version table exists
if ! psql $DATABASE_URL -c "SELECT 1 FROM alembic_version LIMIT 1" >/dev/null 2>&1; then
    # First time setup - stamp and upgrade
    alembic -c app/alembic.ini stamp head
fi

# Always run upgrade after
alembic -c app/alembic.ini upgrade head
```


## Roadmap

In no particular order:
- [ ] Neighborhood evaluation via Google Maps streetview + walkability scores + distance to park + crime statistics, etc
- [ ] Fan out chain-of-thought evaluation for important criteria: 
    - break down responses to complex questions like is this sound proof
    - considering floor plans, proximity to the street, insulation etc
    - a great place for it to shine is surfacing details you might have missed ahead of going, especially disqualifiers against a tour
- [ ] Deploy + regularly update db via cron job
- [ ] Explore better vLLM benchmarks + quantify performance/cost losses when using structured outputs
- [ ] **IMPORTANT**, batch API support to reduce costs
- [ ] Use context manager to streamline SQLAlchemy sessions
- [ ] Email notification system for top listings
