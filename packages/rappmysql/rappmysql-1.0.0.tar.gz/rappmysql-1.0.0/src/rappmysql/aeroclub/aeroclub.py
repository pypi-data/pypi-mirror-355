import csv
import os
import sys
import re
import numpy as np
from datetime import datetime, timedelta
import dateutil.parser as dparser
import pathlib
import shutil
import traceback
from mysqlquerys import connect
from mysqlquerys import mysql_rm

np.set_printoptions(linewidth=250)


def convert_timedelta(duration):
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return days, hours, minutes, seconds


class AeroclubSQL:
    def __init__(self, ini_file):
        self.ini_file = ini_file
        self.conf = connect.Config(self.ini_file)
        self.dataBase = self.sql_rm.DataBase(self.conf.credentials)
        # self.table_zbor_log = mysql_rm.Table(self.conf.credentials, 'zbor_log')
        self.table_zbor_log = mysql_rm.Table(self.conf.credentials, 'flight_logs')
        self.table_docs = mysql_rm.Table(self.conf.credentials, 'docs')

    @property
    def sql_rm(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        if self.conf.db_type == 'mysql':
            sql_rm = mysql_rm
        return sql_rm

    def csv_table_head_conversion(self, csv_table_head):
        # print('csv_table_head', csv_table_head)
        table_head_conversion = {}
        table_head_conversion['vereinsflieger_csv_1'] = {'Lfz.': 'plane',
                                                         'Datum': 'flight_date',
                                                         'Pilot': 'pilot',
                                                         'Start': 'start',
                                                         'Landung': 'land',
                                                         'Zeit': 'flight_time',
                                                         'Startort': 'place_from',
                                                         'Landeort': 'place_to',
                                                         'Landungen': 'landings'
                                                         }
        table_head_conversion['vereinsflieger_csv_2'] = {'Lfz.': 'plane',
                                                         'Datum': 'flight_date',
                                                         'Pilot': 'pilot',
                                                         'Start': 'start',
                                                         'Landung': 'land',
                                                         'Flugzeit': 'flight_time',
                                                         'Startort': 'place_from',
                                                         'Landeort': 'place_to',
                                                         'Landungen': 'landings'
                                                         }
        table_head_conversion['fly_is_fun_csv'] = {'Inmatr. Avion': 'plane',
                                                   # 'AerodromDecolare': 'place_from',
                                                   'DataDecolare': 'flight_date',
                                                   'Decolare': 'start',
                                                   'Aterizare': 'land',
                                                   'Timp': 'flight_time',
                                                   'AerodromDecolare': 'place_from',
                                                   'AerodromAterizare': 'place_to',
                                                   'Nr. Aterizari': 'landings'
                                                   }
        table_head_conversion['fly_demon_csv'] = {'Aircraft': 'plane',
                                                  'Pilot': 'pilot',
                                                  'Landing Time': 'land',
                                                  'Flight Length': 'flight_time'
                                                  }
        for csv_from, csv_conv_dict in table_head_conversion.items():
            asta_e = True
            for col in list(csv_conv_dict.keys()):
                if col not in csv_table_head:
                    # if csv_from == 'fly_is_fun_csv':
                    #     # print(col)
                    asta_e = False
            if asta_e:
                return csv_from, csv_conv_dict

    def get_csv_provider(self, inpFile):
        tableHead = None
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i, row in enumerate(linereader):
                if i == 0:
                    tableHead = [c.strip('"') for c in row]
                    # print(tableHead, len(tableHead))
        if len(tableHead) > 1:
            csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
        else:
            with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
                linereader = csv.reader(csvfile, delimiter=';', quotechar='"')
                # print('+++', linereader[0])
                for i, row in enumerate(linereader):
                    if i == 0:
                        tableHead = [c.strip('"') for c in row]
                        # print(tableHead, len(tableHead))
            csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
        return csv_from, tabHeadDict

    def import_flydemon_csv(self, inpFile):
        cols = []
        vals = []
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i, row in enumerate(linereader):
                if i == 0:
                    tableHead = [c.strip('"') for c in row]
                    csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
                    continue
                sql_table_head = list(tabHeadDict.keys())
                cols = []
                row_vals = []
                for ir, v in enumerate(row):
                    csvColName = tableHead[ir]
                    if csvColName in sql_table_head:
                        sqlColName = tabHeadDict[csvColName]
                        if sqlColName not in cols:
                            cols.append(sqlColName)
                        if sqlColName == 'flight_date':
                            v = self.table_zbor_log.convertDatumFormat4SQL(v)
                        elif (sqlColName == 'Start') or (sqlColName == 'Landung'):
                            v = self.table_zbor_log.convertTimeFormat4SQL(v)
                        row_vals.append(v)
                    else:
                        if csvColName == 'Log Name':
                            place_from, place_to = v.split('-')
                            if 'place_from' not in cols:
                                cols.append('place_from')
                            if 'place_to' not in cols:
                                cols.append('place_to')
                            row_vals.append(place_from)
                            row_vals.append(place_to)
                        elif csvColName == 'Takeoff Time':
                            v = self.table_zbor_log.convertDateTimeFormat4SQL(v)
                            flight_date = v.date()
                            start = v.time()
                            if 'flight_date' not in cols:
                                cols.append('flight_date')
                            if 'start' not in cols:
                                cols.append('start')
                            row_vals.append(flight_date)
                            row_vals.append(start)
                        else:
                            continue
                vals.append(tuple(row_vals))
        return cols, vals

    def import_fly_is_fun_csv(self, inpFile):
        cols = []
        vals = []
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for i, row in enumerate(linereader):
                if i == 0:
                    tableHead = [c.strip('"') for c in row]
                    csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
                    continue
                sql_table_head = list(tabHeadDict.keys())

                row_vals = []
                for ir, v in enumerate(row):
                    csvColName = tableHead[ir]
                    if csvColName in sql_table_head:
                        sqlColName = tabHeadDict[csvColName]
                        if sqlColName not in cols:
                            cols.append(sqlColName)
                        if sqlColName == 'flight_date':
                            v = self.table_zbor_log.convertDatumFormat4SQL(v)
                        elif (sqlColName == 'start') or (sqlColName == 'land') or (sqlColName == 'flight_time'):
                            v = self.table_zbor_log.convertTimeFormat4SQL(v)
                        row_vals.append(v)
                    else:
                        # print(csvColName)
                        if csvColName == 'Log Name':
                            place_from, place_to = v.split('-')
                            # print(place_from, place_to)
                            if 'place_from' not in cols:
                                cols.append('place_from')
                            if 'place_to' not in cols:
                                cols.append('place_to')
                            row_vals.append(place_from)
                            row_vals.append(place_to)
                        elif csvColName == 'Takeoff Time':
                            v = self.table_zbor_log.convertDateTimeFormat4SQL(v)
                            flight_date = v.date()
                            start = v.time()
                            if 'flight_date' not in cols:
                                cols.append('flight_date')
                            if 'start' not in cols:
                                cols.append('start')
                            row_vals.append(flight_date)
                            row_vals.append(start)
                        else:
                            continue
                row_vals.append(inpFile)
                vals.append(tuple(row_vals))
        cols.append('path_to_log')
        return cols, vals

    def import_vereinsflieger_in_sql(self, inpFile):
        cols = []
        vals = []
        with open(inpFile, 'r', encoding='unicode_escape', newline='') as csvfile:
            linereader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for i, row in enumerate(linereader):
                print(i, row, type(row), len(row))
                if i == 0:
                    tableHead = [c.strip('"') for c in row]
                    csv_from, tabHeadDict = self.csv_table_head_conversion(tableHead)
                    continue
                elif len(row) == 1 and 'Zeitspanne' in row[0]:
                    continue
                sql_table_head = list(tabHeadDict.keys())

                row_vals = []
                for ir, v in enumerate(row):
                    csvColName = tableHead[ir]
                    if csvColName in sql_table_head:
                        sqlColName = tabHeadDict[csvColName]
                        if sqlColName not in cols:
                            cols.append(sqlColName)
                        if sqlColName == 'flight_date':
                            v = self.table_zbor_log.convertDatumFormat4SQL(v)
                        elif (sqlColName == 'Start') or (sqlColName == 'Landung'):
                            v = self.table_zbor_log.convertTimeFormat4SQL(v)
                        elif sqlColName == 'flight_time':
                            v = timedelta(minutes=int(v))
                        row_vals.append(v)
                # row_vals.append(os.path.split(inpFile[1]))
                # print('..-.', inpFile)
                vals.append(tuple(row_vals))
        # cols.append('path_to_log')
        return cols, vals

    def get_price_per_time(self, avion, flight_times):
        take_off, landing = flight_times
        pph = self.table_docs.returnCellWhereValueIsInIntervalAND('pph', 'name', avion, 'valid_from', take_off,
                                                                  'valid_to')
        print('****', pph)
        try:
            pph = float(pph[0][0])
        except:
            return None
        ppm = pph / 60
        flight_time = landing - take_off
        flight_mins = flight_time.seconds / 60
        price = flight_mins * ppm
        return round(price, 2)

    def fill_in_pph(self):
        for zbor in self.table_zbor_log.returnAllRecordsFromTable():
            id = zbor[self.table_zbor_log.columnsNames.index('id')]
            plane = zbor[self.table_zbor_log.columnsNames.index('plane')]
            flight_date = zbor[self.table_zbor_log.columnsNames.index('flight_date')]
            start = zbor[self.table_zbor_log.columnsNames.index('start')]
            land = zbor[self.table_zbor_log.columnsNames.index('land')]
            days, hours, minutes, seconds = convert_timedelta(start)
            start = datetime(flight_date.year, flight_date.month, flight_date.day, hours, minutes, seconds)
            days, hours, minutes, seconds = convert_timedelta(land)
            land = datetime(flight_date.year, flight_date.month, flight_date.day, hours, minutes, seconds)
            price = self.get_price_per_time(plane, (start, land))
            self.table_zbor_log.changeCellContent('price_hour', price, 'id', id)

    def getVideo(self, path):
        foundDirs = []
        dir = os.listdir(path)
        for d in dir:
            pth = os.path.join(path, d)
            if os.path.isdir(pth):
                try:
                    match = re.search(r'\d{4}.\d{2}.\d{2}', d)
                    name = d[match.span()[1]:]
                    date = datetime.strptime(match.group(), '%Y.%m.%d').date()
                    tup = (date, name, pth)
                    foundDirs.append(tup)
                except:
                    try:
                        match = re.search(r'\d{4}-\d{2}-\d{2}', d)
                        name = d[match.span()[1]:]
                        date = datetime.strptime(match.group(), '%Y-%m-%d').date()
                        tup = (date, name, pth)
                        foundDirs.append(tup)
                    except:
                        print('**--**', d)
                        continue

        for row in foundDirs:
            data, name, pth = row

            matches = [('flight_date', data)]
            row_id = self.table_zbor_log.returnCellsWhere('id', matches)
            if not row_id:
                print('*=', data, name, pth)
                continue
            for id in row_id:
                self.table_zbor_log.changeCellContent('name', str(name), 'id', id)
                self.table_zbor_log.changeCellContent('path2video', str(pth), 'id', id)

    def already_in_mysql(self, plane, flight_date, start):
        match1 = ('flight_date', flight_date)
        match2 = ('start', start)
        match3 = ('plane', plane)
        matches = [match1, match2, match3]
        res = self.table_zbor_log.filterRows(matches)
        return res

    def copy_csv_to_profile(self, src):
        # try:
        pth_2_profile = r'static\backup_profile\radu'
        destination = os.path.join(os.path.dirname(__file__), pth_2_profile)
        shutil.copy(src, destination)
        dst = os.path.join(os.path.dirname(__file__), pth_2_profile, os.path.split(src)[1])
        # message = 'successfully copied {} \n\tto {}'.format(src, destination)
        # except Exception:
        #     message = traceback.format_exc()
        return dst

    def import_csv(self, csv_file):
        csv_from, tabHeadDict = self.get_csv_provider(csv_file)
        if csv_from:
            csv_file = self.copy_csv_to_profile(csv_file)
            print(csv_file)
        # return
        # print(csv_from)
        if 'vereinsflieger' in csv_from:
            cols, vals = self.import_vereinsflieger_in_sql(csv_file)
        elif 'demon' in csv_from:
            cols, vals = self.import_flydemon_csv(csv_file)
        elif 'is_fun' in csv_from:
            cols, vals = self.import_fly_is_fun_csv(csv_file)
        # cols.sort()
        print(cols, len(cols))

        # print(vals, len(vals))
        imported = 0
        not_imported = 0
        total = 0
        for row in vals:
            total += 1
            # row.append(csv_file)
            plane, flight_date, start = row[cols.index('plane')], row[cols.index('flight_date')], row[cols.index('start')]
            already_in_sql = self.already_in_mysql(plane, flight_date, start)
            if already_in_sql:
                print('&&&', row)
                not_imported += 1
            else:
                print('*', row)
                self.table_zbor_log.addNewRow(cols, row)
                imported += 1
        print('total {}, imported {}, not_imported {}'.format(total, imported, not_imported))
        self.fill_in_pph()

    def import_all_csv_in_dir(self, src_dir):
        srcDir = pathlib.Path(src_dir)
        for csv_file in srcDir.glob('*.csv'):  # rglob
            self.import_csv(csv_file)

    def get_not_paid_flights(self):
        payments = {}
        match1 = ('paid', 0)
        res = self.table_zbor_log.returnRowsWhere(match1)
        total = 0
        for row in res:
            plane = row[self.table_zbor_log.columnsNames.index('plane')]
            price = row[self.table_zbor_log.columnsNames.index('price_hour')]
            total += price
            if plane not in payments.keys():
                payments[plane] = price
            else:
                payments[plane] += price
        payments['total'] = total
        return payments


def put_files_in_dirs(src_dir):
    dirs = {}
    srcDir = pathlib.Path(src_dir)
    for media_file in srcDir.iterdir():
        if media_file.is_file():
            if re.search("^\d{8}_\d{6}", media_file.name):
                name = re.search("^\d{8}_\d{6}", media_file.name)
                name_datum = mysql_rm.convertDateTimeFormat4SQL(name.group()).date()
            elif re.search("IMG-\d{8}-", media_file.name):
                name = re.search("IMG-\d{8}-", media_file.name)
                name_datum = name.group().split('-')[1]
                name_datum = mysql_rm.convertDatumFormat4SQL(name_datum)
            if name_datum not in dirs.keys():
                dirs[name_datum] = [media_file]
            else:
                dirs[name_datum].append(media_file)

            dir_name = str(name_datum)

            newdir = media_file.parent / dir_name
            if not newdir.exists():
                os.makedirs(newdir)
            shutil.move(media_file, newdir)


def getQuartalDates(quartal, year):
    if quartal == 'Q1':
        quartal = (datetime(year, 1, 1), datetime(year, 3, 31))
    elif quartal == 'Q2':
        quartal = (datetime(year, 4, 1), datetime(year, 6, 30))
    elif quartal == 'Q3':
        quartal = (datetime(year, 7, 1), datetime(year, 9, 30))
    elif quartal == 'Q4':
        quartal = (datetime(year, 10, 1), datetime(year, 12, 31))
    return quartal



def main():
    src_dir = r"D:\Aeroclub\Zbor"
    src_dir = r"E:\Aviatie\Filmulete zbor"
    # put_files_in_dirs(src_dir)

    ini_file = r"D:\Python\MySQL\aeroclub.ini"
    ins = AeroclubSQL(ini_file)
    # ins.fill_in_pph()
    print(ins.get_not_paid_flights())
    return

    # ins.getVideo(src_dir)
    # return
    # # inpDir = r"D:\Documente\Radu\Aeroclub\Flight_Log"
    # # ins.import_all_csv_in_dir(inpDir)

    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\fly_is_fun_bis_2014.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\fly_is_fun_11.07.2015 bis 25.09.2017.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_30.09.2017_10.10.2021.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_11.10.2021_17.09.2024.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_21.09.2024_07.10.2024.csv"
    csv = r"D:\Documente\Radu\Aeroclub\Flight_Log\Export_VEREINSFLIEGER_May_2025.csv"
    ins.import_csv(csv)

    # start = datetime(2024, 5, 11, 7, 58, 0)
    # end = datetime(2024, 5, 11, 8, 22, 0)
    # pph = ins.get_price_per_time("D-MENF", (start, end))
    # # start = datetime(2024, 9, 8, 12, 39, 0)
    # # end = datetime(2024, 9, 8, 13, 6, 0)
    # # pph = ins.get_price_per_time("D-MOEO", (start, end))
    # print(pph)


if __name__ == '__main__':
    # inpFile = r"D:\Documente\Aeroclub\Bad_Endorf\Export.csv"

    # write2flightTable(inpFile)
    # quartals = ['Q1', 'Q2', 'Q3', 'Q4']
    # for year in range(2022, 2023):
    #     for q in quartals:
    #         interval = getQuartalDates(q, year)
    #         print(interval)
    # #         price = getPrice4Time(interval[0], interval[1])
    # #         print(year, q, price)
    # # pth = r"E:\Aviatie\Filmulete zbor"
    # # getVideo(pth)
    main()
