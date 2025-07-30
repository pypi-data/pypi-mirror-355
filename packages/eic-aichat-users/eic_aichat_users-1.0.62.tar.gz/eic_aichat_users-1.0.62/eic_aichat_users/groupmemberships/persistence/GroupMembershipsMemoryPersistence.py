# -*- coding: utf-8 -*-
from typing import Optional, Callable, Any

from pip_services4_components.context import IContext
from pip_services4_data.query import FilterParams, PagingParams, DataPage
from pip_services4_persistence.persistence import IdentifiableMemoryPersistence

from ..data import GroupMembershipV1
from .IGroupMembershipsPersistence import IGroupMembershipsPersistence


class GroupMembershipsMemoryPersistence(IdentifiableMemoryPersistence, IGroupMembershipsPersistence):

    def __init__(self):
        super().__init__()
        self._max_page_size = 100

    def __compose_filter(self, filter_params: Optional[FilterParams]) -> Callable[[GroupMembershipV1], bool]:
        filter_params = filter_params or FilterParams()

        id = filter_params.get_as_nullable_string('id')
        profile_id = filter_params.get_as_nullable_string('profile_id')
        group_id = filter_params.get_as_nullable_string('group_id')
        active = filter_params.get_as_nullable_boolean('active')
        offline_or_online_id = filter_params.get_as_nullable_string('offline_or_onlie_id')

        def to_list(value: Any) -> Optional[list]:
            if isinstance(value, str):
                return value.split(',')
            if isinstance(value, list):
                return value
            return None

        ids = to_list(filter_params.get_as_object('ids'))
        profile_ids = to_list(filter_params.get_as_object('profile_ids'))
        group_ids = to_list(filter_params.get_as_object('group_ids'))
        offline_or_online_ids = to_list(filter_params.get_as_object('offline_or_onlie_id'))

        def predicate(item: GroupMembershipV1) -> bool:
            if id and item.id != id:
                return False
            if ids and item.id not in ids:
                return False
            if profile_ids and item.profile_id not in profile_ids:
                return False
            if group_ids and item.group_id not in group_ids:
                return False
            if profile_id and item.profile_id != profile_id:
                return False
            if group_id and item.group_id != group_id:
                return False
            if active is not None and item.active != active:
                return False
            if offline_or_online_id and item.profile_id != offline_or_online_id and item.offline_id != offline_or_online_id:
                return False
            if offline_or_online_ids and item.profile_id not in offline_or_online_ids and item.offline_id not in offline_or_online_ids:
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

    def create(self, context: Optional[IContext], item: GroupMembershipV1) -> GroupMembershipV1:
        self._check_if_exists(context, item)
        return super().create(context, item)

    def update(self, context: Optional[IContext], item: GroupMembershipV1) -> GroupMembershipV1:
        self._check_if_exists(context, item)
        return super().update(context, item)

    def _check_if_exists(self, context: Optional[IContext], item: GroupMembershipV1) -> None:
        page = self.get_page_by_filter(
            context,
            FilterParams.from_tuples(
                'profile_id', item.profile_id,
                'group_id', item.group_id
            ),
            None
        )

        if not item.id and page.data:
            item.id = page.data[0].id

        if len(page.data) > 1 or (page.data and page.data[0].id != item.id):
            raise Exception("Group membership already exists")
