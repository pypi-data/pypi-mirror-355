# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Optional

from pip_services4_components.context import IContext
from pip_services4_data.query import FilterParams, PagingParams, DataPage

from eic_aichat_users.groups.data.GroupV1 import GroupV1


class IGroupsService(ABC):

    @abstractmethod
    def get_groups(self, context: Optional[IContext], filter_params: FilterParams, paging: PagingParams) -> DataPage:
        raise NotImplementedError()

    @abstractmethod
    def get_group_by_id(self, context: Optional[IContext], group_id: str) -> Optional[GroupV1]:
        raise NotImplementedError()

    @abstractmethod
    def create_group(self, context: Optional[IContext], group: GroupV1) -> GroupV1:
        raise NotImplementedError()

    @abstractmethod
    def set_group(self, context: Optional[IContext], group: GroupV1) -> GroupV1:
        raise NotImplementedError()

    @abstractmethod
    def update_group(self, context: Optional[IContext], group: GroupV1) -> GroupV1:
        raise NotImplementedError()

    @abstractmethod
    def delete_group_by_id(self, context: Optional[IContext], group_id: str) -> Optional[GroupV1]:
        raise NotImplementedError()

    @abstractmethod
    def delete_groups_by_filter(self, context: Optional[IContext], filter_params: FilterParams) -> None:
        raise NotImplementedError()
