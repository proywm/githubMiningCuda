import requests
import time
import csv
import argparse
import datetime
import os

def build_github_query(language=None, stars=None, forks=None, last_commit=None):
    """
    Build a GitHub search query based on provided filters.

    :param language: Filter by programming language.
    :param stars: Filter by minimum number of stars.
    :param forks: Filter by minimum number of forks.
    :param last_commit: Filter by last commit date (YYYY-MM-DD).
    :return: GitHub search query.
    """

    query_parts = []
    
    if language:
        query_parts.append(f'language:{language}')
    if stars is not None:
        query_parts.append(f'stars:>{stars}')
    if forks is not None:
        query_parts.append(f'forks:>{forks}')
    if last_commit:
        query_parts.append(f'pushed:>{last_commit}')
    #query_parts.append(f'sort:stars')
    #query_parts.append(f'order:desc')
    return ' '.join(query_parts)

def search_github_repositories(query, result_file, result_limit=None):
    """
    Search GitHub repositories based on the provided query and retrieve repository information.

    :param query: GitHub search query.
    :param result_limit: Result limit.
    :return: List of retrieved repositories.
    """

    base_url = 'https://api.github.com/search/repositories'
    params = {'q': query, 'per_page': 1000, 'page': 1, 'sort':'stars'}  # Adjust as per_page needed for your use case and page starts with 1
    
    repositories = []
    remaining_results = result_limit if result_limit else float('inf')
    idx = 1  # Initialize the serial number

    with open(result_file, 'w', newline='') as csvfile:
        fieldnames = ['Serial No', 'Name', 'Description', 'Stars', 'Forks', 'Last Commit', 'Repository URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        while remaining_results > 0:
            response, new_repositories = fetch_github_repositories(base_url, params, remaining_results)
            if response is None or new_repositories is None:
                break

            repositories.extend(new_repositories)

            remaining_results, idx = process_github_repositories(new_repositories, remaining_results, idx, writer, response, params)
    
    return repositories

def fetch_github_repositories(base_url, params, remaining_results):
    """
    Fetch GitHub repositories from the API based on the provided URL and parameters.

    :param base_url: GitHub API base URL.
    :param params: Request parameters.
    :param remaining_results: Number of remaining results to retrieve.
    :return: Response object and retrieved repositories.
    """

    response = requests.get(base_url, params=params)

    # Check rate limit
    rate_limit = int(response.headers['X-RateLimit-Limit'])
    rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
    reset_time = int(response.headers['X-RateLimit-Reset'])
    check_rate_limit(rate_limit, rate_limit_remaining, reset_time)

    if response.status_code != 200:
        print(f"Failed to retrieve GitHub repositories. Status code: {response.status_code}")
        return None, None

    data = response.json()
    new_repositories = data.get('items', [])

    return response, new_repositories

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

def process_github_repositories(new_repositories, remaining_results, idx, writer, response, params):
    """
    Process the retrieved GitHub repositories and write the information to a CSV file.

    :param new_repositories: List of new repositories.
    :param remaining_results: Number of remaining results.
    :param idx: Serial number.
    :param writer: CSV writer.
    :param response: Response object.
    :param params: Request parameters.
    :return: Updated remaining_results and idx.
    """

    for repo in new_repositories:
        remaining_results -= 1
        print_github_repository(repo, idx, writer)
        idx += 1

    if 'next' in response.links and remaining_results > 0:
        params['page'] += 1
        # print(f"Rate Limit - Remaining: {response.headers['X-RateLimit-Remaining']}, Limit: {response.headers['X-RateLimit-Limit']}")

    return remaining_results, idx

def print_github_repository(repo, idx, writer):
    """
    Print repository information to a CSV file.

    :param repo: Repository data.
    :param idx: Serial number.
    :param writer: CSV writer.
    """

    writer.writerow({
        'Serial No': idx,
        'Name': repo['name'],
        'Description': repo['description'],
        'Stars': repo['stargazers_count'],
        'Forks': repo['forks_count'],
        'Last Commit': repo['pushed_at'],
        'Repository URL': repo['html_url']
    })

#python repo_fetcher.py --language Python --stars 100 --forks 10 --last_commit 2023-01-01 --result_limit 2000
def main():
    # Define command-line arguments for filter parameters
    parser = argparse.ArgumentParser(description='Fetch GitHub repositories based on filters.')
    parser.add_argument('--language', default='Python', help='Filter by programming language')
    parser.add_argument('--stars', type=int, default=20, help='Filter by minimum number of stars')
    parser.add_argument('--forks', type=int, default=0, help='Filter by minimum number of forks')
    parser.add_argument('--last_commit', default='2010-01-01', help='Filter by last commit date (YYYY-MM-DD)')
    parser.add_argument('--result_limit', type=int, default=None, help='Result limit')
    args = parser.parse_args()

    # Build the GitHub search query based on provided filter parameters
    query = build_github_query(args.language, args.stars, args.forks, args.last_commit)

    # Create a 'results' directory if it doesn't exist
    results_dir = f'repository_lists'
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)
    date = datetime.date.today().strftime("%m%d%Y")
    result_file = f'{results_dir}/github_repositories_{args.language}_{date}.csv'

    # Search GitHub repositories and store the results in a CSV file
    search_github_repositories(query, result_file, args.result_limit)

if __name__ == '__main__':
    main()