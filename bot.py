from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import uuid
import difflib

conn = sqlite3.connect('streets.db')
cur = conn.cursor()

logging.basicConfig(level=logging.INFO)
bot = Bot(token='')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Класс состояний FSM
class RegistrationStates(StatesGroup):
    STATE_CITY = State()    # Состояние для ввода города
    STATE_STREET = State()  # Состояние для ввода улицы
    STATE_NUMBER = State()  # Состояние для ввода улицы
    STATE_DONE = State()    # Завершающее состояние


def create_results_from_chunk(chunk):
    # Создает результаты для каждой части данных
    results = []
    for data in chunk:
        results.append(
            types.InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=data,
                input_message_content=types.InputTextMessageContent(
                    message_text=data)
            )
        )
    return results


def sort_by_similarity(lst, query):
    # Создаем функцию, которая будет извлекать ключ сортировки из элементов списка
    def similarity_key(elem):
        # Вычисляем схожесть между элементом списка и вводной строкой
        matcher = difflib.SequenceMatcher(None, elem, query)
        return matcher.ratio()

    # Сортируем список по схожести элементов и вводной строки
    sorted_lst = sorted(lst, key=similarity_key, reverse=True)
    return sorted_lst


@dp.inline_handler(state='*')
async def inline_handler(query: types.InlineQuery):
    data = streets_check  # Функция, которая возвращает список всех элементов
    data = sort_by_similarity(data, query.query)
    offset = int(query.offset) if query.offset else 0
    limit = 50  # Количество элементов, которые нужно вернуть за один запрос
    results = []
    while offset < len(data):
        chunk = data[offset:offset + limit]
        results += create_results_from_chunk(chunk)
        offset += limit
        if len(results) >= 50:
            break
    next_offset = str(offset) if offset < len(
        data) else ''  # Устанавливаем next_offset
    await bot.answer_inline_query(query.id, results, next_offset=next_offset)


@dp.message_handler(commands=['start', 'again', 'Вернуться'], state='*', )
async def start_handler(message: types.Message):
    global big_message, current_page
    big_message = ''
    current_page = 1
    big_message = None
    global cities_kb, streets_kb, numbers_kb
    cities_kb, streets_kb, numbers_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1), ReplyKeyboardMarkup(
        resize_keyboard=True, row_width=10), ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    cities_kb.add(KeyboardButton('/Вернуться'))
    streets_kb.add(KeyboardButton('/Вернуться'))
    numbers_kb.add(KeyboardButton('/Вернуться'))
    global cities_check, streets_check, numbers_check
    cities_check, streets_check, numbers_check = [], [], []
    available_cities = cur.execute("SELECT DISTINCT city FROM streets")
    for i in available_cities.fetchall():
        btn = KeyboardButton(i[0])
        cities_kb.add(btn)
        cities_check.append(i[0])

    await RegistrationStates.STATE_CITY.set()
    await message.delete()
    global welcome_msg
    welcome_msg = await message.answer("🔎 DEPUTEYE - бот позволяющий вам узнать депутата который ответственнен на вашей улице.\n🇰🇿Выбери город", reply_markup=cities_kb)

# Функция-обработчик второго состояния FSM (STATE_STREET)


@dp.message_handler(state=RegistrationStates.STATE_CITY)
async def city_handler(message: types.Message, state: FSMContext):
    global city
    city = message.text
    if city in cities_check:
        global streets_check
        pagination_cb = CallbackData('pagination', 'page')

        async def send_large_message(message: types.Message):
            # Создаем объект InlineKeyboardMarkup с двумя кнопками пагинации

            pagination_keyboard = InlineKeyboardMarkup(row_width=2)
            pagination_keyboard.add(InlineKeyboardButton(
                ">>", callback_data=pagination_cb.new(page="next")))
            # Создаем большое сообщение
            all_streets = cur.execute(
                f"SELECT DISTINCT name FROM streets WHERE city='{city}'")

            streets_msg = 'СПРАВОЧНИК\n'
            a = 0
            message_parts, streets_names = [], []
            for i in all_streets.fetchall():
                streets_names.append(i[0].lower())
            streets_names.sort()
            for i in streets_names:
                a += 1
                streets_msg += f"<code>{i}</code>\n"
                streets_check.append(i.lower())
                if a == 20:
                    a = 0
                    message_parts.append(streets_msg)
                    streets_msg = "СПРАВОЧНИК\n"
            global search_results
            search_results = []
            total_pages = len(message_parts)
            current_page = 1
            global big_message
            # Отправляем первую страницу сообщения с клавиатурой пагинации
            # big_message = await bot.send_message(message.from_id, message_parts[0], parse_mode="HTML", reply_markup=pagination_keyboard)

            async def edit_message_page(page: int, kb):
                # Обновляем текст сообщения на указанной странице
                global big_message
                big_message = await bot.edit_message_text(message_parts[page-1], message.from_id, big_message.message_id, parse_mode="HTML", reply_markup=kb)

            async def on_pagination_callback(callback_query):
                nonlocal current_page

                # Обрабатываем нажатие на кнопку пагинации
                data = callback_query.data
                if data == pagination_cb.new(page="prev"):
                    if current_page > 1:
                        current_page -= 1
                        pagination_keyboard = InlineKeyboardMarkup(row_width=2)
                        pagination_keyboard.add(InlineKeyboardButton("<<", callback_data=pagination_cb.new(page="prev")),
                                                InlineKeyboardButton(">>", callback_data=pagination_cb.new(page="next")))
                elif data == pagination_cb.new(page="next"):
                    if current_page < total_pages:
                        pagination_keyboard = InlineKeyboardMarkup(row_width=2)
                        pagination_keyboard.add(InlineKeyboardButton("<<", callback_data=pagination_cb.new(page="prev")),
                                                InlineKeyboardButton(">>", callback_data=pagination_cb.new(page="next")))
                        current_page += 1

                if current_page == total_pages:
                    pagination_keyboard = InlineKeyboardMarkup(row_width=2)
                    pagination_keyboard.add(InlineKeyboardButton(
                        "<<", callback_data=pagination_cb.new(page="prev")))
                if current_page == 1:
                    pagination_keyboard = InlineKeyboardMarkup(row_width=2)
                    pagination_keyboard.add(InlineKeyboardButton(
                        ">>", callback_data=pagination_cb.new(page="next")))
                # Обновляем текст сообщения и клавиатуру
                await edit_message_page(current_page, kb=pagination_keyboard)
                await callback_query.answer()

            # Регистрируем обработчик нажатий на кнопки пагинации
            dp.register_callback_query_handler(
                on_pagination_callback, pagination_cb.filter(), state='*')
        await send_large_message(message)
        # Сохраняем город в FSM и переходим в следующее состояние (STATE_STREET)
        await state.update_data(city=city)
        await RegistrationStates.STATE_STREET.set()
        with open('path/to/your/gif/file.gif', 'rb') as gif:
            await bot.send_animation(chat_id=message.chat.id, animation=gif)
        choose_street_msg = await message.answer(f'🏘 Выберите улицу.\nДопустим вы живёте по адресу Хименко напишите боту "улица Хименко" только потом бот предложит вам выбрать номер дома.\nНапишите <code>@deputeye_bot</code> в строку ввода сообщения и он поможет вам найти улицу.', parse_mode="HTML", reply_markup=streets_kb)
    else:
        cities_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                cities_kb,
            ],
            resize_keyboard=False,
        )
        await message.answer("❌ Этот город не доступен, либо написан с опечаткой. Используй кнопки.", reply_markup=cities_kb)


@dp.message_handler(state=RegistrationStates.STATE_STREET)
async def street_handler(message: types.Message, state: FSMContext):
    street = message.text
    data = await state.get_data()
    city = data.get("city")
    # await message.answer(streets_check[:50])
    if street.lower() in streets_check:

        street_numbers = cur.execute(
            f"SELECT numbers FROM streets WHERE city='{city}' AND name='{street.lower()}'")
        all_numbers_string = ''
        for i in street_numbers.fetchall():
            all_numbers_string += i[0]+','

        numbers = all_numbers_string.split(',')
        a = 0
        for i in numbers:
            btn = KeyboardButton(i)
            numbers_kb.add(btn)
            numbers_check.append(i)
            a += 1
        if a == 0:
            btn = KeyboardButton('Без номера')
            numbers_kb.add(btn)
        await state.update_data(street=street)
        await RegistrationStates.STATE_NUMBER.set()
        # await big_message.delete()
        global number_nice
        number_nice = await message.answer("✅ Отлично!\n#️⃣ Выбери доступный номер улицы.", reply_markup=numbers_kb)
    else:
        await message.answer("❌ Эта улица не доступна, либо написана с опечаткой.\n❗️ Если вашей улицы нет в списке - выберите соседнюю улицу.", reply_markup=streets_kb)

# Функция-обработчик завершающего состояния FSM (STATE_DONE)


@dp.message_handler(state=RegistrationStates.STATE_NUMBER)
async def street_handler(message: types.Message, state: FSMContext):

    number = message.text
    await state.update_data(number=number)
    if number in numbers_check:
        await state.update_data(number=number)
        await RegistrationStates.STATE_DONE.set()
        some_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                ["/again"],
            ],
            resize_keyboard=False,
        )
        data = await state.get_data()
        street = data.get("street")
        number = data.get("number")
        city = data.get("city")
        await message.answer(f"🔎 Ищем депутата по улице - {street} {number} г.{city}...")
        try:
            deputy = cur.execute(
                f"SELECT * FROM streets WHERE city='{city}' AND name='{street.lower()}' AND numbers LIKE '%{number},%' OR city='{city}' AND name='{street.lower()}' AND numbers LIKE '%{number}%'").fetchone()

            await message.answer(f"{street} {number} города {city}\n\n🇰🇿 Депутат - {deputy[4]}\n\nИзбирательный округ №{deputy[3]}\n\nИзбирательные участки: {deputy[5]}.", reply_markup=some_keyboard)
            await state.reset_state()

        except:
            await message.answer(f"❌ К сожалению произошла ошибка при поиске - скоро все починим!", reply_markup=some_keyboard)
            await state.reset_state()
    elif number == 'Без номера':
        await state.update_data(number=number)
        await RegistrationStates.STATE_DONE.set()
        some_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                ["/again"],
            ],
            resize_keyboard=False,
        )
        data = await state.get_data()
        street = data.get("street")
        number = data.get("number")
        city = data.get("city")
        await message.answer(f"🔎 Ищем депутата по улице - {street} {number} г.{city}...")
        try:
            deputy = cur.execute(
                f"SELECT * FROM streets WHERE city='{city}' AND name='{street}'").fetchone()

            await message.answer(f"{street} {number} города {city}\n\n🇰🇿 Депутат - {deputy[4]}\n\nИзбирательный округ №{deputy[3]}\n\nИзбирательные участки: {deputy[5]}.", reply_markup=some_keyboard)
            await state.reset_state()

        except:
            await message.answer(f"❌ К сожалению произошла ошибка при поиске - скоро все починим!", reply_markup=some_keyboard)
            await state.reset_state()

    else:
        numbers_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                numbers_kb,
            ],
            resize_keyboard=False,
        )

        data = await state.get_data()
        street = data.get("street")
        number = data.get("number")
        await message.answer(f"Извини, но улица {street} с номером {number} не найдена в базе данных, скорее всего номер написан с опечаткой. Используй кнопки!", reply_markup=numbers_kb)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
