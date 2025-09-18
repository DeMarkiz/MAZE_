from tortoise import fields, models


class MessageModel(models.Model):
    id = fields.IntField(pk=True)
    chat = fields.ForeignKeyField("models.ChatModel", related_name="messages")
    content = fields.TextField()
    is_from_user = fields.BooleanField()
    created_at = fields.DatetimeField(auto_now_add=True)
    context_summary = fields.TextField(null=True)
    emotion = fields.CharField(max_length=50, null=True)
    topic = fields.CharField(max_length=100, null=True)
    importance = fields.IntField(default=1)
    out_of_scope = fields.BooleanField(default=False)

    class Meta:
        table = "messages"
