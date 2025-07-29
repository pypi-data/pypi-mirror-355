"""cli entry to find the user who owns a file or directory."""
import click
from damply.admin import UserInfo
from pathlib import Path

class WindowsNotSupportedError(NotImplementedError):
    """Exception raised when trying to use pwd module on Windows."""
    pass



@click.command()
@click.argument(
    'path',
    type=click.Path(
        exists=True,
        path_type=Path,
        file_okay=True,
        dir_okay=True,
        readable=True,
    ),
    default=Path().cwd(),
)
@click.option(
    '--json',
    '-j',
    is_flag=True,
    help="Output in JSON format.",
)
def whose(path: Path, json: bool) -> None:
    """Print the owner of the file or directory."""
    import platform
    if platform.system() == "Windows":
        raise WindowsNotSupportedError(
            "The 'whose' command is not supported on Windows. "
        )

    # get the files owner
    file_owner = path.stat().st_uid

    # get the user info
    user_info = UserInfo.from_uid(file_owner)
    if user_info is None:
        click.echo(f"No user found for UID {file_owner}.")
        return
    
    if json:
        info_dict = {
            "path": str(path.resolve()),
            "username": user_info.name,
            "uid": user_info.uid,
            "realname": user_info.realname,
        }
        import json
        click.echo(json.dumps(info_dict, indent=2))
    else:
        click.echo(f"Path: {path.resolve()}")
        click.echo(f"Username: {user_info.name}")
        click.echo(f"UID: {user_info.uid}")
        click.echo(f"Real Name: {user_info.realname}")