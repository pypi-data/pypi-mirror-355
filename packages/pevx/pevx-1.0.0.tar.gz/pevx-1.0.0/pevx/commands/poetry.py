#!/usr/bin/env python3
import click
import os
import subprocess

@click.command()
@click.option('--domain', '-d', default='prudentia-sciences', help='CodeArtifact domain')
@click.option('--domain-owner', '-o', default='728222516696', help='CodeArtifact domain owner')
@click.option('--repo', '-r', default='pypi-store', help='CodeArtifact repository name')
@click.option('--region', '-reg', default='us-east-1', help='AWS region')
@click.option('--priority', '-p', default='supplemental', help='Priority for the source')
def add_codeartifact(domain, domain_owner, repo, region, priority):
    """Authenticate poetry with AWS CodeArtifact."""
    click.echo("Authenticating poetry with AWS CodeArtifact...")

    # Set environment variables
    os.environ['CODEARTIFACT_DOMAIN'] = domain
    os.environ['CODEARTIFACT_DOMAIN_OWNER'] = domain_owner
    os.environ['CODEARTIFACT_REPO'] = repo
    os.environ['CODEARTIFACT_REGION'] = region

    try:
        # Get AWS CodeArtifact token
        click.echo("Getting AWS CodeArtifact token...")
        result = subprocess.run([
            'aws', 'codeartifact', 'get-authorization-token',
            '--domain', domain,
            '--domain-owner', domain_owner,
            '--region', region,
            '--query', 'authorizationToken',
            '--output', 'text'
        ], capture_output=True, text=True, check=True)

        token = result.stdout.strip()
        if not token:
            click.echo("Error: Failed to retrieve CodeArtifact token. Check your AWS credentials.")
            return 1

        os.environ['CODEARTIFACT_AUTH_TOKEN'] = token

        # Configure repository URL
        repo_url = f"https://{domain}-{domain_owner}.d.codeartifact.{region}.amazonaws.com/pypi/{repo}/simple/"

        # Remove existing source if it exists
        click.echo("Configuring poetry...")
        subprocess.run(['poetry', 'source', 'remove', 'codeartifact'],
                      stderr=subprocess.DEVNULL, check=False)

        # Add source
        subprocess.run(['poetry', 'source', 'add', 'codeartifact', repo_url, '--priority', priority], check=True)

        # Configure basic auth
        subprocess.run(['poetry', 'config', 'http-basic.codeartifact', 'aws', token], check=True)

        click.echo("Successfully authenticated poetry with AWS CodeArtifact!")
        return 0

    except subprocess.CalledProcessError as e:
        click.echo(f"Error executing command: {e}")
        if e.stderr:
            click.echo(f"Error details: {e.stderr}")
        return 1
    except Exception as e:
        click.echo(f"Unexpected error: {e}")
        return 1