# -*- coding: utf-8 -*-
from datetime import datetime
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
from eic_aichat_users.groups.logic.IGroupsService import IGroupsService
from eic_aichat_users.partialfacade.operations.version1.Authorize import AuthorizerV1


# TODO
class GroupsMembershipsOperation(RestOperations):
    def __init__(self):
        super().__init__()
        self._group_memberships: IGroupMembershipsService = None
        self._group: IGroupsService = None
        self._dependency_resolver.put('groupmemberships', Descriptor('aichatusers-groupmemberships', 'service', '*', '*', '1.0'))
        self._dependency_resolver.put('groups', Descriptor('aichatusers-groups', 'service', '*', '*', '1.0'))

    def set_references(self, references: IReferences):
        super().set_references(references)
        self._group_memberships = self._dependency_resolver.get_one_required('groupmemberships')
        self._group = self._dependency_resolver.get_one_required('groups')

    def get_memberships(self):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id

        filter_params = self._get_filter_params()
        paging = self._get_paging_params()
        filter_params.set_as_object('profile_id', user_id)

        try:
            page = self._group_memberships.get_memberships(context, filter_params, paging)
            return self._send_result(page)
        except Exception as err:
            return self._send_error(err)

    def get_membership_by_id(self, membership_id: str):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id
        try:
            membership = self._group_memberships.get_membership_by_id(context, membership_id)
            if membership is None or membership.id == "":
                raise BadRequestException(self._get_trace_id(), "WRONG_MEMBERSHIP_ID", "Membership id does not exist")
            if membership.profile_id != user_id:
                raise BadRequestException(self._get_trace_id(), "WRONG_USER", "Profile id does not match user id")
            
            return self._send_result(membership)
        except Exception as err:
            return self._send_error(err)

    def create_membership(self):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id

        data = bottle.request.json
        groupMembership_data = data if isinstance(data, dict) else json.loads(data or '{}')
        groupMembership = GroupMembershipV1(**groupMembership_data)

        try:
            group = self._group.get_group_by_id(context, groupMembership.group_id)
            if group is None or group.id == "":
                raise BadRequestException(self._get_trace_id(), "WRONG_GROUP_ID", "Group id does not exist")
            if group.owner_id != user_id:
                raise BadRequestException(self._get_trace_id(), "WRONG_USER", "User id does not match group owner id")
            
            memberships = self._group_memberships.create_membership(context, groupMembership)
            return self._send_result(memberships)
        except Exception as err:
            return self._send_error(err)
        
    def update_membership(self):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id
    
        data = bottle.request.json
        groupMembership_data = data if isinstance(data, dict) else json.loads(data or '{}')
        groupMembership = GroupMembershipV1(**groupMembership_data)

        try:
            group = self._group.get_group_by_id(context, groupMembership.group_id)
            if group is None or group.id == "":
                raise BadRequestException(self._get_trace_id(), "WRONG_GROUP_ID", "Group id does not exist")
            if group.owner_id != user_id:
                raise BadRequestException(self._get_trace_id(), "WRONG_USER", "User id does not match group owner id")
            
            memberships = self._group_memberships.update_membership(context, groupMembership)
            return self._send_result(memberships)
        except Exception as err:
            return self._send_error(err)
        
    def delete_membership_by_id(self, id):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id
        try:
            membership = self._group_memberships.get_membership_by_id(context, id)
            if membership is None or membership.id == "":
                raise BadRequestException(self._get_trace_id(), "WRONG_MEMBERSHIP_ID", "Membership id does not exist")
            if membership.profile_id != user_id:
                raise BadRequestException(self._get_trace_id(), "WRONG_USER", "Profile id does not match user id")
            
            memberships = self._group_memberships.delete_membership_by_id(context, id)
            return self._send_result(memberships)
        except Exception as err:
            return self._send_error(err)
        
    def delete_membership_by_filter(self):
        context = Context.from_trace_id(self._get_trace_id())
        filter_params = self._get_filter_params()
        try:
            res = self._group.delete_groups_by_filter(context, filter_params)
            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)
        
    def activate_membership_by_id(self, id):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id
        try:
            membership = self._group_memberships.get_membership_by_id(context, id)
            if membership is None or membership.id == "":
                raise BadRequestException(self._get_trace_id(), "WRONG_ID", "Id does not exist")
            
            group = self._group.get_group_by_id(context, membership.group_id)
            if group is None or group.id == "":
                raise BadRequestException(self._get_trace_id(), "WRONG_GROUP_ID", "Group id does not exist")
            if group.owner_id != user_id:
                raise BadRequestException(self._get_trace_id(), "WRONG_USER", "User id does not match group owner id")
            
            membership.active = True
            membership.member_since = datetime.utcnow()
            
            res = self._group_memberships.update_membership(context, membership)
            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)
        
    def deactivate_membership_by_id(self, id):
        context = Context.from_trace_id(self._get_trace_id())
        user_id = bottle.request.user_id
        try:
            membership = self._group_memberships.get_membership_by_id(context, id)
            if membership is None or membership.id == "":
                raise BadRequestException(self._get_trace_id(), "WRONG_ID", "Id does not exist")
            
            group = self._group.get_group_by_id(context, membership.group_id)
            if group is None or group.id == "":
                raise BadRequestException(self._get_trace_id(), "WRONG_GROUP_ID", "Group id does not exist")
            if group.owner_id != user_id:
                raise BadRequestException(self._get_trace_id(), "WRONG_USER", "User id does not match group owner id")
            
            membership.active = False
            
            res = self._group_memberships.update_membership(context, membership)
            return self._send_result(res)
        except Exception as err:
            return self._send_error(err)
        
    def register_routes(self, controller: RestController, auth: AuthorizerV1):
            controller.register_route_with_auth('get', '/users/groups/memberships', None, auth.signed(), lambda: self.get_memberships())
            
            controller.register_route_with_auth('get', '/users/groups/:id/memberships', None, auth.signed(), lambda id: self.get_membership_by_id(id))

            controller.register_route_with_auth('post', '/users/groups/memberships', None, auth.signed(), lambda: self.create_membership())

            controller.register_route_with_auth('put', '/users/groups/memberships', None, auth.signed(), lambda: self.update_membership())

            controller.register_route_with_auth('delete', '/users/groups/:id/memberships', None, auth.signed(), lambda id: self.delete_membership_by_id(id))

            controller.register_route_with_auth('delete', '/users/groups/memberships', None, auth.admin(), lambda: self.delete_membership_by_filter())

            controller.register_route_with_auth('post', '/users/groups/:id/memberships/activate', None, auth.signed(), lambda id: self.activate_membership_by_id(id))

            controller.register_route_with_auth('post', '/users/groups/:id/memberships/deactivate', None, auth.signed(), lambda id: self.deactivate_membership_by_id(id))
            
        
