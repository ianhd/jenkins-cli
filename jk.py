# run 'pipreqs . --force' to update requirements.txt (then remove version #'s?)

import os
import sys
from helpers.env_validator import validate_and_load_env
from helpers.env_jenkins_loader import load_jenkins_instances
from helpers.jenkins_helper import search_jenkins

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')    
validate_and_load_env(env_path)
jenkins_instances = load_jenkins_instances(env_path)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Main entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: 'jk <search_term>'\n")
    elif len(sys.argv) == 2:
        q = sys.argv[1]
        clear_screen()
        search_jenkins(jenkins_instances, q)
        print()
    # elif sys.argv[1] in ["bl", "build", "bld", "bu"] and len(sys.argv) == 3:
    #     trigger_build(sys.argv[2])
    else:
        print("Invalid command.")
