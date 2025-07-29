import stat
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, date
from pathlib import Path

import rich.repr
from rich import print

@dataclass
class DirectoryAudit:
    path: Path
    owner: str
    group: str
    full_name: str
    permissions: str
    last_accessed: date
    last_modified: date
    last_changed: date

    @classmethod
    def from_path(cls, path: Path) -> 'DirectoryAudit':
        # resolve ~ and expand environment variables and canonicalize the path
        path = path.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"The path {path} does not exist.")

        stats = path.stat()

        try:
            from pwd import getpwuid
            from grp import getgrgid

            pwuid_name = getpwuid(stats.st_uid).pw_name
            pwuid_gecos = getpwuid(stats.st_uid).pw_gecos
            group_name = getgrgid(stats.st_gid).gr_name
        except ImportError:
            pwuid_name = 'Unknown'
            pwuid_gecos = 'Unknown'
            group_name = 'Unknown'
        except KeyError:
            pwuid_name = 'Unknown'
            pwuid_gecos = 'Unknown'
            group_name = 'Unknown'

        return DirectoryAudit(
            path=path,
            owner=pwuid_name,
            group=group_name,
            full_name=pwuid_gecos,
            permissions=stat.filemode(stats.st_mode),
            last_accessed=datetime.fromtimestamp(stats.st_atime, tz=timezone.utc).date(),
            last_modified=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).date(),
            last_changed=datetime.fromtimestamp(stats.st_ctime, tz=timezone.utc).date(),
        )

    def __rich_repr__(self) -> rich.repr.Result:
        yield 'path', self.path.absolute()
        yield 'owner', self.owner
        yield 'group', self.group
        yield 'full_name', self.full_name
        yield 'permissions', self.permissions
        yield 'last_accessed', self.last_accessed
        yield 'last_modified', self.last_modified
        yield 'last_changed', self.last_changed
        
    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 4) -> str:
        import json
        return json.dumps(self.to_dict(), default=str, indent=indent)


if __name__ == '__main__':
    from rich import print
    audit = DirectoryAudit.from_path(Path('/cluster/projects/bhklab/projects/BTCIS'))
    print(audit)

    print("*" * 20)
    print(audit.to_dict())
    print("*" * 20)
    print(audit.to_json())