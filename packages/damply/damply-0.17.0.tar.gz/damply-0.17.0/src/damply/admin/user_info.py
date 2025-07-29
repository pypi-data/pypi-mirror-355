"""utility function to get the user info of the current user or via stat uid"""

from __future__ import annotations

import pwd
from dataclasses import asdict, dataclass


@dataclass
class UserInfo:
	"""Data class to hold user information."""

	uid: int
	name: str
	realname: str | None = None
	default_group: str | None = None

	@classmethod
	def from_username(cls, name: str) -> UserInfo:
		"""Create a UserInfo instance from a username."""
		try:
			user = pwd.getpwnam(name)
		except KeyError as ke:
			msg = f"User '{name}' does not exist."
			raise ValueError(msg) from ke

		try:
			from damply.admin.group_info import GroupInfo

			default_group = GroupInfo.from_group_id(user.pw_gid).name
		except ValueError:
			default_group = None

		return cls(
			uid=user.pw_uid,
			name=user.pw_name,
			realname=user.pw_gecos.split(',')[0] if user.pw_gecos else None,
			default_group=default_group,
		)

	@classmethod
	def from_uid(cls, uid: int) -> UserInfo:
		"""Create a UserInfo instance from a user ID."""
		try:
			user = pwd.getpwuid(uid)
		except KeyError as ke:
			msg = f'User with UID {uid} does not exist.'
			raise ValueError(msg) from ke

		try:
			from damply.admin.group_info import GroupInfo

			default_group = GroupInfo.from_group_id(user.pw_gid).name
		except ValueError:
			default_group = None

		return cls(
			uid=user.pw_uid,
			name=user.pw_name,
			realname=user.pw_gecos.split(',')[0] if user.pw_gecos else None,
			default_group=default_group,
		)

	def to_dict(self) -> dict[str, any]:
		"""Convert the UserInfo instance to a dictionary."""
		base_dict = asdict(self)
		# add groups to the dictionary
		base_dict['groups'] = self.groups
		return base_dict

	@property
	def groups(self) -> list[str]:
		"""Get the list of groups the user belongs to.

		Because of our permissions, we have to use subprocess and `groups <user>`
		to get the groups of the user.
		Returns:
		    list[str]: List of group names the user belongs to.
		"""
		import subprocess

		try:
			result = subprocess.run(
				['groups', self.name], capture_output=True, text=True, check=True
			)
			groups = result.stdout.strip().split(': ')[1].split()
		except subprocess.CalledProcessError as e:
			msg = f'Failed to get groups for user {self.name}: {e}'
			raise RuntimeError(msg) from e
		else:
			return groups

	def __repr__(self) -> str:
		return (
			f'UserInfo(uid={self.uid}, '
			f"name='{self.name}', "
			f"realname='{self.realname}', "
			f"default_group='{self.default_group}', "
			f'groups={self.groups})'
		)


if __name__ == '__main__':
	pass
