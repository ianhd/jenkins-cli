import os
from dotenv import load_dotenv

def validate_and_load_env(env_path):
    # Check if the .env file exists
    if not os.path.exists(env_path):
        print("\nOops. Please create a .env file. Look at .env.example as a template.\n")
        exit()

    load_dotenv(env_path)

    # Make sure required env variables are there
    env_keys_csv = 'JENKINS_BASE_URL_1,JENKINS_API_TOKEN_1,JENKINS_USERNAME_1'
    env_keys = env_keys_csv.split(',')
    missing = [key for key in env_keys if not os.getenv(key)]
    if missing:
        print(f"\nOops. Please make sure these keys are set in .env file: {env_keys_csv}\n")
        exit()
