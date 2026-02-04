import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import aiohttp
import base64
from src.config import _Config

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)


class PaymentManager:
    """Yookassa"""
    SHOP_ID = _Config.YUKASSA_SHOP_ID
    SECRET_KEY = _Config.YUKASSA_SECRET_KEY


    _active_checks: Dict[str, asyncio.Task] = {}


    @staticmethod
    def _get_auth_header() -> str:
        auth_string = f"{PaymentManager.SHOP_ID}:{PaymentManager.SECRET_KEY}"
        return base64.b64encode(auth_string.encode()).decode()

    @classmethod
    async def create_payment(
            cls,
            telegram_id: int,
            amount: float,
            days: int,
            description: str = "Premium подписка"
    ) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "RUB"
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": f"https://t.me/HpKrBot?start=payment_{telegram_id}"
                    },
                    "capture": True,
                    "description": f"{description} на {days} дней",
                    "metadata": {
                        "telegram_id": telegram_id,
                        "days": days,
                        "type": "premium",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }

                headers = {
                    "Authorization": f"Basic {cls._get_auth_header()}",
                    "Idempotence-Key": str(datetime.utcnow().timestamp()),
                    "Content-Type": "application/json"
                }

                async with session.post(
                        "https://api.yookassa.ru/v3/payments",
                        json=data,
                        headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Payment creation failed: {await response.text()}")
                        return None

                    result = await response.json()

                    return {
                        "payment_id": result["id"],
                        "payment_url": result["confirmation"]["confirmation_url"],
                        "status": result["status"],
                        "amount": amount,
                        "days": days,
                        "telegram_id": telegram_id
                    }

        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return None

    @classmethod
    async def check_payment_status(cls, payment_id: str) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Basic {cls._get_auth_header()}"
                }

                async with session.get(
                        f"https://api.yookassa.ru/v3/payments/{payment_id}",
                        headers=headers
                ) as response:
                    if response.status != 200:
                        return None

                    return await response.json()

        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return None

    @classmethod
    async def start_background_check(
            cls,
            payment_id: str,
            telegram_id: int,
            timeout_minutes: int = 5
    ) -> None:
        if payment_id in cls._active_checks:
            cls._active_checks[payment_id].cancel()

        task = asyncio.create_task(
            cls._background_check_worker(payment_id, telegram_id, timeout_minutes)
        )
        cls._active_checks[payment_id] = task

        logger.info(f"Started background check for payment {payment_id}")

    @classmethod
    async def _background_check_worker(
            cls,
            payment_id: str,
            telegram_id: int,
            timeout_minutes: int
    ) -> None:
        end_time = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        check_interval = 10  # секунд

        while datetime.utcnow() < end_time:
            try:
                status_data = await cls.check_payment_status(payment_id)

                if status_data:
                    status = status_data.get("status")

                    if status == "succeeded":
                        await cls._process_successful_payment(status_data, telegram_id)
                        break
                    elif status in ["canceled", "expired"]:
                        logger.info(f"Payment {payment_id} was {status}")
                        break

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error in background check: {e}")
                await asyncio.sleep(check_interval)

        if payment_id in cls._active_checks:
            del cls._active_checks[payment_id]

        logger.info(f"Background check finished for payment {payment_id}")

    @classmethod
    async def _process_successful_payment(
            cls,
            status_data: Dict[str, Any],
            telegram_id: int
    ) -> None:
        try:
            metadata = status_data.get("metadata", {})

            days_str = metadata.get("days", "30")
            days = int(days_str)

            from src.database.CRUDs.subscription import AsyncSubscriptionService

            await AsyncSubscriptionService.create_subscription(
                telegram_id=telegram_id,
                subscription_type="premium",
                days=days
            )

            logger.info(f"Subscription activated for user {telegram_id}, {days} days")

        except Exception as e:
            logger.error(f"Error processing successful payment: {e}")



    @classmethod
    def create_payment_keyboard(cls, payment_url: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оплатить",
                        url=payment_url
                    )
                ]
            ]
        )


    @classmethod
    async def cleanup(cls) -> None:
        for payment_id, task in cls._active_checks.items():
            task.cancel()

        cls._active_checks.clear()
        logger.info("Payment manager cleaned up")