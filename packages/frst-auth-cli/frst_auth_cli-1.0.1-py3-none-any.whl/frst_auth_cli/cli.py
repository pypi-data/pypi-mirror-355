import typer
import json
import os
from frst_auth_cli.core import FrstAuthClient
from frst_auth_cli.config import load_config
from frst_auth_cli.config import save_config
from frst_auth_cli.config import DEFAULT_CONFIG
from frst_auth_cli.config import CONFIG_PATH

app = typer.Typer()
config_app = typer.Typer()
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init(
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite the config file if it already exists."
    )
):
    """Create or overwrite config.json in the user's home directory."""
    if not force and os.path.exists(CONFIG_PATH):
        typer.echo(f"Config already exists at {CONFIG_PATH}. Use --force to overwrite.")  # noqa E501
        raise typer.Exit(1)
    save_config(DEFAULT_CONFIG)
    typer.echo(f"Config saved at {CONFIG_PATH}.")


@config_app.command("show")
def config_show():
    """Show the current content of config.json."""
    config = load_config()
    typer.echo(json.dumps(config, indent=2))


@app.command()
def verify_backend_token(
    env: str = typer.Argument(..., help="Environment name (e.g. aws-dev, aws-prod, gcp-dev or gcp-prod)"),  # noqa E501
    token: str = typer.Argument(..., help="Backend token to be validated")
):
    """Validate backend_token and return user's groups, default group, and modules."""  # noqa E501
    from frst_auth_cli.exceptions import UserNotFoundError, GroupNotFoundError

    try:
        client = FrstAuthClient(env)
        user = client.verify_backend_token(token)

        typer.echo(f"User: {user.name}")
        typer.echo("Groups:")
        for group in user.groups:
            typer.echo(f"- {group.name} (uuid: {group.uuid})")

        # Default group
        default_group = user.get_group_default()
        typer.echo(f"Default group: {default_group.name}")

        # List modules of the default group
        typer.echo("Modules in default group:")
        for module in default_group.modules:
            typer.echo(f"- {module.get('code')}")

        # Default module
        default_module_code = default_group.module_default
        typer.echo(f"Default module: {default_module_code}")

    except UserNotFoundError:
        typer.echo("User not found or invalid token.")
        raise typer.Exit(1)
    except GroupNotFoundError:
        typer.echo("Group not found for this user.")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@app.command()
def verify_app_token(
    env: str = typer.Argument(..., help="Environment name (e.g. aws-dev, aws-prod, gcp-dev or gcp-prod)"),  # noqa E501
    token: str = typer.Argument(..., help="App token to be validated")
):
    """Validate app_token and return the app's name and permissions."""
    from frst_auth_cli.exceptions import AppNotFoundError

    try:
        client = FrstAuthClient(env)
        app = client.verify_app_token(token)

        typer.echo(f"App: {app.name}")
        typer.echo("Permissions:")
        for perm in app.permissions:
            typer.echo(f"- {perm}")

    except AppNotFoundError:
        typer.echo("App not found or invalid app token.")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
