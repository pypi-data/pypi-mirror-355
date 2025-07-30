from .account import AccountDict
from .typing import List, Optional, TypedDict


class EnterpriseSettings(TypedDict):
    dashboard_message: Optional[str]
    docs_message: Optional[str]
    featured_dashboard_app: Optional[str]


class User(TypedDict):
    email: str
    enterprise_settings: Optional[EnterpriseSettings]
    groups: List[AccountDict]
    intrinsic_account: AccountDict


class UserDetailed(TypedDict):
    pass
