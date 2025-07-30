"""
monday.client
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2019 by Christina D'Astolfo.
:license: Apache2, see LICENSE for more details.
"""

from typing import Optional, Dict, Any

from .__version__ import __version__
from .resources import CustomResource, ItemResource, ColumnsResource, UpdateResource, TagResource, BoardResource, \
    UserResource, GroupResource, ComplexityResource, WorkspaceResource, NotificationResource, MeResource

_DEFAULT_HEADERS = {
    "API-Version": "2023-10"
}

DEFAULT_TIMEOUT = 60

class MondayClient:
    def __init__(self, token: str, headers: Optional[Dict[str, Any]] = None, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        :param token: API token for the new :class:`BaseResource` object.
        :param headers: (optional) headers for the new :class:`BaseResource` object.
        :param timeout: (optional) timeout in seconds for API requests.
        """

        if not headers:
            headers = _DEFAULT_HEADERS.copy()

        self.custom: CustomResource = CustomResource(token=token, headers=headers, timeout=timeout)
        self.items: ItemResource = ItemResource(token=token, headers=headers, timeout=timeout)
        self.columns: ColumnsResource = ColumnsResource(token=token, headers=headers, timeout=timeout)
        self.updates: UpdateResource = UpdateResource(token=token, headers=headers, timeout=timeout)
        self.tags: TagResource = TagResource(token=token, headers=headers, timeout=timeout)
        self.boards: BoardResource = BoardResource(token=token, headers=headers, timeout=timeout)
        self.users: UserResource = UserResource(token=token, headers=headers, timeout=timeout)
        self.groups: GroupResource = GroupResource(token=token, headers=headers, timeout=timeout)
        self.complexity: ComplexityResource = ComplexityResource(token=token, headers=headers, timeout=timeout)
        self.workspaces: WorkspaceResource = WorkspaceResource(token=token, headers=headers, timeout=timeout)
        self.notifications: NotificationResource = NotificationResource(token=token, headers=headers, timeout=timeout)
        self.me: MeResource = MeResource(token=token, headers=headers, timeout=timeout)

    def __str__(self) -> str:
        return f'MondayClient {__version__}'

    def __repr__(self) -> str:
        return f'MondayClient {__version__}'
