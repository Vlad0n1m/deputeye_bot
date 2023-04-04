df = open('Deputes.txt', 'r', encoding="utf-8").readlines()
bigline = ""
for i in df:
    bigline+=i
bigline = bigline.split('по избирательному округу')
deputes = []
for i in range(1,19):
    deputes.append(bigline[i].split('–')[1].lstrip().replace('\n', ''))
