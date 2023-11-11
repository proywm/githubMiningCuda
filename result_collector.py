import os
import subprocess
import glob
import shutil
import argparse
from datetime import datetime
import pandas as pd

def create_directories(destination_dir, raw_dir):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)

def copy_csv_files(worker_nodes, source_dir, raw_dir):
    for node_ip in worker_nodes:
        try:
            subprocess.run(["scp", f"{node_ip}:{source_dir}/github_repo_analysis_result_*.csv", raw_dir], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error while copying files from {node_ip}: {e}")
            continue

def merge_csv_files(raw_dir, merged_csv, max_file_size):
    file_size = 0
    counter = 1
    header_copied = False
    merged_csv_base = os.path.splitext(merged_csv)[0]

    for csv_file in glob.glob(f"{raw_dir}/*.csv"):
        df = pd.read_csv(csv_file)
        df = df.drop_duplicates()
        deduplicated_csv = os.path.join(raw_dir, f"deduplicated_{os.path.basename(csv_file)}")
        df.to_csv(deduplicated_csv, index=False)

        with open(deduplicated_csv, 'rb') as source_file:
            with open(merged_csv, 'ab') as merged_file:
                if not header_copied:
                    shutil.copyfileobj(source_file, merged_file)
                    header_copied = True
                else:
                    next(source_file)
                    shutil.copyfileobj(source_file, merged_file)

        file_size += os.path.getsize(deduplicated_csv)

        if file_size >= max_file_size:
            counter += 1
            merged_csv = f"{merged_csv_base}_{counter}.csv"
            file_size = 0

def git_operations(repo_dir, merged_csv_base, PAT):
    os.chdir(repo_dir)
    try:
        subprocess.run(["git", "pull"], check=True)
        subprocess.run(["git", "add", merged_csv_base + "_*.csv"], check=True)
        subprocess.run(["git", "commit", "-m", "Add result from master node"], check=True)
        repository_url = f"https://{PAT}@github.com/proywm/githubMiningCuda.git"
        subprocess.run(["git", "push", repository_url], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error in Git operations: {e}")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Copy and merge CSV files from worker nodes.")
    parser.add_argument("PAT", help="Your GitHub Personal Access Token")
    args = parser.parse_args()

    # PAT from the command-line argument
    PAT = args.PAT

    # File containing worker node IP addresses
    sshhosts_file = "sshhosts"

    # Directory to copy CSV files from each node
    source_dir = "githubMiningCuda/analyzer/results"

    # Directory to store the merged CSV file
    destination_dir = "analysis_results"
    raw_dir = os.path.join(destination_dir, "raw")

    # Generate a timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # Merged CSV file name with timestamp and counter suffix
    merged_csv = os.path.join(destination_dir, f"commit_analysis_result_{timestamp}.csv")
    max_file_size = 49 * 1024 * 1024  # 49 MB

    # Create the destination directory and "raw" directory if they don't exist
    create_directories(destination_dir, raw_dir)

    # Check if the sshhosts file exists
    if not os.path.isfile(sshhosts_file):
        print("The sshhosts file does not exist. Please create the file with one IP address per line.")
        exit(1)

    # Read worker node IP addresses from the file into a list
    with open(sshhosts_file, 'r') as file:
        worker_nodes = file.read().splitlines()

    # Copy CSV files from worker nodes
    copy_csv_files(worker_nodes, source_dir, raw_dir)

    # Merge CSV files and deduplicate rows
    merge_csv_files(raw_dir, merged_csv, max_file_size)

    # Perform Git operations
    merged_csv_base = os.path.splitext(merged_csv)[0]
    git_operations("githubMiningCuda", merged_csv_base, PAT)

if __name__ == "__main__":
    main()
