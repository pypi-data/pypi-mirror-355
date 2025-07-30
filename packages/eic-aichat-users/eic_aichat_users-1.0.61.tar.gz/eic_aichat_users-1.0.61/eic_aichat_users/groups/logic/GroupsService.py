# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from pip_services4_components.config import ConfigParams, IConfigurable
from pip_services4_components.context import IContext
from pip_services4_components.refer import IReferenceable, IReferences, Descriptor
from pip_services4_data.query import FilterParams, PagingParams, DataPage
from pip_services4_data.keys import IdGenerator

from eic_aichat_users.groups.data.GroupV1 import GroupV1
from eic_aichat_users.groups.logic.IGroupsService import IGroupsService
from eic_aichat_users.groups.persistence.IGroupsPersistence import IGroupsPersistence



class GroupsService(IGroupsService, IConfigurable, IReferenceable):
    _persistence: IGroupsPersistence = None
    def configure(self, config: ConfigParams):
        pass  

    def set_references(self, references: IReferences):
        self._persistence = references.get_one_required(
            Descriptor('aichatusers-groups', 'persistence', '*', '*', '1.0')
        )

    def get_groups(self, context: Optional[IContext], filter_params: FilterParams, paging: PagingParams) -> DataPage:
        return self._persistence.get_page_by_filter(context, filter_params, paging)

    def get_group_by_id(self, context: Optional[IContext], group_id: str) -> Optional[GroupV1]:
        return self._persistence.get_one_by_id(context, group_id)

    def create_group(self, context: Optional[IContext], group: GroupV1) -> GroupV1:
        group.id = group.id or IdGenerator.next_long()
        group.active_since = group.active_since or datetime.utcnow()
        return self._persistence.create(context, group)

    def set_group(self, context: Optional[IContext], group: GroupV1) -> GroupV1:
        group.active_since = group.active_since or datetime.utcnow()
        return self._persistence.set(context, group)

    def update_group(self, context: Optional[IContext], group: GroupV1) -> GroupV1:
        return self._persistence.update(context, group)

    def delete_group_by_id(self, context: Optional[IContext], group_id: str) -> Optional[GroupV1]:
        return self._persistence.delete_by_id(context, group_id)

    def delete_groups_by_filter(self, context: Optional[IContext], filter_params: FilterParams) -> None:
        self._persistence.delete_by_filter(context, filter_params)
