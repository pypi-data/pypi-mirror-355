"""Console script for sumtools."""

import typer

app = typer.Typer()


@app.command()
def main():
    """Run the main CLI command."""
    typer.echo("sumtools")
    typer.echo("=" * len("sumtools"))
    typer.echo("a suite for summary level GWAS downstream analysis")


if __name__ == "__main__":
    app()  # pragma: no cover
