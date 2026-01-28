from aiogram import Router

main_router = Router()
try:
    from .start import user_router as start_router

    main_router.include_router(start_router)
except Exception as e:
    print(f'File src/bot/handlers/__init__.py, Error:{e}')