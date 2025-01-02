# run 'pipreqs . --force' to update requirements.txt (then remove version #'s?)
# ask the user in readme.md to run 'pip install -r requirements.txt' command to get all pip libraries

import requests
import os
import sys
import re
import time
from tabulate import tabulate
from colorama import Fore, Style, init as colorama_init
from helpers.env_validator import validate_and_load_env
from utils.env_functions import upsert_env_var
from utils.env_functions import del_env_var

validate_and_load_env()

colorama_init()

# retrieve env vars
jenkins_instance = os.getenv('JENKINS_INSTANCE')
avail_jenkins_instances = os.getenv('AVAILABLE_JENKINS_INSTANCES')
jenkins_base_url = os.getenv(f'{jenkins_instance}_BASE_URL').rstrip('/')
username = os.getenv(f'{jenkins_instance}_USERNAME')
api_token = os.getenv(f'{jenkins_instance}_API_TOKEN')
jobs_or_views = os.getenv(f'{jenkins_instance}_JOBS_OR_VIEWS')
job_or_view = jobs_or_views.rstrip('s')
parent = os.getenv('PARENT')
    
# Jenkins Configuration
JENKINS_URL = f"{jenkins_base_url}/{job_or_view}/{parent}" # point to a parent
AUTH = (username, api_token)

def set_parent(new_parent):
    upsert_env_var("PARENT", new_parent)
    print(f"\n✔  parent is now set to '{new_parent}'.\n")        
    
def set_jenkins(new_jenkins):
    upsert_env_var("JENKINS_INSTANCE", new_jenkins)
    del_env_var("PARENT")
    print(f"\n✔  jenkins instance is now set to {Fore.GREEN}{new_jenkins}{Style.RESET_ALL}; parent is cleared.\n")        

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_jenkins():
    print(f"\nAvailable Jenkins instances: {avail_jenkins_instances}\n")

# Function to list Jenkins jobs
def list_jobs(parents_only):
    list_children = not parents_only
    
    clear_screen()
    
    print(f"Using {Fore.GREEN}{jenkins_base_url} ({jenkins_instance}){Style.RESET_ALL}...\n")
    
    # if the user typed `jk list` but no parent is set, mention it, and instead list out parents
    # so they can select a parent
    if list_children and not parent:
        print(f"No parent has been set; listing all parents so you can set one using {Fore.CYAN}jk set parent <name>{Style.RESET_ALL} command.") 
        parents_only = True       
    elif list_children and parent:
        print(f"Jobs in {Fore.GREEN}{parent}{Style.RESET_ALL}:")   
    else:
        print(f"All parent {jobs_or_views}:")

    
    api_endpoint = f"{jenkins_base_url if parents_only else JENKINS_URL}/api/json?tree=views[name,url],jobs[name,url]"
        
    # print()
    
    # if parents_only:
    #     print(f"All parent {jobs_or_views}:")
    # else:
    #     print(f"Jobs in {Fore.GREEN}{parent}{Style.RESET_ALL}:")

    try:
        response = requests.get(api_endpoint, auth=AUTH)
        response.raise_for_status()
        jobs = response.json().get("jobs", [])
        views = response.json().get("views", [])
        items = []
        if parents_only and jobs_or_views == "views":
            items = views
        else:
            items = jobs
        # items = jobs if jobs_or_views == "jobs" else views
        print()
        table_data = [(item["name"], item["url"]) for item in items]
        print(tabulate(table_data, headers=[f"{"Parent" if parents_only else "Job"}", "URL"], tablefmt="grid"))        
        print()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching jobs: {e}")
        
    print(f"Related commands:")
    print()
    if parents_only:
        print(f"{Fore.CYAN}jk set parent <name>{Style.RESET_ALL} to set parent")
    else:
        print(f"{Fore.CYAN}jk ls parents{Style.RESET_ALL} to list all parents")
        print(f"{Fore.CYAN}jk build <job_name>{Style.RESET_ALL} trigger a build")
    print(f"{Fore.CYAN}jk set jenkins <name>{Style.RESET_ALL} to set jenkins instance")
    print(f"{Fore.CYAN}jk ls jenkins{Style.RESET_ALL} to list available jenkins instances")
    print()

# Function to trigger a build with parameters
def trigger_build(job_name):
    job_url = f"{JENKINS_URL}/job/{job_name}/buildWithParameters"
    
    # Make the POST request to trigger the build
    response = requests.post(job_url, auth=AUTH)
    
    # Check for a successful response (status code 201 indicates success)
    if response.status_code == 201:
        print()
        print("✔  build triggered successfully.")
        
        # Print out the Location header from the response
        location = response.headers.get('Location')
        if location:
            # Extract the integer at the end of the string
            queue_item = int(re.findall(r"/(\d+)/$", location)[0])
            monitor_queue(location, queue_item)
        else:
            print("Location header not found in the response.")
    else:
        print()
        print(f"Failed to trigger build. Status code: {response.status_code}")

def get_failure_reason(data):
    for action in data.get("actions", []):
        if "causes" in action:
            causes = action["causes"]
            return ", ".join(cause.get("shortDescription", "Unknown cause") for cause in causes)
    return "Unknown reason"

def render_progress_bar(percentage, width=50):
    completed = int(width * percentage / 100)
    remaining = width - completed
    bar = f"[{'#' * completed}{'.' * remaining}] {percentage:.2f}%"
    return bar

# git push test

def monitor_build(location, build_number):
    print(f"⏳ monitoring build status from {location}")
    
    api_url = f"{location}api/json"
    
    print()
    
    while True:
        response = requests.get(api_url, auth=AUTH)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("building"):
            # Check the final result of the build
            result = data.get("result")
            if result == "FAILURE":
                failure_reason = get_failure_reason(data)
                print(f"\n\n🤦‍♂️ build failed. Reason: {failure_reason}.\n")
                exit()
            elif result == "SUCCESS":
                print("\n\n🙌 build succeeded!\n")
                exit()
            else:
                print(f"\nBuild ended with result: {result}\n")
                exit()
            break
        
        # Calculate progress percentage
        timestamp = data["timestamp"]
        estimated_duration = data["estimatedDuration"]
        current_time = int(time.time() * 1000)
        
        elapsed_time = current_time - timestamp
        progress_percentage = min((elapsed_time / estimated_duration) * 100, 100)
        
        # Render progress bar
        bar = render_progress_bar(progress_percentage)
        sys.stdout.write(f"\r{bar}")
        sys.stdout.flush()
        
        # Sleep for 3 seconds to reduce API calls
        time.sleep(3)    

def monitor_queue(location, queue_item, timeout_seconds = 30, interval_seconds = 5):
    print(f"⏳ waiting on build # from {location}")

    api_url = f"{jenkins_base_url}/queue/item/{queue_item}/api/json"

    start_time = time.time()
    
    while True:
        try:
            response = requests.get(api_url, auth=AUTH)
            response.raise_for_status()
            
            data = response.json()

            # Check if the desired data exists in the response
            if "executable" in data and "number" in data["executable"]:
                build_number = data["executable"]["number"]
                build_url = data["executable"].get("url", "URL not available")
                monitor_build(build_url, build_number)
            else:
                why = data["why"]
                #print(f"Build # is not available yet; {why}.")
        except requests.RequestException as e:
            print(f"Error retrieving data: {e}")
            exit()
            
        if time.time() - start_time > timeout_seconds:
            print("Timeout expired; unable to retrieve build #.")
            exit()
        
        time.sleep(interval_seconds)

# Main entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: jk list | build <job_name>")
    elif sys.argv[1] in ["ls","list"] and len(sys.argv) == 3 and sys.argv[2] == "jenkins":
        list_jenkins()
    elif sys.argv[1] in ["ls","list"]:
        list_jobs(len(sys.argv) == 3)
    elif len(sys.argv) >= 4 and sys.argv[1] == "set" and sys.argv[2] == "parent":
        parent_name = sys.argv[3]
        set_parent(parent_name)     
    elif len(sys.argv) >= 4 and sys.argv[1] == "set" and sys.argv[2] == "jenkins":
        jenkins_name = sys.argv[3]
        set_jenkins(jenkins_name)
    elif sys.argv[1] in ["bl", "build", "bld", "bu"] and len(sys.argv) == 3:
        trigger_build(sys.argv[2])
    else:
        print("Invalid command.")
