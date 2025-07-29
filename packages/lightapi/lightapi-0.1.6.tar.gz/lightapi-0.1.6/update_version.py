import sys
import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import tomli_w

def get_current_version():
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)
    return data['project']['version']

def increment_version(version):
    parts = version.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)

def update_version(new_version):
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)
    
    data['project']['version'] = new_version
    
    with open('pyproject.toml', 'wb') as f:
        tomli_w.dump(data, f)

if __name__ == "__main__":
    current = get_current_version()
    new = increment_version(current)
    update_version(new)
    print(f"Updated version from {current} to {new}")
    
    # Write to GitHub output
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"new_version={new}\n")
