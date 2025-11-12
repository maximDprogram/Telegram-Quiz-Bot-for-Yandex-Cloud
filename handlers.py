import os
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from service import get_question, new_quiz, get_quiz_index, update_quiz_state, get_quiz_length, get_question_data, get_score

router = Router()

@router.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    await callback.message.answer("Верно!")
    current_question_index = await get_quiz_index(callback.from_user.id)
    current_score = await get_score(callback.from_user.id)
    current_score += 1
    current_question_index += 1
    await update_quiz_state(callback.from_user.id, current_question_index, current_score)
    quiz_length = await get_quiz_length()
    if current_question_index < quiz_length:
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Вы набрали {current_score} из {quiz_length}")

@router.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    current_question_index = await get_quiz_index(callback.from_user.id)
    question_data = await get_question_data(current_question_index)
    correct_option = question_data['correct_option']
    await callback.message.answer(f"Неправильно. Правильный ответ: {question_data['options'][correct_option]}")
    current_score = await get_score(callback.from_user.id)
    current_question_index += 1
    await update_quiz_state(callback.from_user.id, current_question_index, current_score)
    quiz_length = await get_quiz_length()
    if current_question_index < quiz_length:
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Вы набрали {current_score} из {quiz_length}")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(F.text=="Начать игру")
@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    image_url = os.getenv("image_url")
    await message.answer_photo(photo=image_url)
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)