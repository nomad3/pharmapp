# Pharmacy Chain Price Scraping System

**Date:** 2026-02-23
**Status:** Implemented and verified

## Goal

Scrape real retail prices from Chile's 4 major pharmacy chains (Cruz Verde, Salcobrand, Dr. Simi, Farmacias Ahumada) using their ecommerce search APIs, normalize into the marketplace tables, and expose admin endpoints for triggering/monitoring scrapes.

## Architecture

Each pharmacy chain has a different ecommerce platform with its own search API:

| Chain | Platform | API Type | Rate Limit |
|-------|----------|----------|------------|
| Dr. Simi | VTEX | REST Catalog API (open) | 1.5s |
| Cruz Verde | Salesforce Commerce Cloud | OCAPI (public client_id) | 2.0s |
| Salcobrand | Algolia | Search API (public keys) | 1.5s |
| Ahumada | SFCC SFRA | HTML scraping (Cloudflare) | 3.0s |

**Pipeline:** Query Builder → Scrapers → ETL Normalization → Marketplace Tables → ScrapeRun Tracking

## Files Created

### Scrapers (`backend/app/scrapers/`)
- `__init__.py` — package init
- `base.py` — `ScrapedProduct` dataclass + `BaseScraper` ABC with rate limiting, exponential backoff retry (skips 4xx), batch search
- `drsimi.py` — VTEX Catalog API: `GET /api/catalog_system/pub/products/search?ft={query}`. Extracts product specs (Principio Activo, Receta Medica) from VTEX fields. Handles 400 gracefully (returns empty).
- `cruzverde.py` — SFCC OCAPI: `GET /s/Chile/dw/shop/v19_1/product_search?q={query}&client_id=c19ce24d-...&expand=prices,availability,images`
- `salcobrand.py` — Algolia: `POST /1/indexes/sb_variant_production/query` with public app ID `GM3RP06HJG` and API key. Requires `Referer: https://salcobrand.cl/` header.
- `ahumada.py` — HTML scraping with browser-like headers. Parses product tiles via regex. Degrades gracefully on Cloudflare 403.
- `query_builder.py` — Builds search queries from `Medication.active_ingredient`. Cleans Cenabast-style prefixes (`1-aciclovir` → `aciclovir`), strips dosage info, deduplicates.

### ETL (`backend/app/etl/`)
- `scrape_to_marketplace.py` — Normalizes `ScrapedProduct` list into `Medication`, `Pharmacy`, `Price` tables. Creates one "Online" pharmacy per chain. Deduplicates by `(chain, sku)`. Upserts prices (update existing, insert new).

### Model (`backend/app/models/`)
- `scrape_run.py` — `ScrapeRun` model tracking: chain, status (running/completed/failed), queries_total/completed, products_found, prices_upserted, medications_created, errors (JSON), timestamps.

### Orchestration (`backend/app/tasks/`)
- `scraping.py` — Replaced placeholder. `run_scrape_with_session()` creates its own DB session for background execution. Iterates chains → scraper.search_batch() → ETL upsert → update ScrapeRun.

### API (`backend/app/api/v1/`)
- `scraping.py` — Admin endpoints:
  - `POST /scraping/run?chains=dr_simi&query_limit=30` — trigger background scrape
  - `GET /scraping/runs` — list recent runs with status
  - `GET /scraping/runs/{id}` — run details including errors

## Files Modified

- `backend/app/models/__init__.py` — registered `ScrapeRun`
- `backend/app/api/v1/routes.py` — registered `scraping` router, removed old placeholder `/admin/trigger-scraping` endpoint

## Key Design Decisions

1. **Own DB session for background tasks** — FastAPI closes the request session after response, so background tasks must create their own via `SessionLocal()`.
2. **Skip 4xx retries** — Only retry 5xx and connection errors. VTEX returns 400 for queries it can't parse (brand names, medical supplies).
3. **Query cleaning** — Cenabast ingredient names have numeric prefixes (`1-`, `1.1-`), dosage info, and parentheticals that need stripping for pharmacy search APIs.
4. **One pharmacy per chain** — Creates virtual "Cruz Verde Online", "Dr. Simi Online" etc. rather than per-store records (no store-level data from search APIs).
5. **Dedup by (chain, sku)** — Multiple search queries may return the same product; dedup before ETL prevents duplicate prices.

## Verified Results

Test scrape with 10 queries across all 4 chains:
- **96 products found**, 66 prices upserted, 28 new medications created
- Cruz Verde: 63 prices, Dr. Simi: 27, Ahumada: 5, Salcobrand: 5
- Transparency page now shows real retail chain markup data:
  - Cenabast: +2% (score 100)
  - Cruz Verde: +131% (score 74)
  - Ahumada: +330% (score 34)
  - Dr. Simi: +413% (score 18)
  - Salcobrand: +515% (score 0)

## Usage

```bash
# Trigger scrape (all chains, 200 queries)
curl -X POST http://localhost:8000/api/v1/scraping/run

# Trigger specific chains with limited queries
curl -X POST "http://localhost:8000/api/v1/scraping/run?chains=dr_simi&chains=cruz_verde&query_limit=30"

# Check status
curl http://localhost:8000/api/v1/scraping/runs

# Or use Swagger UI at http://localhost:8000/docs
```
