# -*- coding: utf-8 -*-
from typing import Any, Optional
from datetime import datetime

from pip_services4_data.data import IStringIdentifiable
from pip_services4_data.keys import IdGenerator


class IStringIdentifiable:
    id: str


class GroupMembershipV1(IStringIdentifiable):
    def __init__(
        self,
        id: Optional[str] = None,
        profile_id: Optional[str] = None,
        group_id: Optional[str] = None,
        created: Optional[datetime] = None,
        active: Optional[bool] = True,
        member_since: Optional[datetime] = None
    ):
        self.id: str = id or IdGenerator.next_long()
        self.profile_id = profile_id
        self.group_id = group_id
        self.created = created or datetime.utcnow()
        self.active = active if active is not None else True
        self.member_since = member_since or datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "group_id": self.group_id,
            "created": self.created.isoformat() if isinstance(self.created, datetime) else self.created,
            "active": self.active,
            "member_since": self.member_since.isoformat() if isinstance(self.member_since, datetime) else self.member_since
        }
