import csv
import requests
from typing import Dict, List, Annotated, Optional, Union
from pydantic import Field

def fetch_fdh_data() -> List[Dict[str, str]]:
    """Fetch and parse FDH statistics from Immigration Department"""
    url = "https://www.immd.gov.hk/opendata/eng/law-and-security/visas/statistics_FDH.csv"
    response = requests.get(url)
    response.raise_for_status()
    
    reader = csv.DictReader(response.text.splitlines())
    result = [dict(row) for row in reader]

    return result

def get_fdh_statistics(
    year: Annotated[Optional[int], Field(description="Filter by specific year")] = None
) -> Dict[str, Union[Dict[str, str], List[Dict[str, str]], str]]:
    """Get statistics on Foreign Domestic Helpers in Hong Kong.
    Data source: Immigration Department"""
    data = fetch_fdh_data()
    
    if year:
        year_str = str(year)
        result = next((item for item in data if item["As at end of Year"] == year_str), None)
        return {"data": result} if result else {"error": f"No data for year {year}"}
    
    return {"data": data}
