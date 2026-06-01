from app.db import upsert_scraped_company, count_companies
sample = [
    {"yc_slug": "acme-ai", "name": "Acme AI", "description": "AI tooling for SMBs", "tags": ["ai","saas"], "batch": "S21", "website": "https://acme.ai", "location": "SF", "company_url": "https://www.ycombinator.com/companies/acme-ai"},
    {"yc_slug": "greenfarm", "name": "GreenFarm", "description": "Sustainable vertical farms", "tags": ["agtech"], "batch": "W20", "website": "https://greenfarm.example", "location": "NY", "company_url": "https://www.ycombinator.com/companies/greenfarm"},
    {"yc_slug": "finflow", "name": "FinFlow", "description": "Payments infrastructure", "tags": ["fintech"], "batch": "S22", "website": "https://finflow.example", "location": "Remote", "company_url": "https://www.ycombinator.com/companies/finflow"},
    {"yc_slug": "biohealth", "name": "BioHealth", "description": "Biotech analytics", "tags": ["biotech"], "batch": "S19", "website": "https://biohealth.example", "location": "Boston", "company_url": "https://www.ycombinator.com/companies/biohealth"},
    {"yc_slug": "eduplus", "name": "EduPlus", "description": "Adaptive learning platform", "tags": ["edtech"], "batch": "S20", "website": "https://eduplus.example", "location": "London", "company_url": "https://www.ycombinator.com/companies/eduplus"},
    {"yc_slug": "climatix", "name": "Climatix", "description": "Climate risk modeling", "tags": ["climate","analytics"], "batch": "W22", "website": "https://climatix.example", "location": "Berlin", "company_url": "https://www.ycombinator.com/companies/climatix"},
]
for c in sample:
    upsert_scraped_company(c)
print('inserted sample rows, total companies now:', count_companies())
