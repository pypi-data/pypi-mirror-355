# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Optional

from pip_services4_components.context import IContext
from pip_services4_data.query import FilterParams, PagingParams, DataPage

from ..data import GroupMembershipV1


class IGroupMembershipsService(ABC):

    @abstractmethod
    def get_memberships(self, context: Optional[IContext], filter_params: FilterParams,
                        paging: PagingParams) -> DataPage:
        raise NotImplementedError()

    @abstractmethod
    def get_membership_by_id(self, context: Optional[IContext], membership_id: str) -> Optional[GroupMembershipV1]:
        raise NotImplementedError()

    @abstractmethod
    def create_membership(self, context: Optional[IContext], membership: GroupMembershipV1) -> GroupMembershipV1:
        raise NotImplementedError()

    @abstractmethod
    def update_membership(self, context: Optional[IContext], membership: GroupMembershipV1) -> GroupMembershipV1:
        raise NotImplementedError()

    @abstractmethod
    def delete_membership_by_id(self, context: Optional[IContext], membership_id: str) -> Optional[GroupMembershipV1]:
        raise NotImplementedError()

    @abstractmethod
    def delete_memberships_by_filter(self, context: Optional[IContext], filter_params: FilterParams) -> None:
        raise NotImplementedError()
