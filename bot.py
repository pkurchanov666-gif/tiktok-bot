async def background_generate(context, user_id):

    await context.bot.send_message(chat_id=user_id, text="🚀 Я начал генерацию")

    try:
        paths, specs = await generate_all_photos()

        await context.bot.send_message(chat_id=user_id, text="📦 generate_all_photos завершилась")

        await context.bot.send_message(chat_id=user_id, text=f"Paths: {paths}")

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ Ошибка: {e}")
