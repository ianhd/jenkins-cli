from InquirerPy import inquirer
from InquirerPy import prompt
from rich import print  # Use rich for colored console output
from models.search_result import SearchResult
import requests
import time
import sys
import re

def search_jenkins(jenkins_instances, search_term):
    search_term = search_term.lower()  # Make search case-insensitive
    results = []

    def search_items(items):
        """ Recursively search items (views or jobs) and collect matches as SearchResult instances. """
        for item in items:
            name = item["name"]
            item_type = item["_class"]
            url = item["url"]
            username = item.get("username","")
            api_token = item.get("api_token","")
            if search_term in name.lower():
                results.append(SearchResult(item_type, name, url, username, api_token))
                if "views" in item:
                    for view in item["views"]:
                        results.append(SearchResult(view["_class"], view["name"], view["url"], username, api_token))
                if "jobs" in item:
                    for job in item["jobs"]:
                        results.append(SearchResult(job["_class"], job["name"], job["url"], username, api_token))
            else:
                if "views" in item:
                    search_items(item["views"])
                if "jobs" in item:
                    search_items(item["jobs"])

    for jenkins in jenkins_instances:
        views = get_jenkins_views(jenkins)
        search_items(views)
        jobs = get_jenkins_jobs(jenkins)
        search_items(jobs)

    workflow_jobs = [result for result in results if result.result_type == "WorkflowJob"]

    if results:
        print(f"[bold cyan]*** Search Results for {search_term}***[/bold cyan]")
        choices = [str(workflow_jb) for workflow_jb in workflow_jobs]
        choices.append("Cancel")

    try:
        selected = inquirer.select(
            message="Select a result or cancel:",
            choices=choices,
            cycle=True,  # Enables cycling through the options
        ).execute()

        if "Cancel" in selected:
            raise KeyboardInterrupt

        selected_result = workflow_jobs[choices.index(selected)]

        confirm_questions = [
            {
                "type": "confirm",
                "message": "Do you want to build this job? " + selected_result.url,
                "default": True,  # default answer is Yes
                "name": "confirm",
            }
        ]

        answers = prompt(confirm_questions)
        answer = answers['confirm']
        if answer:
            trigger_build(selected_result.url, selected_result.username, selected_result.api_token)
        else:
            print("Operation was canceled.")
            return
        # print(f"Your answer: {answers['confirm']}")        
    except KeyboardInterrupt:
        print("[bold red]Search operation was canceled.[/bold red]")
        return

# Function to trigger a build with parameters
def trigger_build(job_url, username, api_token):
    auth = (username, api_token)
    job_url = f"{job_url}buildWithParameters"
    
    # Make the POST request to trigger the build
    response = requests.post(job_url, auth=auth)
    
    # Check for a successful response (status code 201 indicates success)
    if response.status_code == 201:
        print()
        print("✔  build triggered successfully.")
        
        # Print out the Location header from the response
        location = response.headers.get('Location')
        if location:
            # Extract the integer at the end of the string
            queue_item = int(re.findall(r"/(\d+)/$", location)[0])
            monitor_queue(location, queue_item, auth)
        else:
            print("Location header not found in the response.")
    else:
        print()
        print(f"Failed to trigger build. Status code: {response.status_code}")

def render_progress_bar(percentage, width=50):
    completed = int(width * percentage / 100)
    remaining = width - completed
    bar = f"[{'#' * completed}{'.' * remaining}] {percentage:.2f}%"
    return bar

def monitor_build(location, auth):
    print(f"⏳ monitoring build status from {location}")
    
    api_url = f"{location}api/json"

    more_info_url = re.sub(r'/\d+/$', '/', location)

    print()
    
    while True:
        response = requests.get(api_url, auth=auth)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("building"):
            # Check the final result of the build
            result = data.get("result")
            if result == "FAILURE":
                print(f"\n\n😡 build failed. More details here: {more_info_url}\n")
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

def monitor_queue(location, queue_item, auth, timeout_seconds = 30, interval_seconds = 5):
    print(f"⏳ waiting on build # from {location}")

    api_url = f"{location}api/json"

    start_time = time.time()
    
    while True:
        try:
            response = requests.get(api_url, auth=auth)
            response.raise_for_status()
            
            data = response.json()

            # Check if the desired data exists in the response
            if "executable" in data and "number" in data["executable"]:
                build_url = data["executable"].get("url", "URL not available")
                monitor_build(build_url, auth)
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

def get_jenkins_views(jenkins):
    url = f"{jenkins.base_url}/api/json?tree=views[name,_class,url,views[name,_class,url,views[*]]]"
    response = requests.get(url, auth=(jenkins.username, jenkins.api_token))
    response.raise_for_status()
    data = response.json().get("views", [])

    for item in data:
        item["username"] = jenkins.username
        item["api_token"] = jenkins.api_token

    return data

def get_jenkins_jobs(jenkins):
    url = f"{jenkins.base_url}/api/json?tree=jobs[name,_class,url,jobs[name,_class,url,jobs[*]]]"
    response = requests.get(url, auth=(jenkins.username, jenkins.api_token))
    response.raise_for_status()
    data = response.json().get("jobs", [])

    for item in data:
        item["username"] = jenkins.username
        item["api_token"] = jenkins.api_token

    return data
