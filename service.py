from database import pool, execute_update_query, execute_select_query, get_question_data
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer"
        ))
    builder.adjust(1)
    return builder.as_markup()

async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)
    question_data = await get_question_data(current_question_index)
    correct_index = question_data['correct_option']
    opts = question_data['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{question_data['question']}", reply_markup=kb)

async def new_quiz(message):
    user_id = message.from_user.id
    await update_quiz_state(user_id, 0, 0)
    await get_question(message, user_id)

async def get_quiz_index(user_id):
    state = await get_quiz_state(user_id)
    return state['question_index']

async def get_score(user_id):
    state = await get_quiz_state(user_id)
    return state['score']

async def get_quiz_state(user_id):
    get_user_state = """
    DECLARE $user_id AS Uint64;
    SELECT question_index, score FROM quiz_state WHERE user_id == $user_id;
    """
    results = execute_select_query(pool, get_user_state, user_id=user_id)
    if len(results) == 0:
        return {'question_index': 0, 'score': 0}
    if results[0]["question_index"] is None:
        return {'question_index': 0, 'score': 0}
    return {'question_index': results[0]["question_index"], 'score': results[0]["score"] or 0}

async def update_quiz_state(user_id, question_index, score):
    set_quiz_state = """
    DECLARE $user_id AS Uint64;
    DECLARE $question_index AS Uint64;
    DECLARE $score AS Uint64;
    UPSERT INTO quiz_state (user_id, question_index, score) VALUES ($user_id, $question_index, $score);
    """
    execute_update_query(
        pool, set_quiz_state, user_id=user_id, question_index=question_index, score=score
    )

async def get_quiz_length():
    query = "SELECT COUNT(*) AS count FROM quiz_questions;"
    results = execute_select_query(pool, query)
    return results[0]['count']