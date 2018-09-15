import pickle
import json
import os
import threading
from threading import Thread
from datetime import datetime, timedelta
from base64 import b64encode
from uuid import uuid4
from config import Config
from operator import attrgetter
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc
from flask import render_template, flash, redirect, url_for, request, Flask
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.exceptions import HTTPException
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)

@app.before_first_request
def create_database():
    db.create_all()
    db.session.commit()

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/') 
@app.route('/index', methods=['GET', 'POST'])
def index():    
    return render_template("index.html", title='Home Page')
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', test="test asdasdasds")
    #return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username, current_user.email)
    if request.method == 'POST':
        if form.validate_on_submit():   
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your changes have been saved.')
            return redirect(url_for('edit_profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('edit_profile.html', title='Edit Profile', form=form)