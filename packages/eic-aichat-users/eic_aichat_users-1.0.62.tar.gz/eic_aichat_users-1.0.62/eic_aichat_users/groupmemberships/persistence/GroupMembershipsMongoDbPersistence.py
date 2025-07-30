# -*- coding: utf-8 -*-
from typing import Optional, Any

from pip_services4_components.context import IContext
from pip_services4_data.query import FilterParams, PagingParams, DataPage
from pip_services4_mongodb.persistence import IdentifiableMongoDbPersistence

from ..data import GroupMembershipV1
from .IGroupMembershipsPersistence import IGroupMembershipsPersistence


class GroupMembershipsMongoDbPersistence(IdentifiableMongoDbPersistence, IGroupMembershipsPersistence):

    def __init__(self):
        super().__init__('group_memberships')
        self._max_page_size = 100

        self._ensure_index({ "profile_id": 1 })
        self._ensure_index({ "group_id": 1 })
        self._ensure_index({ "group_id": 1,  "profile_id": 1}, { 'unique': True })

    def _compose_filter(self, filter_params: Optional[FilterParams]) -> Any:
        filter_params = filter_params or FilterParams()
        criteria = []

        def to_list(value):
            if isinstance(value, str):
                return value.split(',')
            elif isinstance(value, list):
                return value
            return None

        id = filter_params.get_as_nullable_string('id')
        if id:
            criteria.append({ '_id': id })

        ids = to_list(filter_params.get_as_object('ids'))
        if ids:
            criteria.append({ '_id': { '$in': ids } })

        profile_ids = to_list(filter_params.get_as_object('profile_ids'))
        if profile_ids:
            criteria.append({ 'profile_id': { '$in': profile_ids } })

        profile_id = filter_params.get_as_nullable_string('profile_id')
        if profile_id:
            criteria.append({ 'profile_id': profile_id })

        offline_id = filter_params.get_as_nullable_string('offline_id')
        if offline_id:
            criteria.append({ 'offline_id': offline_id })

        group_id = filter_params.get_as_nullable_string('group_id')
        if group_id:
            criteria.append({ 'group_id': group_id })

        active = filter_params.get_as_nullable_boolean('active')
        if active is not None:
            criteria.append({ 'active': active })

        attempts = filter_params.get_as_nullable_integer('attempts')
        if attempts is not None:
            criteria.append({ 'attempts': attempts })

        return { '$and': criteria } if criteria else {}

    def get_page_by_filter(self, context: Optional[IContext], filter_params: FilterParams,
                                 paging: PagingParams) -> DataPage:
        return super().get_page_by_filter(
            context,
            self._compose_filter(filter_params),
            paging,
            None,
            None
        )

    def delete_by_filter(self, context: Optional[IContext], filter_params: FilterParams) -> None:
        super().delete_by_filter(context, self._compose_filter(filter_params))

    def create(self, context: Optional[IContext], item: GroupMembershipV1) -> GroupMembershipV1:
        return super().create(context, item)
