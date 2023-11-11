import requests
import time
import csv
import argparse
import datetime
import os
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse

github_token = "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"

def get_number_of_commits(username, repo):
    # GitHub API URL for commit search
    url = f'https://api.github.com/repos/{username}/{repo}/commits'

    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    # Make the request to the GitHub API
    response = requests.get(url, headers=headers)

    # Check rate limit
    rate_limit = int(response.headers['X-RateLimit-Limit'])
    rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
    reset_time = int(response.headers['X-RateLimit-Reset'])
    check_rate_limit(rate_limit, rate_limit_remaining, reset_time)

    
    # Check if the request was successful
    if response.status_code == 200:
        commit_data = response.json()
        number_of_commits = len(commit_data)
        return number_of_commits
    else:
        print(f"Failed to fetch commits for {username}/{repo}. Status code: {response.status_code}, Response: {response.text}")
        return None

def check_rate_limit(rate_limit, rate_limit_remaining, reset_time):
    """
    Check the GitHub rate limit and wait if necessary.

    :param rate_limit: Total rate limit.
    :param rate_limit_remaining: Remaining rate limit.
    :param reset_time: Rate limit reset time.
    """

    if rate_limit_remaining == 0:
        sleep_time = reset_time - int(time.time()) + 1
        print(f"Rate Limit Exceeded. Waiting for {sleep_time} seconds...")
        time.sleep(sleep_time)
    print(f"Rate Limit - Remaining: {rate_limit_remaining}, Limit: {rate_limit}")

# Temporary list to hold all rows with updated data
updated_rows = []

def main():
    # Define command-line arguments for filter parameters
    parser = argparse.ArgumentParser(description='Fetch GitHub commit counts based on repolist.')
    parser.add_argument('--repolist', help='Provide the repo list generated from repo_fetcher.py')
    args = parser.parse_args()

    with open(args.repolist, newline='') as csvfile:
        repo_reader = csv.DictReader(csvfile)

        # Include the new column for commit numbers
        fieldnames = repo_reader.fieldnames + ['CommitNumber']
        for row in repo_reader:
            repo_url = row['Repository URL']
            print(f"repo_url: {repo_url}")
            # Parse the URL to get the path
            path = urlparse(repo_url).path

            # Split the path to get the username and repository name
            parts = path.strip("/").split('/')
            if len(parts) == 2:
                username, repo_name = parts
                print(f"Username: {username}, Repository Name: {repo_name}")
                number_of_commits = get_number_of_commits(username, repo_name)
                if number_of_commits is not None:
                    print(f"The repository '{username}/{repo_name}' has {number_of_commits} commits.")
                    row['CommitNumber'] = number_of_commits
            updated_rows.append(row)
    # Write the updated data back to the CSV file
    with open(args.repolist, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

if __name__ == '__main__':
    main()
