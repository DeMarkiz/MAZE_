import enum

from tortoise import models, fields


class PlanName(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    VIP = "vip"


class SubscriptionPlanModel(models.Model):
    name = fields.CharEnumField(PlanName, max_length=10, unique=True)
    description = fields.TextField(null=True)
    price_usd = fields.DecimalField(max_digits=10, decimal_places=2)
    duration_days = fields.IntField(default=30)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "subscription_plans"


class SubscriptionModel(models.Model):
    user = fields.ForeignKeyField("models.UserModel", related_name="subscriptions")
    plan = fields.ForeignKeyField("models.SubscriptionPlanModel", related_name="subscriptions")
    start_date = fields.DatetimeField(auto_now_add=True)
    end_date = fields.DatetimeField()
    is_active = fields.BooleanField(default=True)
    payment_id = fields.CharField(max_length=255, null=True, description="ID транзакции в платежной системе")
    payment_amount = fields.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        table = "subscriptions"
