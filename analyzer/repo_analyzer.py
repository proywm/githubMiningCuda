import socket
from pydriller import Repository
import csv
import os
import re

root_dir = "githubMiningCuda/analyzer"
file_type = '.cu'
published_commits = 0
commit_counter = 0
# Set the number of commits after which the result file will be pushed to GitHub
buffer_size = 100

# Create a 'results' directory if it doesn't exist
results_dir = f'{root_dir}/results'
if not os.path.exists(results_dir):
    os.mkdir(results_dir)

def read_repository_urls_from_csv(input_csv_file):
    print("Processing input filename: ", input_csv_file)
    with open(input_csv_file, 'r') as input_file:
        reader = csv.reader(input_file)
        # Skip the header row
        next(reader, None)
        repo_urls = [row[6] for row in reader]
    return repo_urls

# Function to load patterns from a CSV file
def load_patterns_from_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return [re.compile(row[0]) for row in reader if row]
    
def search_patterns_in_commit_message(message, patterns):
    for pattern in patterns:
        #print(f"Loaded pattern object: {message}")
        if pattern.search(message):
            return True
    return False

def analyze_repository(repo_url, patterns, output_csv_file):
    global commit_counter
    global published_commits
    processed_commits = set()
    commit_data = []
    #print(patterns)
    for commit in Repository(repo_url, only_modifications_with_file_types=['.cu', '.cuh', '.c', '.h', '.cpp', '.hpp']).traverse_commits():
        if commit.hash in processed_commits:
            continue  # Skip already processed commits
        modified_files_count = len(commit.modified_files)
        if modified_files_count < 10 and search_patterns_in_commit_message(commit.msg, patterns):
            print(f"Pattern found in commit {commit.hash}: {commit.msg}")
            # store the commit message and source files
            for modification in commit.modified_files:
                if modification.filename.endswith(('.cu', '.cuh', '.c', '.h', '.cpp', '.hpp')):  # example for Python files
                    original_codes = []
                    modified_codes = []
                    modified_files = set()  # Use a set to keep distinct file names
                                        
                    try:
                        original_codes.append(modification.source_code_before)
                        modified_codes.append(modification.source_code)
                        modified_files.add(modification.filename)
                    except ValueError as e:
                        print(f"Error processing commit {commit.hash}: {e}")
                        continue  # Continue with the next commit if an error occurs

            # Construct the commit URL
            commit_url = f"{repo_url}/commit/{commit.hash}"
            commit_data.append([commit.project_name, commit_url, commit.insertions, commit.deletions, commit.lines, 
                                 commit.files])
            # commit_data.append([commit.project_name, commit_url, commit.insertions, commit.deletions, commit.lines, 
            #                     commit.files, original_codes, modified_codes, list(modified_files)])
            # commit_data.append([commit.project_name, commit_url, commit.hash, commit.msg, commit.committer_date, commit.author.name, commit.insertions, 
            #                     commit.deletions, commit.lines, commit.files, modified_files, original_codes, modified_codes, methods_before, methods_after])
            processed_commits.add(commit.hash)
            commit_counter += 1
            # Push interim commit analysis result to GitHub
            if commit_counter % buffer_size == 0:
                published_commits += buffer_size
                write_commit_analysis_to_csv(output_csv_file, commit_data)
                print(f"{commit_counter} commits are added")
    # Ensure all commits are written to result file
    print(f"Total {commit_counter} commits found from the repository: {repo_url}")
    if(commit_counter>published_commits):
        write_commit_analysis_to_csv(output_csv_file, commit_data)
    return commit_data

def roll_output_csv_file(output_csv_file, counter):
    # Incrementally name the new file
    filename_parts = os.path.splitext(output_csv_file)
    new_output_csv_file = f"{filename_parts[0]}_{counter}.csv"
    os.rename(output_csv_file, new_output_csv_file)

def write_commit_analysis_to_csv(output_csv_file, commit_data):
    with open(output_csv_file, 'a', newline='') as output_file:
        writer = csv.writer(output_file)
        if output_file.tell() == 0:
            # If the file is empty, write the header row
            #writer.writerow(["Project Name", "Commit URL", "Additions", "Deletions", "LoC Changed", "LoC changed in Python Files", "LoC Related to Concurrency", "LOC Ratio", "Total Files Changed", "Python Files Changed", "Python Files that Matched Keywords"])
            # writer.writerow(["Project Name", "Commit URL", "Commit Hash", "Message", "Commit Date", "Author Name", "Additions", "Deletions", "Lines changed", "Files Changed", "Modified files", "Original Code", "Modified Code", "Methods Before", "Methods After"])
            writer.writerow(["Project Name", "Commit URL", "Commit Hash", "Message", "Commit Date", "Author Name", "Additions", "Deletions", "Lines changed", "Files Changed"])
        # Write the commit data
        writer.writerows(commit_data)

def main():
    # Generate the output file name with the specified prefix and IP address
    host_ip = socket.gethostbyname(socket.gethostname())
    date = datetime.date.today().strftime("%m%d%Y")
    # Define the input CSV file name
    input_csv_file = os.path.join(root_dir, f"github_repositories_{host_ip}_{date}.csv")
    
    repo_urls = read_repository_urls_from_csv(input_csv_file)
    print(repo_urls)
    # Specify the output file path inside the 'results' directory
    output_csv_file = os.path.join(results_dir, f"github_repo_analysis_result_{host_ip}.csv")
    patterns = load_patterns_from_csv(os.path.join(root_dir, f"patterns.csv"))
                                      
    for repo_url in repo_urls:
        # Analyze each repository and collect commit data
        print("Processing repo url: ", repo_url)
        analyze_repository(repo_url, patterns, output_csv_file)

if __name__ == "__main__":
    main()