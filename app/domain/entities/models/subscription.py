from dataclasses import dataclass
from datetime import datetime
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.subscribe import SubscriptionPlanModel


@dataclass
class Subscription:
    user: UserModel
    plan: SubscriptionPlanModel
    start_date: datetime
    end_date: datetime
    is_active: bool
    payment_id: str
    payment_amount: float



