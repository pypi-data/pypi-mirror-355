import typer

from alr_spec.core.update import update_package_logic

app = typer.Typer()


@app.command(help="Update package (version, release, checksums)")
def update_package(
    package_path: str = typer.Argument(
        ".", help="Путь к пакету (папке или alr.sh)"
    ),
    only_check: bool = typer.Option(
        False, "--only-check", help="Only check for updates"
    ),
    no_checksums: bool = typer.Option(
        False, "--no-checksums", help="Disable checksums update"
    ),
):
    try:
        update_package_logic(package_path, no_checksums, only_check)
    except Exception as e:
        typer.echo(f"Ошибка: {e}")
        raise typer.Exit(code=1)
