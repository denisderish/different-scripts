import os
import re
import datetime
from datetime import datetime, timedelta
import csv
import time

# Скрипт составляет список txt-файлов, которые хранятся на диске в определенных папках.

#ПАРАМЕТРЫ
##############
#путь сохранения отчета
pathSaveDir = os.getcwd()
pathSaveFile = os.path.join(pathSaveDir, 'report.csv')

#имя диска, на котором хранятся папки ('bron_tlf','delete','dolg','mask','service')
root_dir = 'P:\\'

#имя папок
list_dir = ('bron_tlf','delete','dolg','mask','service')

#количество дней, за которые нужен отчет, включая текущий день
report_days = 2

#код города
phone_code_city = 342

#количество знаков в телефонном номере после кода города
amount_char_phone = 7

#имя действий из имен файлов, которые нам нужны
list_action = ('delete', 'install', 'install_day', 'service', 'dolg_ON', 'dolg_OFF', 'bron_ON', 'bron_OFF', 'mask_ON',
                 'mask_OFF')
##############

def listDictFinal():

# Разделение имени файла на действие и дату его формирования в биллинге
    def fileNameDate(file):
        find = re.search(r'(\w+)_\w+_(\d+)\.', file)  # разделяет имя файла на действие и дату его создания
        action = find.groups()[0]  # действие
        timeCreateFileBilling = datetime.strptime(find.groups()[1], "%d%m%y%H%M")  # дата создания
        return action, timeCreateFileBilling

# Составление словаря о каждом файле
    def dictFinal(filename, dir):
        path = os.path.join(root_dir, dir, filename)
        action, timeBilling = fileNameDate(filename)
        timeLastModFileOS = datetime.fromtimestamp(int(os.path.getmtime(path)))
        dict = {'Путь к файлу': path, 'Действие': action, 'ДатаВремяМодификацииФайла': timeLastModFileOS,
                'ДатаВремяВыгрузкиБиллинг': timeBilling}
        return dict

# формирование списка файлов
    listDict = []
    for dir in list_dir:
        path = os.path.join(root_dir, dir)
        if os.access(path, os.R_OK):
            listDict += (list(map(lambda filename: dictFinal(filename, dir), os.listdir(path))))  # тут начало
        else:
            print('Неправильный путь или нет доступа на чтение: ' + str(path))
    if bool(listDict):
        listDict.sort(key=lambda x: x['ДатаВремяМодификацииФайла'], reverse=True)
    else:
        print('Не удалось составить список файлов.')
        exit()
    return listDict

# фильтр для вывода и чтения файлов за последние 2 дня (текущий и предыдущий день)
def timeFilter(listdictfinal):
    listDictFiltered = []
    for record in listdictfinal:
        if ((record['Действие'] in list_action) and
                (record['ДатаВремяМодификацииФайла'].date() > (datetime.now().date() - timedelta(days=report_days)))):
            listDictFiltered.append(record)
            listDictFiltered += (readFile(record['Путь к файлу'],record['Действие']))
        else:
            continue
    return listDictFiltered

# чтение файла построчно и формирование команды для softswitch
def readFile(pathFile, action):

    list_action = {'delete': 'SET OWSBR: SD=K\'{nomer},LP=0, SETMODE=Manl, OS=IOOF;',
                   'install': 'SET OWSBR: SD=K\'{nomer}, LP=0, SETMODE=Manl, OS=NRM;',
                   'install_day': 'SET OWSBR: SD=K\'{nomer}, LP=0, SETMODE=Manl, OS=NRM;',
                   'dolg_ON': 'SET OWSBR: SD=K\'{nomer}, LP=0, SETMODE=Manl, OS=NRM;',
                   'dolg_OFF': 'SET OWSBR: SD=K\'{nomer},LP=0, SETMODE=Manl, OS=IOOF;',
                   'bron_ON': 'PRK SBR: D=K\'{nomer}, LP=0;',
                   'bron_OFF': 'RES SBR: D=K\'{nomer}, LP=0;',
                   'mask_ON': 'MOD MSBR: D=K\'{nomer}, LP=0, TEN=EID, OCR=LCO-1&LC-1&LCT-1&NTT-1&ITT-1&ICTX-'
                                   '1&OCTX-1&INTT-1&IITT-1&ICLT-1&ICDDD-1&ICIDD-1&IOLT-1&CCO1-1&CCO2-1&CCO3-1&CCO4-'
                                   '1&CCO5-1&CCO6-1&CCO7-1&CCO8-1&CCO9-1&CCO10-1&CCO11-1&CCO12-1&CCO13-1&CCO14-'
                                   '1&CCO15-1&CCO16-1;',
                   'mask_OFF': 'MOD MSBR: D=K\'{nomer}, LP=0, TEN=EID, OCR=CCO3-0&CCO4-0&CCO5-0&CCO6-0&CCO7-'
                                    '0&CCO8-0&CCO9-0&CCO10-0&CCO11-0&CCO12-0&CCO13-0&CCO14-0&CCO15-0&CCO16-0;',
                    'LST MSBR': 'LST MSBR: D=K\'{nomer}, LP=0, TEN=EID, SRF=YES;'}

    list_action_service = {
        'ВЫКЛЮЧИТЬ ВЫХОД НА АМТС(8) ТЕЛЕФОН': 'MOD MSBR: D=K\'{nomer}, LP=0, TEN=EID, OCR=CCO3-0&CCO4-0&CCO5-0&CCO6-0&CCO7-'
                                              '0&CCO8-0&CCO9-0&CCO10-0&CCO11-0&CCO12-0&CCO13-0&CCO14-0&CCO15-0&CCO16-0;',
        'ВКЛЮЧИТЬ ВЫХОД НА АМТС(8) ТЕЛЕФОН': 'MOD MSBR: D=K\'{nomer}, LP=0, TEN=EID, OCR=LCO-1&LC-1&LCT-1&NTT-1&ITT-1&ICTX-'
                                             '1&OCTX-1&INTT-1&IITT-1&ICLT-1&ICDDD-1&ICIDD-1&IOLT-1&CCO1-1&CCO2-1&CCO3-1&CCO4-'
                                             '1&CCO5-1&CCO6-1&CCO7-1&CCO8-1&CCO9-1&CCO10-1&CCO11-1&CCO12-1&CCO13-1&CCO14-'
                                             '1&CCO15-1&CCO16-1;',
        'ОТКЛЮЧЕНИЕ ПО ИНИЦИАТИВЕ ПРЕДП-Я ТЕЛЕФОН': 'SET OWSBR: SD=K\'{nomer},LP=0, SETMODE=Manl, OS=IOOF;',
        'ВКЛЮЧЕНИЕ ПОСЛЕ ОТКЛ ПО ИНИЦ ТЕЛЕФОН': 'SET OWSBR: SD=K\'{nomer}, LP=0, SETMODE=Manl, OS=NRM;',
        'ВКЛ АОН ТЕЛЕФОН': 'MOD MSBR: D=K\'{nomer}, LP=0, TEN=EID, NS=CLIP-1;',
        'ВКЛ БЕЗУСЛОВНАЯ ПЕРЕАДРЕСАЦИЯ ТЕЛЕФОН': 'MOD MSBR: D=K\'{nomer}, LP=0, TEN=EID, NS=CFU-1;'}

    listResult = []

    if os.access(pathFile, os.R_OK):
        content = open(pathFile, 'r', encoding='cp1251')
        for line in content:
            result = {}
            result['Путь к файлу'] = line.replace('\n', '')  # строку из файла заносим в столбец 'Путь к файлу'
            reg_exp_phone = r'^%s(\d{%s})' % (phone_code_city, amount_char_phone)
            telephone = re.search(reg_exp_phone, line)  # выполняется поиск 7-значного номера телефона(без phone_code_city), начинающегося с phone_code_city

            if telephone != None:
                # частный случай для действия service, сами действия хранятся в файле
                if action == 'service':
                    reg_exp_text = r'^%s\d{%s}\s([а-яА-Я\W+\d+]+)\n' % (phone_code_city, amount_char_phone)
                    line_text_action = re.search(reg_exp_text, line)
                    if line_text_action.groups()[0] in list_action_service:
                        result['Команда'] = list_action_service[line_text_action.groups()[0]].format(nomer=telephone.groups()[0])
                    else:
                        result['Команда'] = 'КОМАНДА НЕ ОПРЕДЕЛЕНА'
                else:
                    result['Команда'] = list_action[action].format(nomer=telephone.groups()[0])
                result['Просмотр номера'] = list_action['LST MSBR'].format(nomer=telephone.groups()[0])
            else:
                result['Команда'] = 'НОМЕР ТЕЛЕФОНА НЕ ОПРЕДЕЛЕН'
            listResult.append(result)

        content.close()

    else:
        print('Неправильный путь или нет доступа на чтение: ' + str(pathFile))

    return listResult

# Вывод готового списка словарей в файл формата csv
def printFile(listDict):
    try:
        with open(pathSaveFile, mode='w', encoding='cp1251') as csvFile:
            print('Файл будет сохранен по пути: ' + pathSaveFile)
            csvFile.write('Время генерации отчета: %s;\n' % (datetime.now().strftime('%d-%m-%Y %H:%M:%S')))
            columnsName = ['Путь к файлу', 'Действие', 'ДатаВремяМодификацииФайла', 'ДатаВремяВыгрузкиБиллинг', 'Команда', 'Просмотр номера']
            csvReport = csv.DictWriter(csvFile, delimiter=';', lineterminator='\r', fieldnames=columnsName)
            csvReport.writeheader()
            csvReport.writerows(x for x in listDict)
            print('Отчет сформирован!')
    except PermissionError as e:
        print(e.strerror, pathSaveFile)
        exit()

def main():

    os.system('del %TEMP%\\report_telephone.csv')

    script_start = time.time()

    if os.path.exists(pathSaveFile):
        try:
            os.remove(pathSaveFile)
        except PermissionError as e:
            print('%s : %s\\n' % (e.strerror, pathSaveFile))
            print('Закройте файл ' + str(pathSaveFile) + ' и запустите скрипт заново.')
            exit()
        printFile(timeFilter(listDictFinal()))
    else:
        printFile(timeFilter(listDictFinal()))

    script_finish = time.time()

    print(f'Well done sir, script consumed {script_finish - script_start:.2f} sec of your life')

    os.system('copy report.csv %TEMP%\\report_telephone.csv')
    os.system('%TEMP%\\report_telephone.csv')
    os.system('TIMEOUT /T 20')

if __name__ == '__main__':
    main()
