import enum
from decimal import Decimal
from datetime import datetime
from tortoise import models, fields
from app.infrastructure.logging.setup_logger import logger


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentProvider(str, enum.Enum):
    YOOMONEY = "yoomoney"
    ADMIN = "admin"


class PaymentModel(models.Model):
    """Модель для хранения информации о платежах"""
    
    # Основные поля
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.UserModel", related_name="payments")
    plan = fields.ForeignKeyField("models.SubscriptionPlanModel", related_name="payments")
    
    # Платежная информация
    payment_id = fields.CharField(max_length=255, unique=True, description="ID транзакции в платежной системе")
    payment_provider = fields.CharEnumField(PaymentProvider, default=PaymentProvider.YOOMONEY)
    payment_status = fields.CharEnumField(PaymentStatus, default=PaymentStatus.PENDING)
    
    # Сумма и валюта
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    currency = fields.CharField(max_length=3, default="RUB")
    
    # Метаданные
    description = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict, description="Дополнительные данные платежа")
    
    # Временные метки
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    paid_at = fields.DatetimeField(null=True)
    
    # Webhook данные
    webhook_received = fields.BooleanField(default=False)
    webhook_data = fields.JSONField(default=dict, description="Данные полученные от webhook")
    
    class Meta:
        table = "payments"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.user.telegram_id} - {self.amount} {self.currency}"
    
    async def mark_as_paid(self, webhook_data: dict = None):
        """Отмечает платеж как оплаченный"""
        self.payment_status = PaymentStatus.SUCCEEDED
        self.paid_at = datetime.now()
        self.webhook_received = True
        if webhook_data:
            self.webhook_data = webhook_data
        await self.save()
        logger.info(f"Payment {self.payment_id} marked as paid")
    
    async def mark_as_failed(self, reason: str = None):
        """Отмечает платеж как неудачный"""
        self.payment_status = PaymentStatus.FAILED
        if reason:
            self.metadata["failure_reason"] = reason
        await self.save()
        logger.warning(f"Payment {self.payment_id} marked as failed: {reason}")
    
    @classmethod
    async def create_payment(
        cls, 
        user_id: int, 
        plan_id: int, 
        payment_id: str, 
        amount: Decimal,
        provider: PaymentProvider = PaymentProvider.YOOMONEY,
        description: str = None
    ) -> "PaymentModel":
        """Создает новый платеж с валидацией"""
        
        # Валидация суммы
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        # Проверяем, не существует ли уже такой платеж
        existing_payment = await cls.filter(payment_id=payment_id).first()
        if existing_payment:
            raise ValueError(f"Payment with ID {payment_id} already exists")
        
        # Создаем платеж
        payment = await cls.create(
            user_id=user_id,
            plan_id=plan_id,
            payment_id=payment_id,
            payment_provider=provider,
            amount=amount,
            description=description
        )
        
        logger.info(f"Created payment {payment_id} for user {user_id}, amount: {amount}")
        return payment
    
    @classmethod
    async def get_by_payment_id(cls, payment_id: str) -> "PaymentModel":
        """Получает платеж по ID"""
        return await cls.filter(payment_id=payment_id).first()
    
    @classmethod
    async def get_user_payments(cls, user_id: int, limit: int = 10) -> list["PaymentModel"]:
        """Получает платежи пользователя"""
        return await cls.filter(user_id=user_id).limit(limit)
    
    @classmethod
    async def get_pending_payments(cls) -> list["PaymentModel"]:
        """Получает все ожидающие платежи"""
        return await cls.filter(payment_status=PaymentStatus.PENDING) 
