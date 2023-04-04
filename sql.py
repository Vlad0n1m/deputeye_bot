import sqlite3

conn = sqlite3.connect('streets.db')
cur = conn.cursor()

available_cities = cur.execute("SELECT DISTINCT city FROM streets")
cities = ''
for i in available_cities.fetchall():
    cities+=i[0]+', '
    # передать все города в кнопки
print(f'Доступные города: {cities}')
user_city = str(input('Введите ваш город - '))

all_streets = cur.execute(f"SELECT DISTINCT name FROM streets WHERE city='{user_city}'")
print('Доступные улицы:')
all_streets_string = ''
# print(all_streets.fetchall())
for i in all_streets.fetchall():
    all_streets_string += i[0]+', '
print(all_streets_string)
name_of_street = str(input('Введите название вашей улицы - '))
street_numbers = cur.execute(f"SELECT numbers FROM streets WHERE city='{user_city}' AND name='{name_of_street}'")
# street_numbers = cur.execute(f"SELECT numbers FROM streets WHERE city='Петропавловск' AND name='улица Хименко'")
all_numbers_string = ''
# print(street_numbers.fetchall())
for i in street_numbers.fetchall():
    all_numbers_string += i[0]+','
available_numbers = all_numbers_string.split(',') # передать в кнопки
# print(available_numbers)
user_street_number = str(input(f'Доступные номера для улицы {name_of_street}:\n{all_numbers_string}'))
deputy = cur.execute(f"SELECT * FROM streets WHERE city='{user_city}' AND name='{name_of_street}' AND numbers LIKE '%{user_street_number},%' OR city='{user_city}' AND name='{name_of_street}' AND numbers LIKE '%{user_street_number}%'").fetchone()
print(deputy)