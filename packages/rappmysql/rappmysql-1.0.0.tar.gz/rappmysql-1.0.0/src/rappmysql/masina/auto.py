import numpy as np
from rappmysql.mysqlquerys import connect
from rappmysql.mysqlquerys import mysql_rm
from datetime import datetime, timedelta
import traceback
import sys, os
import time

np.set_printoptions(linewidth=250)
compName = os.getenv('COMPUTERNAME')
try:
    compName = os.getenv('COMPUTERNAME')
    if compName == 'DESKTOP-5HHINGF':
        ini_users = r"D:\Python\MySQL\users.ini"
        ini_chelt = r"D:\Python\MySQL\cheltuieli.ini"
        ini_masina = r"D:\Python\MySQL\masina.ini"
        report_dir = r"D:\Python\MySQL\onlineanywhere\static"
    else:
        ini_users = r"C:\_Development\Diverse\pypi\cfgm.ini"
        ini_chelt = r"C:\_Development\Diverse\pypi\cfgm.ini"
        ini_masina = r"C:\_Development\Diverse\pypi\cfgm.ini"
        # ini_file = r"C:\_Development\Diverse\pypi\cfgmRN.ini"
        report_dir = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\static"
except:
    ini_users = '/home/radum/mysite/static/wdb.ini'



class Masina:
    def __init__(self, ini_file, user_id, id_car):
        '''
        :param ini_file:type=QFileDialog.getOpenFileName name=filename file_type=(*.ini;*.txt)
        '''
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.user_id = user_id
        self.id_car = id_car
        if isinstance(ini_file, dict):
            credentials = ini_file
        else:
            self.conf = connect.Config(ini_file)
            credentials = self.conf.credentials
        self.checkup_list(credentials)
        self.alimentari = mysql_rm.Table(credentials, 'masina')
        self.types_of_costs = ["electric", "benzina", "intretinere", "asigurare", 'impozit', 'TüV', 'carwash']

    def checkup_list(self, credentials):
        if not isinstance(credentials, dict):
            raise RuntimeError('Credentials not dict')
        db = mysql_rm.DataBase(credentials)
        if not db.is_connected:
            raise RuntimeError('Could not connect to database')
        print('Connected to database:', db.is_connected)
        if 'users' not in db.allAvailableTablesInDatabase:
            print('Table "users" not in database...creating')
            pth_template_users = os.path.join(os.path.dirname(__file__), 'static', 'sql', 'users_template.sql')
            if not os.path.exists(pth_template_users):
                raise RuntimeError('Could not find {}'.format(pth_template_users))
            db.createTableFromFile(pth_template_users, 'users')
        # else:
        #     users_table = mysql_rm.Table(credentials, 'users')
        #     print()

    @property
    def no_of_records(self):
        return self.alimentari.noOfRows

    @property
    def default_interval(self):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        startDate = datetime(datetime.now().year - 1, datetime.now().month, datetime.now().day)
        endDate = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
        return startDate, endDate

    @property
    def total_money(self):
        col = self.alimentari.returnColumn('brutto')
        return round(sum(col), 2)

    @property
    def tot_benzina(self):
        matches = [('type', 'benzina'),
                   ('id_users', self.user_id),
                   ('id_all_cars', self.id_car)]
        col = self.alimentari.returnCellsWhere('brutto', matches)
        return round(sum(col), 2)

    @property
    def tot_electric(self):
        matches = [('type', 'electric'),
                   ('id_users', self.user_id),
                   ('id_all_cars', self.id_car)]
        col = self.alimentari.returnCellsWhere('brutto', matches)
        return round(sum(col), 2)

    @property
    def monthly(self):
        try:
            return round((self.monthly_benzina + self.monthly_electric), 2)
        except:
            return None

    @property
    def monthly_benzina(self):
        try:
            matches = [('type', 'benzina'),
                       ('id_users', self.user_id),
                       ('id_all_cars', self.id_car)]
            rows = self.alimentari.returnRowsWhere(matches)
            rows = np.atleast_2d(rows)
            money = rows[:, self.alimentari.columnsNames.index('brutto')]
            start_date = min(rows[:, self.alimentari.columnsNames.index('data')])
            finish_date = max(rows[:, self.alimentari.columnsNames.index('data')])

            total_money = round(sum(money), 2)
            days = (finish_date - start_date).days
            average_day_per_month = 365 / 12
            monthly = (average_day_per_month * total_money) / days
            return round(monthly, 2)
        except:
            return None

    @property
    def monthly_electric(self):
        matches = [('type', 'electric'),
                   ('id_users', self.user_id),
                   ('id_all_cars', self.id_car)]
        rows = self.alimentari.returnRowsWhere(matches)
        rows = np.atleast_2d(rows)
        money = rows[:, self.alimentari.columnsNames.index('brutto')]
        start_date = min(rows[:, self.alimentari.columnsNames.index('data')])
        finish_date = max(rows[:, self.alimentari.columnsNames.index('data')])
        total_money = round(sum(money), 2)
        days = (finish_date - start_date).days
        average_day_per_month = 365 / 12
        try:
            monthly = (average_day_per_month * total_money) / days
            return round(monthly, 2)
        except:
            return None

    @property
    def db_start_date(self):
        all_dates = self.alimentari.returnColumn('data')
        matches = [('id_users', self.user_id),
                   ('id_all_cars', self.id_car)]
        all_dates = self.alimentari.returnCellsWhere('data', matches)
        # print('**all_dates', all_dates, type(all_dates))
        if all_dates:
            start_date = min(all_dates)
        else:
            start_date = None
        return start_date

    @property
    def db_last_record_date(self):
        try:
            # all_dates = self.alimentari.returnColumn('data')
            matches = [('id_users', self.user_id),
                       ('id_all_cars', self.id_car)]
            all_dates = self.alimentari.returnCellsWhere('data', matches)
            finish_date = max(all_dates)
            return finish_date
        except:
            return None

    @property
    def table_alimentari(self):
        arr = [('', 'Alimentari[€]', 'Benzina[€]', 'Electric[€]')]
        if self.no_of_records > 0:
            total_alim = round(self.tot_benzina + self.tot_electric, 2)
            arr.append(('Monthly', self.monthly, self.monthly_benzina, self.monthly_electric))
            arr.append(('Total', total_alim, self.tot_benzina, self.tot_electric))
        else:
            arr.append(('Monthly', None, None, None))
            arr.append(('Total', None, None, None))

        arr = np.atleast_2d(arr)
        return arr

    # @property
    # def bkp_table_totals(self):
    #     if not self.db_start_date:
    #         return None
    #     types = ['benzina', 'electric', 'asigurare', 'impozit', 'TüV', 'intretinere']
    #     table = []
    #     try:
    #         for year in reversed(range(self.db_start_date.year, self.db_last_record_date.year + 1)):
    #             dd = {}
    #             dd['year'] = year
    #             startTime = datetime(year, 1, 1)
    #             endTime = datetime(year, 12, 31)
    #             rows = self.alimentari.returnRowsOfYear('data', startTime, 'data', endTime)
    #             arr = np.atleast_2d(rows)
    #             tot = 0
    #             for t in types:
    #                 indx = np.where(arr[:, self.alimentari.columnsNames.index('type')] == t)
    #                 # if t == 'asigurare':
    #                 #     print(indx)
    #                 col = arr[indx, self.alimentari.columnsNames.index('brutto')]
    #                 value = sum(col[0])
    #                 value = round(value, 2)
    #                 dd[t] = value
    #                 tot += value
    #             dd['total/row'] = round(tot, 2)
    #             table.append(dd)
    #             # print(dd)
    #         table_head = tuple(dd.keys())
    #         arr = [table_head]
    #         for tab in table:
    #             row = []
    #             for k, v in tab.items():
    #                 row.append(v)
    #             arr.append(tuple(row))
    #         arr = np.atleast_2d(arr)
    #         row_totals = ['totals']
    #         total_total = 0
    #         for col in range(1, arr.shape[1]):
    #             # print(arr[0, col], round(sum(arr[1:, col].astype(float)), 2))
    #             val = round(sum(arr[1:, col].astype(float)), 2)
    #             row_totals.append(val)
    #             total_total += val
    #         row_tot = np.array(row_totals)
    #         new_arr = np.insert(arr, 1, row_tot, axis=0)
    #         return new_arr
    #     except:
    #         print(traceback.format_exc())
    #         return table

    @property
    def dict_totals(self):
        if not self.db_start_date:
            return None
        table_dict = {}
        try:
            for year in reversed(range(self.db_start_date.year, self.db_last_record_date.year + 1)):
                dd = {}
                startTime = datetime(year, 1, 1)
                endTime = datetime(year, 12, 31)
                tot = 0
                for t in self.types_of_costs:
                    # print('t', t)
                    matches = [('id_users', '=', self.user_id),
                               ('id_all_cars', '=', self.id_car),
                               ('type', '=', t),
                               ('data', '>=', startTime),
                               ('data', '<=', endTime)
                               ]
                    payments4Interval = self.alimentari.returnRowsQuery(matches)
                    if payments4Interval:
                        payments4Interval = np.atleast_2d(payments4Interval)
                        col = payments4Interval[:, self.alimentari.columnsNames.index('brutto')]
                        value = sum(col)
                        value = round(value, 2)
                        dd[t] = value
                        tot += value
                dd['total/row'] = round(tot, 2)
                table_dict[year] = dd
            return table_dict
        except:
            return str(traceback.format_exc())

    @property
    def table_totals(self):
        table_head = self.types_of_costs.copy()
        table_totals = []
        for year, expenses in self.dict_totals.items():
            row = [year]
            total_per_year = 0
            for col in table_head:
                if col in expenses.keys():
                    row.append(expenses[col])
                    total_per_year += expenses[col]
                else:
                    row.append(0)
            row.append(round(total_per_year, 2))
            table_totals.append(tuple(row))
        table_head.insert(0, 'year')
        table_head.append('tot/year')
        table_totals.insert(0, tuple(table_head))
        table_totals = np.atleast_2d(table_totals)
        return table_totals

    @property
    def last_records(self):
        # print(len(tuple(self.alimentari.columnsNames)))
        table_head = self.alimentari.columnsNames.copy()
        table_head.remove('file')
        last_records = [tuple(table_head)]
        for typ in self.types_of_costs:
            matches = [('id_users', self.user_id),
                       ('id_all_cars', self.id_car),
                       ('type', typ)]
            table = self.alimentari.filterRows(matches, order_by=('data', 'DESC'))
            if table:
                # print('++', tuple(table[0]), len(tuple(table[0])))
                last_records.append(tuple(table[0]))

        last_records = np.atleast_2d(last_records)
        # last_records = np.atleast_2d(last_records)
        return last_records

    def delete_row(self, row_id):
        condition = ('id', row_id)
        self.alimentari.delete_multiple_rows(condition)

    def get_monthly_interval(self, month: str, year):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        mnth = datetime.strptime(month, "%B").month
        startDate = datetime(year, mnth, 1)

        if mnth != 12:
            lastDayOfMonth = datetime(year, mnth + 1, 1) - timedelta(days=1)
        else:
            lastDayOfMonth = datetime(year + 1, 1, 1) - timedelta(days=1)

        return startDate, lastDayOfMonth

    def get_all_alimentari(self):
        cols = []
        for k, v in self.alimentari.columnsDetProperties.items():
            if v[0] == 'longblob':
                continue
            cols.append(k)
        alimentari = self.alimentari.returnColumns(cols)
        # alimentari = self.alimentari.returnAllRecordsFromTable()
        alimentari = np.atleast_2d(alimentari)
        alimentari = np.insert(alimentari, 0, cols, axis=0)
        return alimentari

    def get_alimentari_for_interval_type(self, selectedStartDate, selectedEndDate, alim_type):
        # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        matches = [('data', (selectedStartDate, selectedEndDate)),
                   ('id_users', self.user_id),
                   ('id_all_cars', self.id_car)]
        if alim_type:
            matches.append(('type', alim_type))
        print(matches)
        table = self.alimentari.filterRows(matches, order_by=('data', 'DESC'))

        if table:
            table_head = []
            for col_name, prop in self.alimentari.columnsDetProperties.items():
                # print(col_name, prop)
                if prop[0] == 'longblob':
                    continue
                table_head.append(col_name)
            arr = np.atleast_2d(table)
            arr = np.insert(arr, 0, np.array(table_head), axis=0)
        else:
            arr = np.atleast_2d(np.array(self.alimentari.columnsNames))
        return arr

    def upload_file(self, file_name, id):
        self.alimentari.changeCellContent('file', file_name, 'id', id)
        pth, file_name = os.path.split(file_name)
        self.alimentari.changeCellContent('file_name', file_name, 'id', id)

    def insert_new_alim(self, current_user_id, id_all_cars, data, alim_type, brutto, amount, refuel, other, recharges,
                        km, comment, file, provider):
        '''
        :param data:type=dateTime name=date
        :param alim_type:type=comboBox name=alim_type items=[electric,benzina,TüV,intretinere]
        :param brutto:type=text name=brutto
        :param amount:type=text name=amount
        :param refuel:type=text name=refuel
        :param other:type=text name=other
        :param recharges:type=text name=recharges
        :param km:type=text name=km
        :param comment:type=text name=comment
        :param file:type=QFileDialog.getOpenFileName name=file
        '''
        if file:
            _, file_name = os.path.split(file)
            cols = ['id_users', 'id_all_cars', 'data', 'type', 'brutto', 'amount', 'refuel', 'other', 'recharges',
                    'ppu', 'km', 'comment', 'file', 'file_name', 'eProvider']
        else:
            cols = ['id_users', 'id_all_cars', 'data', 'type', 'brutto', 'amount', 'refuel', 'other', 'recharges',
                    'ppu', 'km', 'comment', 'eProvider']
        try:
            if isinstance(brutto, str) and ',' in brutto:
                brutto = brutto.replace(',', '.')
            brutto = float(brutto)
        except:
            brutto = None
        try:
            if isinstance(amount, str) and ',' in amount:
                amount = amount.replace(',', '.')
            elif amount == '':
                amount = 1
            amount = float(amount)
        except:
            amount = None
        try:
            if isinstance(refuel, str) and ',' in refuel:
                refuel = refuel.replace(',', '.')
            refuel = float(refuel)
        except:
            refuel = None
        try:
            if isinstance(other, str) and ',' in other:
                other = other.replace(',', '.')
            other = float(other)
        except:
            other = None
        try:
            if isinstance(recharges, str) and ',' in recharges:
                recharges = recharges.replace(',', '.')
            recharges = float(recharges)
        except:
            recharges = None
        try:
            km = int(km)
        except:
            km = None

        ppu = round(float(brutto) / float(amount), 3)
        if file:
            vals = [current_user_id, id_all_cars, data, alim_type, brutto, amount, refuel, other, recharges, ppu, km,
                    comment, file, file_name, provider]
        else:
            vals = [current_user_id, id_all_cars, data, alim_type, brutto, amount, refuel, other, recharges, ppu, km,
                    comment, provider]

        self.alimentari.addNewRow(cols, tuple(vals))

    def create_sql_table(self, table_name):
        masina_sql = os.path.join(os.path.dirname(__file__), 'static', 'sql',
                                  'auto_template.sql')

        # masina_sql = r'static\sql\auto.sql'
        mysql_rm.DataBase(self.conf.credentials).createTableFromFile(masina_sql, table_name)


def main():
    script_start_time = time.time()
    selectedStartDate = datetime(2021, 1, 1, 0, 0, 0)
    selectedEndDate = datetime(2025, 8, 31, 0, 0, 0)

    # if compName == 'DESKTOP-5HHINGF':
    #     ini_file = r"D:\Python\MySQL\cheltuieli.ini"
    # else:
    #     ini_file = r"C:\_Development\Diverse\pypi\cfgm.ini"
    #     # ini_file = r"C:\_Development\Diverse\pypi\cfgmRN.ini"

    # aaatest = Masina(ini_file, 'aaaa_aaaa')
    # fl = r"C:\_Development\Diverse\pypi\radu\Rechnung.pdf"
    # aaatest.upload_file(fl, 2)
    app_masina = Masina(ini_masina, 1, 1)
    # alimentari = app_masina.get_alimentari_for_interval_type(selectedStartDate, selectedEndDate, None)
    # for i in alimentari:
    #     print(i)
    # print(len(alimentari))
    # print(app_masina.tot_benzina)
    # print(app_masina.tot_electric)
    # print(app_masina.monthly_benzina)
    # print(app_masina.monthly_electric)
    # print(app_masina.dict_totals)
    # print(app_masina.bkp_table_totals)
    print(app_masina.dict_totals)
    print()
    print(app_masina.table_totals)
    # print(app_masina.last_records.shape)

    scrip_end_time = time.time()
    duration = scrip_end_time - script_start_time
    duration = time.strftime("%H:%M:%S", time.gmtime(duration))
    print('run time: {}'.format(duration))


if __name__ == '__main__':
    main()
