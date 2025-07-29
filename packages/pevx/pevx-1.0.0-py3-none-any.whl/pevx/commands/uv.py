import click
import subprocess

from pevx.utils import get_pip_index

@click.command("add")
@click.option('--domain', default='prudentia-sciences')
@click.option('--owner', default='728222516696')
@click.option('--region', default='us-east-1')
@click.option('--repo', default='pypi-store')
@click.argument('package')
def add_package(domain, owner, region, repo, package):
    """Install package from AWS CodeArtifact using uv."""
    click.echo("Getting token from AWS CodeArtifact...")
    index_url = get_pip_index(domain=domain, owner=owner, region=region, repo=repo)
    subprocess.run(['uv', 'add', package, '--index-url', index_url], check=True)
