import typer, pathlib, sys
from metadspy.parser import load_spec
from metadspy.generator import generate_code

app = typer.Typer(add_completion=False)

@app.command()
def build(spec: str, out: str = "dspy_program.py"):
    """Generate a DSPy script from a YAML/JSON spec."""
    spec_obj = load_spec(spec)
    generate_code(spec_obj, output_path=out)
    typer.echo(f"✓  wrote {out}")

if __name__ == "__main__":  # direct file execution
    sys.exit(app())
