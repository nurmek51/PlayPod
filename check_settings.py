import re
import sys

def check_and_fix_settings():
    settings_file = 'PlayPod/settings.py'
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Check specifically for unclosed parentheses in the REDIS_PASSWORD line
    redis_pattern = r'REDIS_PASSWORD\s*=\s*os\.getenv\("REDIS_PASSWORD"(?!\))'
    match = re.search(redis_pattern, content)
    
    if match:
        print(f"Found unclosed parenthesis in {settings_file}")
        # Fix the issue
        fixed_content = re.sub(
            redis_pattern,
            'REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")',
            content
        )
        
        with open(settings_file, 'w') as f:
            f.write(fixed_content)
        print(f"Fixed {settings_file}")
        return True
    else:
        print(f"No syntax issues found in {settings_file}")
        return False

if __name__ == "__main__":
    check_and_fix_settings() 