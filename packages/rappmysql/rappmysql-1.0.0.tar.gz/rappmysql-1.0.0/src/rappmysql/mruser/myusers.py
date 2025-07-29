import csv
import os.path
import traceback
import numpy as np
import datetime as dt
from datetime import datetime, timedelta
import time
import sys
import json
import shutil
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import zipfile
from rappmysql.mysqlquerys import connect, mysql_rm
import rappmysql.masina as masina
# from rappmysql.masina.auto import Masina

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


np.set_printoptions(linewidth=250)
__version__ = 'V5'

app_tables_dict = {'users': 'id', 'user_apps': 'id_users'}
app_masina_tables = {'all_cars': 'user_id'}


# tables_dict = {'users': 'id',
#                'user_apps': 'id_users',
#                'banca': 'id_users',
#                'chelt_plan': 'id_users',
#                'knowntrans': 'id_users',
#                'income': 'id_users',
#                'deubnk': 'id_users',
#                'n26': 'id_users',
#                'sskm': 'id_users',
#                'plan_vs_real': 'id_users',
#                'imported_csv': 'id_users',
#                'yearly_plan': 'id_users',
#                }
# tables_app_dict = {'planned_expenses_app': {'users': 'id',
#                                             'user_apps': 'id_users',
#                                             'chelt_plan': 'id_users',
#                                             'yearly_plan': 'id_users'},
#                    'real_expenses_app': {'users': 'id',
#                                          'user_apps': 'id_users',
#                                          'chelt_plan': 'id_users',
#                                          'yearly_plan': 'id_users',
#                                          'banca': 'id_users',
#                                          'knowntrans': 'id_users',
#                                          'income': 'id_users',
#                                          'deubnk': 'id_users',
#                                          'n26': 'id_users',
#                                          'sskm': 'id_users',
#                                          'plan_vs_real': 'id_users',
#                                          'imported_csv': 'id_users',
#                                          }
#                    }
# sskm_tabHeadDict = {'Auftragskonto': 'Auftragskonto',
#                     'Buchungstag': 'Buchungstag',
#                     'Valutadatum': 'Valutadatum',
#                     'Buchungstext': 'Buchungstext',
#                     'Verwendungszweck': 'Verwendungszweck',
#                     'Glaeubiger ID': 'Glaeubiger',
#                     'Mandatsreferenz': 'Mandatsreferenz',
#                     'Kundenreferenz (End-to-End)': 'Kundenreferenz',
#                     'Sammlerreferenz': 'Sammlerreferenz',
#                     'Lastschrift Ursprungsbetrag': 'Lastschrift',
#                     'Auslagenersatz Ruecklastschrift': 'Auslagenersatz',
#                     'Beguenstigter/Zahlungspflichtiger': 'Beguenstigter',
#                     'Kontonummer/IBAN': 'IBAN',
#                     'BIC (SWIFT-Code)': 'BIC',
#                     'Betrag': 'Betrag',
#                     'Waehrung': 'Waehrung',
#                     'Info': 'Info'}
# n26_tabHeadDict = {'Booking Date': 'Buchungstag',
#                    'Value Date': 'ValueDate',
#                    'Partner Name': 'Beguenstigter',
#                    'Partner Iban': 'IBAN',
#                    'Type': 'Type',
#                    'Payment Reference': 'PaymentReference',
#                    'Account Name': 'AccountName',
#                    'Amount (EUR)': 'Amount',
#                    'Original Amount': 'OriginalAmount',
#                    'Original Currency': 'OriginalCurrency',
#                    'Exchange Rate': 'ExchangeRate'
#                    }
# db_tabHeadDict = {'Booking date': 'Buchungstag',
#                   'Value date': 'Valuedate',
#                   'Transaction Type': 'TransactionType',
#                   'Beneficiary / Originator': 'Beguenstigter',
#                   'Payment Details': 'Verwendungszweck',
#                   'IBAN': 'IBAN',
#                   'BIC': 'BIC',
#                   'Customer Reference': 'CustomerReference',
#                   'Mandate Reference': 'Mandatsreferenz',
#                   'Creditor ID': 'CreditorID',
#                   'Compensation amount': 'Compensationamount',
#                   'Original Amount': 'OriginalAmount',
#                   'Ultimate creditor': 'Ultimatecreditor',
#                   'Ultimate debtor': 'Ultimatedebtor',
#                   'Number of transactions': 'Numberoftransactions',
#                   'Number of cheques': 'Numberofcheques',
#                   'Debit': 'Debit',
#                   'Credit': 'Credit',
#                   'Currency': 'Currency'
#                   }
#
# plan_vs_real_tabHeadDict = {'sskm': {'Buchungstag': 'Buchungstag',
#                                      'myconto': 'myconto',
#                                      'Betrag': 'Betrag',
#                                      'PaymentReference': 'Verwendungszweck',
#                                      'PartnerName': 'Beguenstigter'},
#                             'n26': {'Buchungstag': 'Buchungstag',
#                                     'myconto': 'myconto',
#                                     'Betrag': 'Amount',
#                                     'PaymentReference': 'PaymentReference',
#                                     'PartnerName': 'Beguenstigter'},
#                             'deubnk': {'Buchungstag': 'Buchungstag',
#                                        'myconto': 'myconto',
#                                        'Betrag': 'Debit',
#                                        'PaymentReference': 'Verwendungszweck',
#                                        'PartnerName': 'Beguenstigter'},
#                             }
#
# bank_tabHeadDict = {'Stadtsparkasse München': sskm_tabHeadDict,
#                     'N26': n26_tabHeadDict,
#                     'DeutscheBank': db_tabHeadDict,
#                     }
#
# bank_sql_table = {'Stadtsparkasse München': 'sskm',
#                   'N26': 'n26',
#                   'DeutscheBank': 'deubnk',
#                   }


def calculate_last_day_of_month(mnth, year):
    if mnth < 12:
        # lastDayOfMonth = datetime(datetime.now().year, mnth + 1, 1) - timedelta(days=1)
        lastDayOfMonth = datetime(year, mnth + 1, 1) - timedelta(days=1)
        lastDayOfMonth = lastDayOfMonth.day
    elif mnth == 12:
        lastDayOfMonth = 31
    return lastDayOfMonth


def calculate_today_plus_x_days(x_days):
    result = datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(days=int(x_days))
    return result


def default_interval():
    # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    print('Caller : ', sys._getframe().f_back.f_code.co_name)
    startDate = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
    if datetime.now().month != 12:
        mnth = datetime.now().month + 1
        lastDayOfMonth = datetime(datetime.now().year, mnth, 1) - timedelta(days=1)
    else:
        lastDayOfMonth = datetime(datetime.now().year + 1, 1, 1) - timedelta(days=1)

    return startDate, lastDayOfMonth


def get_monthly_interval(month: str, year):
    # print('Module: {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
    mnth = datetime.strptime(month, "%B").month
    startDate = datetime(year, mnth, 1)

    if mnth != 12:
        lastDayOfMonth = datetime(year, mnth + 1, 1) - timedelta(days=1)
    else:
        lastDayOfMonth = datetime(year + 1, 1, 1) - timedelta(days=1)

    return startDate.date(), lastDayOfMonth.date()


def convert_to_display_table(tableHead, table, displayTableHead):
    newTableData = np.empty([table.shape[0], len(displayTableHead)], dtype=object)
    for i, col in enumerate(displayTableHead):
        indxCol = tableHead.index(col)
        newTableData[:, i] = table[:, indxCol]
    return displayTableHead, newTableData


class CheltApp:
    def __init__(self, ini_file):
        print('__init__CheltApp')
        if isinstance(ini_file, dict):
            credentials = ini_file
        else:
            self.conf = connect.Config(ini_file)
            credentials = self.conf.credentials
        try:
            self.credentials = credentials
            self.auto_db = mysql_rm.DataBase(credentials)
        except:
            print('Could not connect to database')
            raise RuntimeError
        # try:
        #     self.auto_app_checkup_tables()
        #     self.all_cars_table = mysql_rm.Table(self.credentials, 'all_cars')
        #     self.alimentari = mysql_rm.Table(self.credentials, 'masina')
        # except:
        #     print('Could not connect to Tables')
        #     raise RuntimeError('Could not connect to Tables')

    @property
    def cheltuieli(self):
        return 'pula'


class AutoApp:
    def __init__(self, ini_masina):
        print('__init__AutoApp')
        if isinstance(ini_masina, dict):
            credentials = ini_masina
        else:
            self.conf = connect.Config(ini_masina)
            credentials = self.conf.credentials
        try:
            self.credentials = credentials
            self.auto_db = mysql_rm.DataBase(credentials)
        except:
            print('Could not connect to database')
            raise RuntimeError
        try:
            self.auto_app_checkup_tables()
            self.all_cars_table = mysql_rm.Table(self.credentials, 'all_cars')
            self.alimentari = mysql_rm.Table(self.credentials, 'masina')
        except:
            print('Could not connect to Tables')
            raise RuntimeError('Could not connect to Tables')

    def auto_app_checkup_tables(self):
        # for car in self.masini:
        #     app_masina_tables[car.lower()] = 'id_users'

        for table in app_masina_tables.keys():
            # print('##table##', table)
            pth_table_template = os.path.join(os.path.dirname(masina.__file__), 'static', 'sql',
                                              '{}_template.sql'.format(table))
            if table not in self.auto_db.allAvailableTablesInDatabase:
                print('Table {} not in database...creating it'.format(table))
                self.auto_db.createTableFromFile(pth_table_template, table)
            else:
                # exec("sqltable = mysql_rm.Table(self.credentials, '{}')".format(table))
                varName = 'table_{}'.format(table)
                # print("{} = mysql_rm.Table(self.credentials, '{}')".format(varName, table))
                # print('ÄÄ', varName)
                loc = locals()
                # print(loc)
                exec("{} = mysql_rm.Table(self.credentials, '{}')".format(varName, table), globals(), loc)
                varName = loc[varName]
                same = varName.compare_sql_file_to_sql_table(pth_table_template)
                if same is not True:
                    print(same)

    @property
    def masini(self):
        # print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        masini = []
        matches = ('user_id', self.id)
        cars_rows = self.all_cars_table.returnRowsWhere(matches)
        if cars_rows:
            for row in cars_rows:
                indx_brand = self.all_cars_table.columnsNames.index('brand')
                indx_model = self.all_cars_table.columnsNames.index('model')
                table_name = '{}_{}'.format(row[indx_brand], row[indx_model])
                masini.append(table_name)
        return masini

    @property
    def electric_providers(self):
        matches = [('type', 'electric')]
        col = self.alimentari.returnCellsWhere('eProvider', matches)
        electric_providers = list(set(col))
        # electric_providers = ['eCharge', 'MyHyundai', 'EnBW', 'SWM_Plus', 'SWM']
        return electric_providers

    def add_car(self, brand, model, car_type):
        brand = brand.lower()
        model = model.lower()
        car_type = car_type.lower()
        cols = ('user_id', 'brand', 'model', 'cartype')
        vals = (self.id, brand, model, car_type)
        matches = [('user_id', self.id), ('brand', brand), ('model', model), ('cartype', car_type)]
        existing_row = self.all_cars_table.returnRowsWhere(matches)
        # print('existing_row', existing_row)
        if existing_row:
            print('car already existing at id {}'.format(existing_row[0][0]))
            return
        else:
            self.all_cars_table.addNewRow(cols, vals)
            new_auto_table = '{}_{}'.format(brand, model)
            new_auto_table = new_auto_table.lower()
            if new_auto_table in self.auto_db.allAvailableTablesInDatabase:
                print('table {} existing in database'.format(new_auto_table))
            else:
                pth_auto_template = os.path.join(os.path.dirname(masina.__file__), 'static', 'sql', 'auto_template.sql')
                self.auto_db.createTableFromFile(pth_auto_template, new_auto_table)

    def export_car_sql(self, car_id, export_files=False):
        all_cars_ident = {'user_id': self.id, 'id': car_id}
        masina_ident = {'id_users': self.id, 'id_all_cars': car_id}
        tables = {'all_cars': all_cars_ident,
                  'masina': masina_ident}

        tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
        output_dir = os.path.join(os.path.dirname(masina.__file__), 'static', 'backup_profile',
                                  '{:09d}'.format(self.id),
                                  '{:09d}'.format(car_id),
                                  '{}_{:09d}'.format(tim, car_id))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if export_files:
            sql_query = self.auto_db.return_sql_text(tables, export_files=output_dir)
        else:
            sql_query = self.auto_db.return_sql_text(tables)

        output_sql_file = os.path.join(output_dir, '{}_{:09d}.sql'.format(tim, self.id))
        FILE = open(output_sql_file, "w", encoding="utf-8")
        FILE.writelines(sql_query)
        FILE.close()
        #####
        output_zip = os.path.join(os.path.dirname(output_dir), '{}.zip'.format(output_dir))
        zip_file = self.zip_profile_files(output_dir, output_zip)
        if os.path.exists(zip_file):
            shutil.rmtree(output_dir)
        print('finished backup')

        return output_sql_file

    def import_car_with_files(self, zip_file, import_files=False):
        output_dir, file = os.path.split(zip_file)
        src_dir = self.unzip_profile_files(zip_file, output_dir)
        src_dir = os.path.join(src_dir, file[:-4])
        if not os.path.exists(src_dir):
            raise RuntimeError('Missing Folder {}'.format(src_dir))

        sql_files = [x for x in os.listdir(src_dir) if x.endswith('.sql')]
        sql_file = os.path.join(src_dir, sql_files[0])
        # print(sql_file)
        # return
        self.db.run_sql_file(sql_file)
        if import_files:
            attachments = [x for x in os.listdir(src_dir) if
                           (x.endswith('.jpg') or
                            x.endswith('.pdf') or
                            x.endswith('.csv') or
                            x.endswith('.CSV')
                            )]
            tab = []
            for file_name in attachments:
                try:
                    # print(file_name)
                    table_id, orig_name = file_name.split('+')
                    fil = os.path.join(src_dir, file_name)
                    self.alimentari.changeCellContent('file', fil, 'id', table_id)
                    self.alimentari.changeCellContent('file_name', str(orig_name), 'id', table_id)
                    # print(user_id, table_name, table_id, orig_name)
                except:
                    print('could not import {}, name not ok'.format(file_name))
                tup = (table_id, orig_name, file_name)
                tab.append(tup)
            # tab = np.atleast_2d(tab)
            # all_sql_tables = list(np.unique(tab[:, 1]))
            # for table_name in all_sql_tables:
            #     # print('table_name', table_name)
            #     sql_table = mysql_rm.Table(self.credentials, table_name)
            #     table = tab[tab[:, 1] == table_name]
            #     for row in table:
            #         user_id, table_name, table_id, orig_name, fl_name = row
            #         # print('&', user_id, table_name, table_id, orig_name, fl_name)
            #         fil = os.path.join(src_dir, fl_name)
            #         sql_table.changeCellContent('file', fil, 'id', table_id)
            #         sql_table.changeCellContent('file_name', str(orig_name), 'id', table_id)
        if os.path.exists(src_dir):
            shutil.rmtree(src_dir)

    def get_id_all_cars(self, table_name):
        brand, model = table_name.split('_')
        matches = [('user_id', self.id),
                   ('brand', brand),
                   ('model', model),
                   ]
        # print(matches)
        id_all_cars = self.all_cars_table.returnCellsWhere('id', matches)[0]
        return id_all_cars

    def delete_auto(self, table_name):
        brand, model = table_name.split('_')
        matches = [('user_id', self.id), ('brand', brand), ('model', model)]
        id_car = self.all_cars_table.returnCellsWhere('id', matches)
        # print('id_car', id_car)
        condition = ['id', id_car[0]]
        self.all_cars_table.delete_multiple_rows(condition)


class Users(UserMixin, AutoApp, CheltApp):
    def __init__(self, user_name, ini_users):
        super().__init__(ini_masina)
        # CheltApp.__init__(self, ini_file)
        self.user_name = user_name
        # self.auto_db = None
        # self.all_cars_table = None
        self.app_credentials = {}
        if isinstance(ini_users, dict):
            credentials = ini_users
        else:
            self.conf = connect.Config(ini_users)
            credentials = self.conf.credentials
        try:
            self.credentials = credentials
            self.db = mysql_rm.DataBase(credentials)
        except:
            print('Could not connect to database')
            raise RuntimeError
        try:
            self.app_checkup_list()
            #     self.checkup_list()
            self.users_table = mysql_rm.Table(self.credentials, 'users')
            self.user_apps_table = mysql_rm.Table(self.credentials, 'user_apps')
            # if self.user_name:
            #     self.login_user_in_apps()
        except:
            print('Could not connect to Tables')
            raise RuntimeError('Could not connect to Tables')

    # def login_user_in_apps(self):
    #     for app in self.applications:
    #         matches = [('id_users', self.id), ('app_name', app)]
    #         credentials = self.user_apps_table.returnCellsWhere('app_credentials', matches)[0]
    #         identif = credentials.replace("'", '"')
    #         credentials = json.loads(identif)
    #         self.app_credentials[app] = credentials
    #         # if app == 'masina':
    #         #     self.all_cars_table = mysql_rm.Table(credentials, 'all_cars')
    #         #     self.auto_db = mysql_rm.DataBase(credentials)
    #         # print('===', self.all_cars_table.noOfRows)

    def app_checkup_list(self):
        for table in app_tables_dict.keys():
            # print(table)
            pth_table_template = os.path.join(os.path.dirname(__file__), 'static', 'sql',
                                              '{}_template.sql'.format(table))
            if table not in self.db.allAvailableTablesInDatabase:
                print('Table {} not in database...creating it'.format(table))
                self.db.createTableFromFile(pth_table_template, table)
            else:
                # exec("sqltable = mysql_rm.Table(self.credentials, '{}')".format(table))
                varName = 'table_{}'.format(table)
                # print("{} = mysql_rm.Table(self.credentials, '{}')".format(varName, table))
                # print('ÄÄ', varName)
                loc = locals()
                # print(loc)
                exec("{} = mysql_rm.Table(self.credentials, '{}')".format(varName, table), globals(), loc)
                varName = loc[varName]
                same = varName.compare_sql_file_to_sql_table(pth_table_template)
                # if same is not True:
                #     print(same)

    # def checkup_list(self):
    #     for table in tables_dict.keys():
    #         print(table)
    #         pth_table_template = os.path.join(os.path.dirname(__file__), 'static', 'sql',
    #                                           '{}_template.sql'.format(table))
    #         if table not in self.db.allAvailableTablesInDatabase:
    #             print('Table {} not in database...creating it'.format(table))
    #             self.db.createTableFromFile(pth_table_template, table)
    #         else:
    #             # exec("sqltable = mysql_rm.Table(self.credentials, '{}')".format(table))
    #             varName = 'table_{}'.format(table)
    #             loc = locals()
    #             exec("{} = mysql_rm.Table(self.credentials, '{}')".format(varName, table), globals(), loc)
    #             varName = loc[varName]
    #             same = varName.compare_sql_file_to_sql_table(pth_table_template)
    #             # if same is not True:
    #             #     print(same)
    #
    # def user_checkup_list(self):
    #     # print('====', self.user_name)
    #     for app in self.user_apps:
    #         # print('====',tables_app_dict[app])
    #         for table in tables_app_dict[app].keys():
    #             print(table)
    #             pth_table_template = os.path.join(os.path.dirname(__file__), 'static', 'sql',
    #                                               '{}_template.sql'.format(table))
    #             if table not in self.db.allAvailableTablesInDatabase:
    #                 print('Table {} not in database...creating it'.format(table))
    #                 self.db.createTableFromFile(pth_table_template, table)
    #             else:
    #                 # exec("sqltable = mysql_rm.Table(self.credentials, '{}')".format(table))
    #                 varName = 'table_{}'.format(table)
    #                 loc = locals()
    #                 exec("{} = mysql_rm.Table(self.credentials, '{}')".format(varName, table), globals(), loc)
    #                 varName = loc[varName]
    #                 same = varName.compare_sql_file_to_sql_table(pth_table_template)
    #                 # if same is not True:
    #                 #     print(same)

    def add_user(self, register_details):
        cols = []
        vals = []
        for k, v in register_details.items():
            cols.append(k)
            vals.append(v)
        user_id = self.users_table.addNewRow(cols, tuple(vals))
        return user_id

    def add_application(self, app_name):
        cols = ['id_users', 'app_name']  # , 'app_credentials'
        # new_credentials = {}
        # for k, v in self.credentials.items():
        #     if k == 'password':
        #         v = generate_password_hash(v)
        #     if k == 'database' and v == 'users':
        #         v = app_name
        #     else:
        #         v = v
        #     new_credentials[k] = v

        vals = [self.id, app_name]  # , str(new_credentials)
        id_app_row = self.user_apps_table.addNewRow(cols, tuple(vals))
        return id_app_row

    def run_sql_query(self, file):
        self.db.run_sql_file(file)

    @property
    def all_users(self):
        all_users = self.users_table.returnColumn('username')
        return all_users

    @property
    def all_possible_applications(self):
        all_possible_applications = self.user_apps_table.returnColumn('app_name')
        all_possible_applications = list(set(all_possible_applications))
        all_possible_applications = ['cheltuieli', 'masina']
        return all_possible_applications

    @property
    def unused_applications(self):
        unused_applications = set(self.applications) ^ set(self.all_possible_applications)
        # unused_applications = ['cheltuieli', 'masina']
        return list(unused_applications)

    @property
    def id(self):
        matches = ('username', self.user_name)
        user_id = self.users_table.returnCellsWhere('id', matches)[0]
        return user_id

    @property
    def valid_user(self):
        all_users = self.users_table.returnColumn('username')
        if self.user_name in all_users:
            return True
        else:
            return False

    @property
    def admin(self):
        if self.valid_user:
            matches = ('id', self.id)
            user_type = self.users_table.returnCellsWhere('user_type', matches)[0]
            if user_type == 'admin':
                return True
            else:
                return False

    @property
    def applications(self):
        # print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
        matches = ('id_users', self.id)
        user_apps = self.user_apps_table.returnCellsWhere('app_name', matches)
        return list(user_apps)

    @property
    def hashed_password(self):
        matches = ('username', self.user_name)
        hashed_password = self.users_table.returnCellsWhere('password', matches)[0]
        return hashed_password

    # @property
    # def masini(self):
    #     # print('Module: {}, Class: {}, Def: {}, Caller: {}'.format(__name__, __class__, sys._getframe().f_code.co_name, sys._getframe().f_back.f_code.co_name))
    #     masini = {}
    #     masini = []
    #     matches = ('user_id', self.id)
    #     cars_rows = self.all_cars_table.returnRowsWhere(matches)
    #     if cars_rows:
    #         for row in cars_rows:
    #             indx_brand = self.all_cars_table.columnsNames.index('brand')
    #             indx_model = self.all_cars_table.columnsNames.index('model')
    #             table_name = '{}_{}'.format(row[indx_brand], row[indx_model])
    #             # print(table_name)
    #             masini.append(table_name)
    #     return masini

    def verify_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def export_profile(self, output_dir=None, export_files=True):  # todo aici am ramas
        tim = datetime.strftime(datetime.now(), '%Y_%m_%d__%H_%M_%S')
        output_dir_name = '{}_{:09d}'.format(tim, self.id)
        if not output_dir:
            dir = os.path.dirname(__file__)
            output_dir = os.path.join(dir, r'static\backup_profile', '{:09d}'.format(self.id), output_dir_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
        print('starting backup')
        print('tables_dict', tables_dict)
        print('output_dir', output_dir)
        print('self.id', self.id)

        self.db.backup_profile_with_files(tables_dict, user_id=self.id, output_dir=output_dir,
                                          export_files=export_files)
        output_zip = os.path.join(os.path.dirname(output_dir), '{}.zip'.format(output_dir_name))
        zip_file = self.zip_profile_files(output_dir, output_zip)
        if os.path.exists(zip_file):
            shutil.rmtree(output_dir)
        print('finished backup')
        return output_dir

    def zip_profile_files(self, src_dir, output_file):
        relroot = os.path.abspath(os.path.join(src_dir, os.pardir))
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zip:
            for root, dirs, files in os.walk(src_dir):
                # add directory (needed for empty dirs)
                zip.write(root, os.path.relpath(root, relroot))
                for file in files:
                    filename = os.path.join(root, file)
                    if os.path.isfile(filename):  # regular files only
                        arcname = os.path.join(os.path.relpath(root, relroot), file)
                        zip.write(filename, arcname)
        return output_file

    def unzip_profile_files(self, src_file, output_dir):
        with zipfile.ZipFile(src_file, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        return output_dir

    def import_profile_without_files(self, sql_file):
        self.db.run_sql_file(sql_file)

    def erase_traces(self):
        for i in self.db.checkProcess():
            print(i)
        self.db.drop_table_list(list(tables_dict.keys()))


def main():
    script_start_time = time.time()
    selectedStartDate = datetime(2025, 1, 1, 0, 0, 0)
    selectedEndDate = datetime(2025, 1, 31, 0, 0, 0)

    # if compName == 'DESKTOP-5HHINGF':
    #     ini_file = r"D:\Python\MySQL\cheltuieli.ini"
    # else:
    #     ini_file = r"C:\_Development\Diverse\pypi\cfgm.ini"
    #     # ini_file = r"C:\_Development\Diverse\pypi\cfgmRN.ini"

    user = Users('radu', ini_users)
    print('****', user.admin)
    print('****', user.masini)
    print('****', user.cheltuieli)
    # print(user.delete_auto('aaaa_aaaa'))
    # if not user.masini:
    #     print('GGG')
    # else:
    #     for aa in user.masini:
    #         print(aa)
    # output_sql = r'C:\_Development\Diverse\pypi\radu\masina\src\masina\static\backup_profile\000000001\hyundai_ioniq.sql'
    # all_cars_ident = {'user_id': 1, 'id': 1}
    # masina_ident = {'id_users': 1, 'id_all_cars': 1}
    # tables = {'all_cars': all_cars_ident,
    #           'masina': masina_ident}

    # dire = r'C:\_Development\Diverse\pypi\radu\masina\src\masina\static\backup_profile\000000001\000000001'
    # sql_query = user.auto_db.return_sql_text(tables, export_files=dire)
    # print(sql_query)
    # user.export_car_sql(2, export_files=True)
    # profile = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\static\backup_profile\000000001\000000002\2025_06_05__16_22_12_000000002.zip"
    # user.import_profile_with_files(profile, import_files=True)

    scrip_end_time = time.time()
    duration = scrip_end_time - script_start_time
    duration = time.strftime("%H:%M:%S", time.gmtime(duration))
    print('run time: {}'.format(duration))


if __name__ == '__main__':
    main()
