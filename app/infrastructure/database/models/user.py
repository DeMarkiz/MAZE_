from tortoise import models, fields

from app.infrastructure.database.models.subscribe import PlanName


class UserModel(models.Model):
    telegram_id = fields.BigIntField(pk=True, unique=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255, null=True)
    last_name = fields.CharField(max_length=255, null=True)
    subscription_level = fields.CharEnumField(enum_type=PlanName, default=None, null=True, max_length=10)
    is_admin = fields.BooleanField(default=False)
    is_banned = fields.BooleanField(default=False)
    banned_until = fields.DatetimeField(null=True)
    invited_by = fields.ForeignKeyField('models.UserModel', related_name='referrals_from', null=True)
    referrals = fields.JSONField(default=list)
    message_limit = fields.IntField(default=20)
    used_messages = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"
