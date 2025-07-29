from pathlib import Path
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)

def generate_code(spec, output_path: str | Path):
    ctx = {"spec": spec}
    code = env.get_template("main.j2").render(**ctx)
    Path(output_path).write_text(code, encoding="utf-8")
