import subprocess

def get_pip_index(domain: str, owner: str, region: str, repo: str) -> str:
    result = subprocess.run([
        'aws', 'codeartifact', 'get-authorization-token',
        '--domain', domain,
        '--domain-owner', owner,
        '--region', region,
        '--query', 'authorizationToken',
        '--output', 'text'
    ], capture_output=True, text=True, check=True)
    token = result.stdout.strip()
    index_url = f"https://aws:{token}@{domain}-{owner}.d.codeartifact.{region}.amazonaws.com/pypi/{repo}/simple/"
    return index_url
