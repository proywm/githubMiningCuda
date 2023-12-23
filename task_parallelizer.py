import subprocess
import shutil
import os
import pandas as pd
import argparse

# Function to check if a command is available in the system
def is_command_available(command):
    return shutil.which(command) is not None

# Function to read SSH hosts from a file
def read_ssh_hosts(filename):
    with open(filename, "r") as hosts_file:
        return [line.strip() for line in hosts_file]

# Function to split data into separate input CSV files for each node
def split_csv_data(input_csv, num_nodes, hostnames, split_files_dir):
    input_df = pd.read_csv(input_csv)
    rows_per_node = len(input_df) // num_nodes
    split_data = []
    for i in range(num_nodes):
        start_row = i * rows_per_node
        end_row = start_row + rows_per_node
        node_df = input_df[start_row:end_row]

        # Append the IP address to the filename
        filename = os.path.join(split_files_dir, f"github_repositories_{hostnames[i]}.csv")
        node_df.to_csv(filename, index=False)
        split_data.append(filename)
    return split_data

# Function to copy files to remote nodes using parallel-scp
def copy_files_to_nodes(ssh_hosts, data_to_copy, destination_path, user):
    for i, host in enumerate(ssh_hosts):
        remote = user + "@" + host + ":" + destination_path
        print(f"Copying {data_to_copy[i]} to {host} {remote} ...")
        subprocess.run(["scp", data_to_copy[i], remote])
        print(f"{data_to_copy[i]} copied to {host}")

# Main function to execute the entire script
def main():

    parser = argparse.ArgumentParser(description="Copy and split files to remote nodes.")
    parser.add_argument("input_csv", help="Path to the input CSV file")
    parser.add_argument("username", help="Remote username for SSH")
    args = parser.parse_args()

    username = args.username
    split_files_dir = "analyzer"  # Set output directory for the split files
    ssh_hosts = read_ssh_hosts("sshhosts")

    input_csv = args.input_csv  # Ensure the header is present
    num_nodes = len(ssh_hosts)
    hostnames = ssh_hosts
    split_data = split_csv_data(input_csv, num_nodes, hostnames, split_files_dir)

    destination_path = f"/users/{username}/githubMiningCuda/{split_files_dir}"  # Set your destination path here

    copy_files_to_nodes(ssh_hosts, split_data, destination_path, username)

    print("File split and copy on remote nodes completed.")

if __name__ == "__main__":
    main()
