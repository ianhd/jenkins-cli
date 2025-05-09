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

    def search_items(jenkins, items):
        """ Recursively search items (views or jobs) and collect matches as SearchResult instances. """
        for item in items:
            name = item["name"]
            item_type = item["_class"]
            url = item["url"]
            username = jenkins.username
            api_token = jenkins.api_token
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
                    search_items(jenkins, item["views"])
                if "jobs" in item:
                    search_items(jenkins, item["jobs"])

    for jenkins in jenkins_instances:
        views = get_jenkins_views(jenkins)
        search_items(jenkins, views)
        jobs = get_jenkins_jobs(jenkins)
        search_items(jenkins, jobs)

    workflow_jobs = [result for result in results if result.result_type == "WorkflowJob"]

    if results:
        print(f"[bold cyan]*** Search Results for {search_term} ***[/bold cyan]")
        choices = [str(workflow_jb) for workflow_jb in workflow_jobs]
        choices.append("Cancel")
    else:
        print("[bold red]No results found.[/bold red]")
        return        
    
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
            # does this job have a REPO_BRANCH build argument specified?
            repo_branch = get_repo_branch(selected_result.url, selected_result.username, selected_result.api_token)            
            if repo_branch:
                repo_branch = inquirer.text(
                    message="Which branch?",
                    default=repo_branch,
                ).execute()

            # params = get_job_parameters(selected_result.url, selected_result.username, selected_result.api_token)
            # for key, value in params.items():
            #     print(f"[bold cyan]{key}[/bold cyan]: {value}")

            trigger_build(selected_result.url, selected_result.username, selected_result.api_token, repo_branch)
        else:
            print("Operation was canceled.")
            return
    except KeyboardInterrupt:
        print("[bold red]Search operation was canceled.[/bold red]")
        return

# Function to get all job build arguments aka parameters
def get_repo_branch(job_url, username, api_token):
    auth = (username, api_token)
    url = f"{job_url}api/json?tree=property[parameterDefinitions[defaultParameterValue[value]]]"
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    data = response.json()

    for prop in data.get("property", []):
        if prop.get("_class") == "hudson.model.ParametersDefinitionProperty":
            for param in prop.get("parameterDefinitions", []):
                value = param.get("defaultParameterValue", {}).get("value", "")
                if isinstance(value, str):
                    lines = value.strip().splitlines()
                    for line in lines:
                        if line.startswith("REPO_BRANCH="):
                            return line.split("=", 1)[1]
    return None  # Not found

def get_job_parameters(job_url, username, api_token):
    auth = (username, api_token)
    url = f"{job_url}api/json?tree=property[parameterDefinitions[defaultParameterValue[value]]]"
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    data = response.json()

    parameters = {}

    for prop in data.get("property", []):
        param_defs = prop.get("parameterDefinitions")
        if not param_defs:
            continue

        for param in param_defs:
            default_value = param.get("defaultParameterValue", {}).get("value", "")
            if isinstance(default_value, str):
                # Parse the multiline string into key=value pairs
                for line in default_value.splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)
                        parameters[key.strip()] = value.strip()
                return parameters  # assume there's only one such param block
    return parameters

# Function to trigger a build with parameters
def trigger_build(job_url, username, api_token, override_branch=None):
    auth = (username, api_token)

    # Get the parameters
    parameters = get_job_parameters(job_url, username, api_token)

    # Apply override if provided
    if override_branch:
        parameters["REPO_BRANCH"] = override_branch

    # Create args string: KEY=VALUE\nKEY2=VALUE2...
    args_value = "\n".join(f"{k}={v}" for k, v in parameters.items())

    # Trigger build
    job_url = f"{job_url}buildWithParameters"
    response = requests.post(job_url, auth=auth, params={"args": args_value})

    if response.status_code == 201:
        print("\n✔  build triggered successfully.")
        location = response.headers.get('Location')
        if location:
            queue_item = int(re.findall(r"/(\d+)/$", location)[0])
            monitor_queue(location, queue_item, auth)
        else:
            print("Location header not found in the response.")
    else:
        print(f"\nFailed to trigger build. Status code: {response.status_code}")

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
    printed_commits = False

    while True:
        response = requests.get(api_url, auth=auth)
        response.raise_for_status()
        
        data = response.json()

        if data.get("building") and not printed_commits:
            commits = get_build_changes(api_url, auth)
            if commits:
                printed_commits = True
                print("\n📦 Commits for this build:")
                for c in commits:
                    short = (c["id"] or "")[:7]
                    msg   = c["msg"].splitlines()[0]
                    author= c["author"] or "unknown"
                    print(f"  • {short} — {msg} (by {author})")
                print()

        
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

    return data

def get_jenkins_jobs(jenkins):
    url = f"{jenkins.base_url}/api/json?tree=jobs[color,name,_class,url,jobs[name,_class,url,jobs[*]]]"
    response = requests.get(url, auth=(jenkins.username, jenkins.api_token))
    response.raise_for_status()
    jobs = response.json().get("jobs", [])

    filtered_jobs = [job for job in jobs if job.get("color") != "disabled"]
    return filtered_jobs

def get_build_changes(build_url, auth):
    """
    Fetches the list of commits that went into the given Jenkins build.
    Returns:
      List[dict]: each dict has keys "id", "author", "msg".
    """
    if not build_url.endswith('/'):
        build_url += '/'

    # Request both the plural and singular change-set blocks so we cover all job types:
    #   changeSets[items[commitId,msg,author[fullName]]]
    #     – the plural changeSets block that Pipeline/Multibranch jobs populate
    #   changeSet[items[commitId,msg,author[fullName]]]
    #     – the singular changeSet block that freestyle jobs (and some older workflows) use
    api_url = (
        f"{build_url}api/json?"
        "tree=changeSets[items[commitId,msg,author[fullName]]],"
        "changeSet[items[commitId,msg,author[fullName]]]"
    )

    resp = requests.get(api_url, auth=auth)
    resp.raise_for_status()
    data = resp.json()

    commits = []
    for section in ("changeSets", "changeSet"):
        for cs in data.get(section, []):
            for item in cs.get("items", []):
                commits.append({
                    "id":     item.get("commitId"),
                    "author": item.get("author", {}).get("fullName"),
                    "msg":    item.get("msg", "").strip()
                })

    return commits