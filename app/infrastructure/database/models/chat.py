from tortoise import fields, models


class ChatModel(models.Model):
    id = fields.BigIntField(pk=True)
    user = fields.ForeignKeyField("models.UserModel", related_name="chats")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    last_message_at = fields.DatetimeField(null=True)

    class Meta:
        table = "chats"