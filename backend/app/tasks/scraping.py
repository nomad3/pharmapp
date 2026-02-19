"""Triggers ServiceTsunami scraping pipelines for pharmacy price data."""
from app.services.servicetsunami import tsunami_client

PIPELINE_IDS = {
    "cruz_verde": None,
    "salcobrand": None,
    "ahumada": None,
}

async def trigger_all_scrapers():
    """Trigger all pharmacy scraping pipelines."""
    results = {}
    for chain, pipeline_id in PIPELINE_IDS.items():
        if pipeline_id:
            result = await tsunami_client.trigger_scraping_pipeline(pipeline_id)
            results[chain] = result
    return results
