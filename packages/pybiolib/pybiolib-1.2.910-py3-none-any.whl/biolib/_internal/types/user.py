from .account import AccountDict
from .typing import Optional, TypedDict


class EnterpriseSettingsDict(TypedDict):
    dashboard_message: Optional[str]
    docs_message: Optional[str]
    featured_dashboard_app_version_uuid: Optional[str]


class UserDict(TypedDict):
    uuid: str
    email: str
    enterprise_settings: Optional[EnterpriseSettingsDict]
    intrinsic_account: AccountDict


class UserDetailedDict(TypedDict):
    pass
