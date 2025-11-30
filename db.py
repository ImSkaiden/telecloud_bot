from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator

class User(models.Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    user_token = fields.CharField(max_length=255, unique=True, null=True)

    def __str__(self):
        return f"User {self.telegram_id}"

