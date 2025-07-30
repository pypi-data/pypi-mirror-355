# -*- coding: utf-8 -*-
from typing import Any, Optional
from datetime import datetime

from pip_services4_data.data import IStringIdentifiable
from pip_services4_data.keys import IdGenerator

class GroupV1(IStringIdentifiable):
    def __init__(
        self,
        id: Optional[str] = None,
        title: Optional[str] = None,
        active_since: Optional[datetime] = None,
        owner_id: Optional[str] = None,
        group_active: Optional[bool] = True,

    ):
        self.id: str = id or IdGenerator.next_long()
        self.title = title
        self.active_since = active_since or datetime.now()
        self.owner_id = owner_id
        self.group_active = group_active or True

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "active_since": self.active_since.isoformat() if isinstance(self.active_since, datetime) else self.active_since,
            "owner_id": self.owner_id,
            "group_active": self.group_active,
        }