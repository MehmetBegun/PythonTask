import os
import requests

BASE_URL = "https://interpol.api.bund.dev"
API_KEY = os.getenv("INTERPOL_API_KEY")

HEADERS = {
    "Accept": "application/json",
}

if API_KEY:
    HEADERS["x-api-key"] = API_KEY

def search_individual(name=None, nationality=None, dob=None):
    """Search for individuals by name, nationality or date of birth."""
    params = {}
    if name:
        params["name"] = name
    if nationality:
        params["nationality"] = nationality
    if dob:
        params["dob"] = dob
    response = requests.get(f"{BASE_URL}/search", headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_individual_details(individual_id):
    """Retrieve detailed information about a specific individual."""
    response = requests.get(f"{BASE_URL}/individual/{individual_id}", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_red_notice(individual_id):
    """View the red notice associated with a specific individual."""
    response = requests.get(f"{BASE_URL}/red-notice/{individual_id}", headers=HEADERS)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    # Example usage
    result = search_individual(name="John Doe", nationality="USA")
    print(result)

