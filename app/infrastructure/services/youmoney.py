import asyncio
import logging
from decimal import Decimal
from typing import Optional, Tuple
from datetime import datetime, timedelta

from yookassa import Configuration, Payment
from yookassa.domain.exceptions import ApiError, BadRequestError

from app.config import settings
from app.infrastructure.database.models.payment import PaymentModel, PaymentProvider, PaymentStatus
from app.infrastructure.database.models.subscribe import SubscriptionPlanModel
from app.infrastructure.logging.setup_logger import logger


class YouMoneyAPIService:
    """Сервис для работы с YouMoney API"""
    
    def __init__(self):
        # Настройка YouMoney API
        shop_id = str(settings.yoomoney_shop_id).strip()
        secret_key = str(settings.yoomoney_secret_key).strip()
        
        # Логируем для отладки (маскируем секретный ключ)
        masked_secret = secret_key[:8] + "..." + secret_key[-4:] if len(secret_key) > 12 else "***"
        logger.info(f"YouMoney config - Shop ID: {shop_id}, Secret Key: {masked_secret}")
        
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        
        # Валидация настроек
        if not Configuration.account_id or not Configuration.secret_key:
            raise ValueError("YouMoney credentials not configured")
    
    async def create_payment(
        self, 
        plan_id: int, 
        user_id: int,
        return_url: str = None
    ) -> Tuple[str, str, Decimal]:
        """
        Создает платеж в YouMoney
        
        Args:
            plan_id: ID плана подписки
            user_id: ID пользователя
            return_url: URL для возврата после оплаты
            
        Returns:
            Tuple[payment_id, payment_url, amount_rub]
        """
        try:
            # Получаем план подписки
            plan = await SubscriptionPlanModel.get(id=plan_id)
            if not plan:
                raise ValueError(f"Plan with ID {plan_id} not found")
            
            # Цена уже в рублях
            amount_rub = plan.price_usd
            
            # Создаем уникальный label для webhook
            label = f"sub_{user_id}_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Создаем платеж в YouMoney
            payment_data = {
                "amount": {
                    "value": str(amount_rub),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or f"https://t.me/MAZEAI_NovaBot"
                },
                "capture": True,
                "description": f"Подписка {plan.name.upper()} для пользователя {user_id}",
                "metadata": {
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "plan_name": plan.name,
                    "label": label  # Добавляем label в metadata
                },
                "receipt": {
                    "customer": {
                        "email": f"user_{user_id}@bot.local"
                    },
                    "items": [
                        {
                            "description": f"Подписка {plan.name.upper()} на {plan.duration_days} дней",
                            "quantity": "1",
                            "amount": {
                                "value": str(amount_rub),
                                "currency": "RUB"
                            },
                            "vat_code": 1,
                            "payment_subject": "service",
                            "payment_mode": "full_payment"
                        }
                    ]
                }
            }
            
            payment = Payment.create(payment_data)
            
            # Сохраняем платеж в БД (используем наш label как payment_id)
            await PaymentModel.create_payment(
                user_id=user_id,
                plan_id=plan_id,
                payment_id=label,  # Используем наш label как payment_id
                amount=Decimal(str(amount_rub)),
                provider=PaymentProvider.YOOMONEY,
                description=f"Подписка {plan.name.upper()}"
            )
            
            logger.info(f"Created YouMoney payment {label} for user {user_id}, plan {plan.name}")
            return label, payment.confirmation.confirmation_url, Decimal(str(amount_rub))
            
        except (ApiError, BadRequestError) as e:
            logger.error(f"YouMoney API error: {e}")
            raise ValueError(f"Payment creation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating payment: {e}")
            raise
    
    async def check_payment_status(self, payment_id: str) -> Optional[PaymentStatus]:
        """
        Проверяет статус платежа в YouMoney
        
        Args:
            payment_id: ID платежа в YouMoney
            
        Returns:
            PaymentStatus или None если платеж не найден
        """
        try:
            payment = Payment.find_one(payment_id)
            
            # Обновляем статус в БД
            db_payment = await PaymentModel.get_by_payment_id(payment_id)
            if db_payment:
                if payment.status == "succeeded" and db_payment.payment_status != PaymentStatus.SUCCEEDED:
                    await db_payment.mark_as_paid({"yoomoney_status": payment.status})
                elif payment.status == "canceled" and db_payment.payment_status != PaymentStatus.CANCELLED:
                    await db_payment.mark_as_failed("Payment was canceled")
                
                return PaymentStatus(payment.status)
            
            return None
            
        except ApiError as e:
            logger.error(f"YouMoney API error checking payment {payment_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking payment {payment_id}: {e}")
            return None


# Глобальный экземпляр сервиса
youmoney_service = YouMoneyAPIService()


# Обратная совместимость - старые функции
async def create_payment(plan_id: int, user_id: int) -> tuple[str, str, Decimal]:
    """Создает платеж (обратная совместимость)"""
    return await youmoney_service.create_payment(plan_id, user_id)

async def check_payment_status(payment_id: str) -> bool:
    """Проверяет статус платежа (обратная совместимость)"""
    # Ищем платеж в БД по нашему label
    db_payment = await PaymentModel.get_by_payment_id(payment_id)
    if not db_payment:
        return False
    
    # Если платеж уже отмечен как оплаченный, возвращаем True
    if db_payment.payment_status == PaymentStatus.SUCCEEDED:
        return True
    
    # Если нет, проверяем через YooKassa API (если есть yookassa_payment_id)
    if db_payment.webhook_data and 'yookassa_payment_id' in db_payment.webhook_data:
        yookassa_id = db_payment.webhook_data['yookassa_payment_id']
        status = await youmoney_service.check_payment_status(yookassa_id)
        return status == PaymentStatus.SUCCEEDED if status else False
    
    return False
