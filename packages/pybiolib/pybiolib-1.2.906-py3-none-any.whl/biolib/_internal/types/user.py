from .account import AccountDict
from .typing import List, Optional, TypedDict


class EnterpriseSettingsDict(TypedDict):
    dashboard_message: Optional[str]
    docs_message: Optional[str]
    featured_dashboard_app: Optional[str]


class UserDict(TypedDict):
    uuid: str
    email: str
    enterprise_settings: Optional[EnterpriseSettingsDict]
    groups: List[AccountDict]
    intrinsic_account: AccountDict


class UserDetailedDict(TypedDict):
    pass
