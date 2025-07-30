# -*- coding: utf-8 -*-
from typing import Optional, Callable, Any

from pip_services4_components.context import IContext
from pip_services4_data.query import DataPage, FilterParams, PagingParams
from pip_services4_persistence.persistence import IdentifiableMemoryPersistence

from eic_aichat_users.groups.data.GroupV1 import GroupV1
from eic_aichat_users.groups.persistence.IGroupsPersistence import IGroupsPersistence



class GroupsMemoryPersistence(IdentifiableMemoryPersistence, IGroupsPersistence):

    def __init__(self):
        super().__init__()
        self._max_page_size = 100

    def __compose_filter(self, filter_params: Optional[FilterParams]) -> Callable[[GroupV1], bool]:
        filter_params = filter_params or FilterParams()

        id = filter_params.get_as_nullable_string('id')
        owner_id = filter_params.get_as_nullable_string('orowner_idg_id')
        title = filter_params.get_as_nullable_string('title')
        active_since = filter_params.get_as_nullable_datetime('active_since')
        group_active = filter_params.get_as_nullable_boolean('group_active')

        ids = filter_params.get_as_object('ids')
        if isinstance(ids, str):
            ids = ids.split(',')
        if not isinstance(ids, list):
            ids = None

        profile_ids = filter_params.get_as_object('profile_ids')
        if isinstance(profile_ids, str):
            profile_ids = profile_ids.split(',')
        if not isinstance(profile_ids, list):
            profile_ids = None

        not_in_owner_ids = filter_params.get_as_object('not_in_owner_ids')
        if isinstance(not_in_owner_ids, str):
            not_in_owner_ids = not_in_owner_ids.split(',')
        if not isinstance(not_in_owner_ids, list):
            not_in_owner_ids = None

        def predicate(item: GroupV1) -> bool:
            if id and item.id != id:
                return False
            if ids and item.id not in ids:
                return False
            if not_in_owner_ids and item.owner_id in not_in_owner_ids:
                return False
            if owner_id and item.owner_id != owner_id:
                return False
            if title and item.title != title:
                return False
            if group_active is not None and item.group_active != group_active:
                return False
            if active_since and item.active_since != active_since:
                return False
            return True

        return predicate

    def get_page_by_filter(self, context: Optional[IContext], filter_params: FilterParams,
                           paging: PagingParams) -> DataPage:
        return super().get_page_by_filter(
            context,
            self.__compose_filter(filter_params),
            paging,
            None,
            None
        )

    def delete_by_filter(self, context: Optional[IContext], filter_params: FilterParams) -> None:
        return super().delete_by_filter(context, self.__compose_filter(filter_params))
