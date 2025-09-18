import logging
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from app.application.use_cases.subscriptions import \
    activate_subscription_for_user
from app.config import settings
from app.infrastructure.database.models.payment import PaymentModel, PaymentStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/yoomoney")
async def yoomoney_webhook(request: Request):
    """Handle YooKassa payment notifications"""
    try:
        # Получаем данные как JSON (правильный формат для YooKassa)
        try:
            webhook_data = await request.json()
        except Exception as json_error:
            logger.error(f"Failed to parse JSON: {json_error}")
            # Попробуем получить raw данные
            raw_data = await request.body()
            logger.error(f"Raw request body: {raw_data}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        # Логируем все полученные данные для отладки
        logger.info(f"YooKassa webhook received: {webhook_data}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request URL: {request.url}")
        
        # Проверяем структуру данных
        if not webhook_data:
            logger.warning("Empty webhook data received")
            return {"status": "ok", "message": "Empty data acknowledged"}
            
        if not isinstance(webhook_data, dict):
            logger.error("Invalid webhook data format - expected JSON object")
            raise HTTPException(status_code=400, detail="Invalid data format")
        
        # Получаем данные платежа
        payment_data = webhook_data.get('object', {})
        event_type = webhook_data.get('event')
        
        logger.info(f"Event type: {event_type}, Payment data: {payment_data}")
        
        # Обрабатываем только успешные платежи
        if event_type == 'payment.succeeded':
            payment_id = payment_data.get('id')
            status = payment_data.get('status')
            amount_data = payment_data.get('amount', {})
            metadata = payment_data.get('metadata', {})
            
            logger.info(f"Processing successful payment: {payment_id}, status: {status}")
            
            if payment_id and status == 'succeeded':
                # Получаем наш payment_id из metadata
                our_payment_id = metadata.get('label')
                amount = float(amount_data.get('value', 0))
                currency = amount_data.get('currency', 'RUB')
                
                logger.info(f"Our payment ID: {our_payment_id}, amount: {amount} {currency}")
                
                if our_payment_id:
                    await process_successful_payment(our_payment_id, amount, payment_id, metadata)
                    logger.info(f"Payment processed successfully: {our_payment_id}")
                    return {"status": "ok", "message": "Payment processed"}
                else:
                    logger.warning(f"No label found in metadata for payment {payment_id}")
                    return {"status": "ok", "message": "No label found"}
        
        elif event_type == 'payment.canceled':
            payment_id = payment_data.get('id')
            logger.info(f"Payment canceled: {payment_id}")
            return {"status": "ok", "message": "Payment canceled acknowledged"}
        
        else:
            logger.info(f"Unhandled event type: {event_type}")
            return {"status": "ok", "message": "Event acknowledged"}
        
    except Exception as e:
        logger.error(f"Error processing YooKassa webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_successful_payment(payment_id: str, amount: float, yookassa_payment_id: str, metadata: dict):
    """Process successful payment and update subscription"""
    try:
        # Ищем платеж в базе данных
        payment = await PaymentModel.get_by_payment_id(payment_id)
        
        if not payment:
            logger.error(f"Payment not found: {payment_id}")
            return
        
        if payment.payment_status == PaymentStatus.SUCCEEDED:
            logger.info(f"Payment already processed: {payment_id}")
            return
        
        # Обновляем статус платежа
        await payment.mark_as_paid({
            "webhook_data": {
                "yookassa_payment_id": yookassa_payment_id,
                "amount": amount,
                "metadata": metadata,
                "processed_at": datetime.now().isoformat()
            }
        })
        
        logger.info(f"Payment {payment_id} marked as paid")
        
        # Активируем подписку
        await activate_subscription_for_user(
            user_id=payment.user_id,
            plan_id=payment.plan_id,
            payment_id=payment_id,
            payment_amount=Decimal(str(amount)).quantize(Decimal("0.01")),
        )
        
        logger.info(f"Subscription activated for user {payment.user_id}, plan {payment.plan_id}")
        
    except Exception as e:
        logger.error(f"Error processing successful payment: {e}")
        raise

