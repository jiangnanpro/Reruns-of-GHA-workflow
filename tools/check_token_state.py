import requests
import time

# GitHub API endpoint for getting workflow runs
workflow_runs_url = "https://api.github.com/repos/{owner}/{repo}/actions/runs"

# insert Github tokens here.
token1 = ""
token2 = ""

headers1 = {
    "Authorization": f"Bearer {token1}",
    "Accept": "application/vnd.github.v3+json"
}

headers2 = {
    "Authorization": f"Bearer {token2}",
    "Accept": "application/vnd.github.v3+json"
}

# Make a GET request to the GitHub API rate limit endpoint
response1 = requests.get('https://api.github.com/rate_limit', headers=headers1)
response1 = response1.json()['resources']['core']

response2 = requests.get('https://api.github.com/rate_limit', headers=headers2)
response2 = response2.json()['resources']['core']

# Parse and print the response
print(f'token1:{response1}')
print(f'token2:{response2}')