# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, request, abort
from app import db
from flask import current_app
from werkzeug.urls import url_parse
from flask_login import current_user, login_required

from app.models import Manager, User, Company

from datetime import datetime

from app.main.forms import EditProfileForm,CompanyForm,UserForm
from app.main import bp
from flask import g
from app.main.forms import SearchForm


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    companies, total = Company.search(g.search_form.q.data, page,
                               current_app.config['COMPANIES_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['COMPANIES_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), companies=companies,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/delete_company', methods=['GET','POST'])
@login_required
def delete_company():

    company_crypto = request.form['crypto']
    company = Company.query.filter_by(crypto=company_crypto).first_or_404()
    if Manager.query.filter_by(id = company.account_manager_id).first() != current_user:
        flash("It's not your company!")
        abort(403)
    company.delete_myself()

    return '<200>'

@bp.route('/delete_user', methods=['GET','POST'])
@login_required
def delete_user():
    user_id = request.form['id']
    user = User.query.filter_by(id=user_id).first_or_404()
    company = Company.query.filter_by(id=user.company_id).first_or_404()
    if Manager.query.filter_by(id = company.account_manager_id).first() != current_user:
        flash("It's not your company!")
        abort(403)
    user.delete_myself()

    return '<200>'

@bp.route('/follow/<mname>')
@login_required
def follow(mname):
    manager = Manager.query.filter_by(mname=mname).first()
    if manager is None:
        flash('Manager {} not found.'.format(mname))
        return redirect(url_for('main.index'))
    if manager == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.manager', manager=manager))
    current_user.follow(manager)
    db.session.commit()
    flash('You are following {}!'.format(mname))
    return redirect(url_for('main.manager', mname=mname))

@bp.route('/unfollow/<mname>')
@login_required
def unfollow(mname):
    manager = Manager.query.filter_by(mname=mname).first()
    if manager is None:
        flash('Manager {} not found.'.format(mname))
        return redirect(url_for('main.index'))
    if manager == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.manager', mname=mname))
    current_user.unfollow(manager)
    db.session.commit()
    flash('You are not following {}.'.format(mname))
    return redirect(url_for('main.manager', mname=mname))

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        # g.search_form = SearchForm()

@bp.route('/manager/<mname>', methods=['GET', 'POST'])
@login_required
def manager(mname):
    form = CompanyForm()
    
    if form.validate_on_submit():
        company = Company(crypto=form.crypto.data, manager=current_user)
        db.session.add(company)
        db.session.commit()
        flash('Your company is now live!')
        return redirect(url_for('main.manager', mname=mname))
    manager = Manager.query.filter_by(email=mname.lower()+"@getresponse.com").first_or_404()
    page = request.args.get('page', 1, type=int)
    
    if manager == current_user:
        companies = manager.followed_companies().paginate(
            page, current_app.config['COMPANIES_PER_PAGE'], False)
        next_url = url_for('main.index', page=companies.next_num) \
            if companies.has_next else None
        prev_url = url_for('main.index', page=companies.prev_num) \
            if companies.has_prev else None  
        return render_template('manager.html', title = mname , manager=manager, companies=companies.items, form=form, next_url=next_url, prev_url=prev_url )
    else:
        companies = manager.companies.all()
        return render_template('manager.html', title = mname , manager=manager, companies=companies)



@bp.route('/crypto/<crp>', methods=['GET', 'POST'])
@login_required
def crypto(crp):
    form = UserForm()
    manager = Manager.query.filter(Manager.companies.any(crypto=crp)).first()
    if form.validate_on_submit():
        company = Company.query.filter_by(crypto=crp).first()
        user = User(email=form.email.data, api_key = form.api_key.data, company=company)
        db.session.add(user)
        db.session.commit()
        
        flash('You just have add new user for {}'.format(crp))
        
        return redirect(url_for('main.crypto', crp=crp))

    
    current_company = Company.query.filter_by(crypto=crp).first()
    users = current_company.customer_users.all()
    page = request.args.get('page', 1, type=int)

    return render_template('crypto.html', title = crp, users=users, form=form if manager == current_user else None)

@bp.route('/managers')
@login_required
def managers():
    page = request.args.get('page', 1, type=int)
    managers = Manager.query.all()
    return render_template("managers.html", title="Managers Page", managers=managers)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    companies = Company.query.paginate(
        page, current_app.config['COMPANIES_PER_PAGE'], False)
    next_url = url_for('main.index', page=companies.next_num) \
        if companies.has_next else None
    prev_url = url_for('main.index', page=companies.prev_num) \
        if companies.has_prev else None
    return render_template("index.html", title='Home Page', companies=companies.items, next_url=next_url, prev_url=prev_url)



