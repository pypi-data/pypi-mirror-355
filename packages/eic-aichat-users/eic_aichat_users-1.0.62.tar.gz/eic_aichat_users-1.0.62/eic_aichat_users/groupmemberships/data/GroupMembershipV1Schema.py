# -*- coding: utf-8 -*-
from pip_services4_commons.convert import TypeCode
from pip_services4_data.validate import ObjectSchema


class GroupMembershipV1Schema(ObjectSchema):
    def __init__(self):
        super().__init__()

        self.with_optional_property('id', TypeCode.String)
        self.with_optional_property('profile_id', TypeCode.String)
        self.with_required_property('group_id', TypeCode.String)
        self.with_optional_property('created', TypeCode.DateTime)
        self.with_required_property('active', TypeCode.Boolean)
        self.with_required_property('member_since', TypeCode.DateTime)
