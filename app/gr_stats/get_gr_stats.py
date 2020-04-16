import requests
import time
import datetime
from time import mktime
from concurrent.futures import ThreadPoolExecutor
from app.models import User, Company


ROOT = 'https://api3.getresponse360.pl/v3'
NEWLETTERS = '/newsletters'
LOGIN_HISTORY = '/accounts/login-history'
CONTACTS = '/contacts'


def run_function(function_headers):
    return function_headers[0](function_headers[1])

def get_last_big_broadcast_id(json):
    for broadcast in json:
        if int(broadcast['sendMetrics']['sent']) > 200:
            return broadcast['sendOn']
    return -1

def do_broadcast_history(headers):
    url = ROOT + NEWLETTERS+'/?sort[createdOn]=DESC&query[type]=broadcast'
    r = requests.get(url, headers=headers)
    # TODO try catch
    last_big_broadcast_sendOn = get_last_big_broadcast_id(r.json())
    if type(last_big_broadcast_sendOn) == int:
        return str(-1)
    return find_time_span_since_now(last_big_broadcast_sendOn)

def do_login_history(headers):
    url = ROOT + LOGIN_HISTORY
    r = requests.get(url, headers=headers)
    return find_time_span_since_now(r.json()[0]['loginTime'])


def do_add_contact_history(headers):
    url = ROOT + CONTACTS + '?sort[createdOn]=DESC&perPage=1'
    r = requests.get(url, headers=headers)
    return find_time_span_since_now(r.json()[0]['createdOn'])


def find_time_span_since_now(date_raw):
    date_list = [int(x) for x in date_raw[:10].split('-')]
    date = datetime.datetime(date_list[0],date_list[1],date_list[2])
    current_time2 = datetime.datetime.now()
    return str((current_time2 - date).days)

def user_report(id):
    # with app.app_context():
    key = User.query.filter_by(id=id).first().api_key
    headers = {"X-Auth-Token":"api-key {}".format(key)}
    # since_last_broadcast = do_broadcast_history()

    '''
    хаха короче
    многопоточно запускает функция run_function
    она на вход принимает массив
    первый элемент массива функция, а второй заголовки
    '''
    with ThreadPoolExecutor() as executor:
        results = [executor.submit(run_function, function_headers) for function_headers in [[do_login_history,headers],[do_add_contact_history,headers],[do_broadcast_history,headers]]]
    
    return [thread.result() for thread in results] 

def company_summary(crypto):
    current_company = Company.query.filter_by(crypto=crypto).first()

    users = current_company.customer_users.all()

    # with ThreadPoolExecutor() as executor:
    #     results = [executor.submit(user_report, user.id) for user in users]
    users_reports = []
    for user in users:
        users_reports.append(user_report(user.id))

    # users_reports = [thread.result() for thread in results]
    return summarize_users_report(users_reports) 


def summarize_users_report(users_reports):
    min_login = min([ int(report[0]) for report in users_reports])
    min_import = min([ int(report[1]) for report in users_reports])
    min_broad = min([ int(report[2]) for report in users_reports])
    return min_login,min_import,min_broad

def summarize_manager_report(manager_report):
    total = len(manager_report)
    active = len([login for login in manager_report if login[0]<7])
    atrisk = total - active
    return total,active,atrisk
