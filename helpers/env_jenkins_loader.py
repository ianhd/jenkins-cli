import os
from dotenv import load_dotenv
from models.jenkins import Jenkins

def load_jenkins_instances(env_path):
    load_dotenv(env_path)

    output = []
    index = 1
    while True:
        base_url = os.getenv(f"JENKINS_BASE_URL_{index}")
        api_token = os.getenv(f"JENKINS_API_TOKEN_{index}")
        username = os.getenv(f"JENKINS_USERNAME_{index}")
        
        if not base_url or not api_token or not username:
            break  # Stop when we run out of Jenkins configurations

        # Create a Jenkins instance and add it to the list
        output.append(Jenkins(base_url, api_token, username))
        index += 1

    return output

