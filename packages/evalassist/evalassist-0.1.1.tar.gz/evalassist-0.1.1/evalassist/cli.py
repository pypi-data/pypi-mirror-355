import click
from .main import app
import uvicorn

@click.group()
def cli():
    pass

@cli.command()
def serve():
    uvicorn.run(app, host="0.0.0.0", port=8000)

@cli.command()
def version():
    click.echo("evalassist v0.1.1")

def main():
    cli()