from dataclasses import dataclass

@dataclass
class SubscriptionPlan:
    name: str
    description: str
    price_usd: float
    duration_days: int
    is_active: bool