import sqlite3
conn = sqlite3.connect('streets.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS streets(
   city TEXT,
   name TEXT,
   numbers TEXT,
   circle_number TEXT,
   deputy TEXT,
   polling_stations TEXT);
""")
conn.commit()

df = open('Deputes.txt', 'r', encoding="utf-8").readlines()
bigline = ""
for i in df:
    bigline+=i
bigline = bigline.split('по избирательному округу')
deputes = []
for i in range(1,19):
    deputes.append(bigline[i].split('–')[1].lstrip().replace('\n', ''))

lines = open('Data.txt', 'r', encoding="utf8").readlines()
big_line = ''
for line in lines:
    big_line += line

circles_data = big_line.replace('\n', '').split('Избирательный округ №')
circles_data.pop(0)
bd = {}
class Circle:
    def __init__(self, city, number_of_circle, data):
        self.city = city
        self.number_of_circle = number_of_circle
        self.data = data

number = 0
# q = open('test.txt', 'a', encoding="utf8")
streets = []
city = 'Петропавловск'
for circle_data in circles_data:
    number +=1
    circle_data = circle_data.split('Местонахождение окружной избирательной комиссии:')
    data = circle_data[1].split('Границы:')[1].split('Входят избирательные участки: ')
    place, areas, polling_stations = circle_data[1].split('Границы:')[0], data[0], data[1]
    for i in areas.split(';'):
        if i=='':
            continue
        # print(i.split(':'))
        try:
            name, numbers = i.split(':')[0].lstrip(), i.split(':')[1]
            numbers = numbers.replace(' ', '').replace('.', '')
            # streets.append({'name': name, 'numbers':numbers, 'circle_number': number, 'polling_stations': polling_stations, 'depute':deputes[number-1]})
            street_data = (city, name.lower(), numbers, number, deputes[number-1], polling_stations)
            cur.execute("""INSERT INTO streets VALUES(?, ?, ?, ?, ?, ?);""", street_data)
            conn.commit()
        except:
            pass
            
