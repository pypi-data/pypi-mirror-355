# -*- coding: utf-8 -*-
import json
import bottle
import asyncio

from typing import List
from pip_services4_components.refer import Descriptor, IReferences
from pip_services4_http.controller import RestOperations, RestController
from pip_services4_commons.errors import BadRequestException
from pip_services4_data.query import FilterParams
from pip_services4_components.context import Context

from eic_aichat_users.groupmemberships.data.GroupMembershipV1 import GroupMembershipV1
from eic_aichat_users.groupmemberships.logic.IGroupMembershipsService import IGroupMembershipsService
from eic_aichat_users.groups.data.GroupV1 import GroupV1
from eic_aichat_users.groups.logic.IGroupsService import IGroupsService
from eic_aichat_users.partialfacade.operations.version1.Authorize import AuthorizerV1


# TODO
class GroupsOperation(RestOperations):
    def __init__(self):
        super().__init__()
        self._group: IGroupsService = None
        self._group_memberships: IGroupMembershipsService = None
        self._dependency_resolver.put('groups', Descriptor('aichatusers-groups', 'service', '*', '*', '1.0'))
        self._dependency_resolver.put('groupmemberships', Descriptor('aichatusers-groupmemberships', 'service', '*', '*', '1.0'))

    def set_references(self, references: IReferences):
        super().set_references(references)
        self._group = self._dependency_resolver.get_one_required('groups')
        self._group_memberships = self._dependency_resolver.get_one_required('groupmemberships')

    def get_groups(self):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id

        filter_params = self._get_filter_params()
        paging = self._get_paging_params()

        filter_params.set_as_object('owner_id', user_id)
        try:
            page = self._group.get_groups(context, filter_params, paging)
            return self._send_result(page)
        except Exception as err:
            return self._send_error(err)

    def get_group_by_id(self, id: str):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id
        try:
            res = self._group.get_group_by_id(context, id)
            if res is None or res.id == "":
                raise BadRequestException('Group ' + id + ' not found')

            if res.owner_id != user_id:
                raise BadRequestException('Group ' + id + ' is not owned by user ' + user_id)
            
            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)

    def create_group(self):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id

        data = bottle.request.json
        group_data = data if isinstance(data, dict) else json.loads(data or '{}')
        group = GroupV1(**group_data)

        group.owner_id = user_id

        try:
            res = self._group.create_group(context, group)
            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)
        
    def set_group(self):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id

        data = bottle.request.json
        group_data = data if isinstance(data, dict) else json.loads(data or '{}')
        group = GroupV1(**group_data)
        group.owner_id = user_id

        try:
            res = self._group.set_group(context, group)
            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)
        
    def update_group(self):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id

        data = bottle.request.json
        group_data = data if isinstance(data, dict) else json.loads(data or '{}')
        group = GroupV1(**group_data)
        group.owner_id = user_id

        try:
            old_group = self._group.get_group_by_id(context, group.id)
            if old_group is None or old_group.id == "":
                raise BadRequestException('Group ' + id + ' not found')

            if old_group.owner_id != user_id:
                raise BadRequestException('Group ' + id + ' is not owned by user ' + user_id)
            
            res = self._group.update_group(context, group)
            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)
        

    def delete_group_by_id(self, id):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id
        try:
            old_group = self._group.get_group_by_id(context, id)
            if old_group is None or old_group.id == "":
                raise BadRequestException('Group ' + id + ' not found')

            if old_group.owner_id != user_id:
                raise BadRequestException('Group ' + id + ' is not owned by user ' + user_id)
            
            res = self._group.delete_group_by_id(context, id)

            page = self._group_memberships.get_memberships(context, FilterParams().set_as_object('group_id', id), None)
            for membership in page.data:
                self._group_memberships.delete_membership_by_id(context, membership.id)

            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)
        
    def delete_group_by_filter(self):
        context = Context.from_trace_id(self._get_trace_id())
        filter_params = self._get_filter_params()
        try:
            res = self._group.delete_groups_by_filter(context, filter_params)
            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)
        
    def register_routes(self, controller: RestController, auth: AuthorizerV1):
        controller.register_route_with_auth('get', '/users/groups', None, auth.signed(), lambda: self.get_groups())
        
        controller.register_route_with_auth('get', '/users/:id/groups', None, auth.signed(), lambda id: self.get_group_by_id(id))

        controller.register_route_with_auth('post', '/users/groups', None, auth.signed(), lambda: self.create_group())

        controller.register_route_with_auth('post', '/users/groups/set', None, auth.signed(), lambda: self.set_group())

        controller.register_route_with_auth('put', '/users/groups', None, auth.signed(), lambda: self.update_group())

        controller.register_route_with_auth('delete', '/users/:id/groups', None, auth.signed(), lambda id: self.delete_group_by_id(id))

        controller.register_route_with_auth('delete', '/users/groups', None, auth.admin(), lambda: self.delete_group_by_filter())
        
    