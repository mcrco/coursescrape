# Instructions

## Setup

- install dependencies (I use ```uv``` for package management, so ```uv sync``` if you do too)
- run ```encrypt.py``` to store your access.caltech.edu creds inside a ```.env``` file (only necessary for scraping TQFR)

## Scrape Course Catalog

- ```catalog.py``` saves all scraped courses to ```json/catalog.json``` and courses by department to ```json/{dept}.json```
- uses the 2024-25 catalog @ [https://www.catalog.caltech.edu/current/2024-25/]

## TQFR

- ```tqfr.py``` saves all scraped courses to ```json/tqfr.json```
- collects TQFRs for all available courses in the past 2 years
  - this is set manually in the ```RELEVANT_TERMS``` variable in ```tqfr.py```
