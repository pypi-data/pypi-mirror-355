import grp
from dataclasses import asdict, dataclass


# custom exception for group not found
class GroupNotFoundError(Exception):
	def __init__(self, group_name: str) -> None:
		super().__init__(f"Group '{group_name}' not found.")
		self.group_name = group_name


@dataclass
class GroupInfo:
	name: str
	gid: int
	members: list[str]

	@classmethod
	def from_group_name(cls, group_name: str) -> 'GroupInfo':
		try:
			group_data = grp.getgrnam(group_name)
		except KeyError as e:
			raise GroupNotFoundError(group_name) from e
		else:
			return cls(
				name=group_data.gr_name,
				gid=group_data.gr_gid,
				members=group_data.gr_mem,
			)

	@classmethod
	def from_group_id(cls, group: int) -> 'GroupInfo':
		try:
			group_data = grp.getgrgid(group)
		except KeyError as e:
			msg = f'GID {group}'
			raise GroupNotFoundError(msg) from e
		else:
			return cls(
				name=group_data.gr_name,
				gid=group_data.gr_gid,
				members=group_data.gr_mem,
			)

	def to_dict(self) -> dict:
		return asdict(self)

	def to_json(self, indent: int = 4) -> str:
		import json

		return json.dumps(self.to_dict(), indent=indent)


def get_all_groups() -> list[GroupInfo]:
	"""Returns a list of all groups on the system."""
	all_groups = []
	for group_data in grp.getgrall():
		all_groups.append(GroupInfo.from_group_id(group_data.gr_gid))
	return all_groups


if __name__ == '__main__':
	pass
