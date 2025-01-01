def upsert_env_var(key, value):
    # Open the .env file in read mode to fetch all lines
    with open('.env', 'r') as file:
        lines = file.readlines()
    
    # Check if the key already exists in the file
    key_exists = False
    for i, line in enumerate(lines):
        if line.startswith(key + "="):
            lines[i] = f"{key}={value}\n"  # Update the existing key's value
            key_exists = True
            break
    
    # If the key doesn't exist, append it to the file
    if not key_exists:
        lines.append(f"{key}={value}\n")
    
    # Write the updated content back to the .env file
    with open('.env', 'w') as file:
        file.writelines(lines)
        
def del_env_var(key):
    # Open the .env file in read mode to fetch all lines
    with open('.env', 'r') as file:
        lines = file.readlines()
    
    # Filter out the line that starts with the key
    lines = [line for line in lines if not line.startswith(key + "=")]
    
    # Write the updated content back to the .env file
    with open('.env', 'w') as file:
        file.writelines(lines)
