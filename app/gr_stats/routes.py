from flask import flash, request, jsonify, current_app
from app.gr_stats import bp
from app.gr_stats.get_gr_stats import user_report, company_summary, summarize_manager_report
from flask_login import login_required
from app.models import User, Manager
from flaskthreads import ThreadPoolWithAppContextExecutor

#  g91j886vzuel4k4izp0wd9m31pe9tw2h


@bp.route('/get_gr_user_activity', methods=['POST'])
@login_required
def get_gr_user_activity():
    dicData = request.form.to_dict()
    idi = dicData['id']
    if dicData['email'] != '':
        idi = User.query.filter_by(email = dicData['email'].strip(' ')).first_or_404().id
    user_activity_report = user_report(idi)
    return jsonify({'days_since_last_login': user_activity_report[0],\
     'days_since_last_contact_add': user_activity_report[1], \
     'days_since_last_broadcast': user_activity_report[2]})


@bp.route('/get_company_summary', methods=['POST'])
@login_required
def get_company_summary():
    dicData = request.form.to_dict()
    company_results = company_summary(dicData['crypto'])

    return jsonify({'days_since_last_login': company_results[0],\
     'days_since_last_contact_add': company_results[1], \
     'days_since_last_broadcast': company_results[2]})


@bp.route('/get_manager_summary', methods=['POST'])
@login_required
def get_manager_summary():
    mname = request.form.to_dict()['mname']
    current_app.manager_cryptos = [company.crypto for company in Manager.query.filter_by(mname=mname).first().companies.all()]
    with ThreadPoolWithAppContextExecutor(max_workers=4) as pool:
        futures = [pool.submit(company_summary,crypto) for crypto in current_app.manager_cryptos]
        manager_report = [future.result() for future in futures]
    
    manager_summary = summarize_manager_report(manager_report)
    print(manager_summary)
    return jsonify({'total_customers_count': manager_summary[0],\
     'active_customers_count': manager_summary[1], \
     'atrisk_customers_count': manager_summary[2]})

