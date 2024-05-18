import json
import os
import sys
import time
from typing import Union
import requests
import yaml
from modules.module import read_config, response, parsing, info_add_result
from random import choice

#from werkzeug.middleware.dispatcher import DispatcherMiddleware
#from prometheus_client import make_wsgi_app

from flask import Flask, render_template, session, request, flash, redirect, url_for


app = Flask(__name__)

#https://prometheus.github.io/client_python/exporting/http/flask/
#app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
#    '/metrics': make_wsgi_app()
#})

menu = [
    {'name': 'Главная', 'url': '/'},
    {'name': 'Поиск', 'url': '/search'},
    {'name': 'Случайный выбор', 'url': '/random'},
    {'name': 'Контакты', 'url': '/contacts'},
]

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

config = read_config('etc/config.yml')
result = {
    'number': 0,
    'salary': 0,
    'num_salary': 0,
    'skills': {},
                }


@app.route('/')
@app.route('/index')
def start_page():
    return render_template('index.html',
                           title='Привет, это поиск по hh.ru',
                           menu=menu)


@app.route('/contacts')
def contacts_page():
    return render_template('contacts.html',
                           title='Страница в разработке',
                           menu=menu)


@app.route('/search', methods=['GET', 'POST'])
def search_page():
    if request.method == "POST":
        config['vacancy'] = request.form['vacancy']
        config['place'] = request.form['place']
        config['pages'] = request.form['pages']

        if config['pages'].isdigit():
            if int(config['pages']) <= 3:
                flash("Обработка началась, по окончанию Вас перенаправит на страницу отчета", category='success')
                return redirect(url_for('page_result'), 301)
            else:
                flash("Число страниц не более 3", category='error')
        else:
            flash("Число страниц должно быть цифрой", category='error')

    return render_template('search.html', title="Поиск", menu=menu, config=config)


@app.route('/random', methods=['GET', 'POST'])
def processing():
    if request.method == "POST":
        config['pages'] = 1
        return redirect(url_for('page_result'), 301)
    else:
        with open(config['random_place'], 'r') as file:
            random_place = file.read()
        random_place = random_place.split('\n')
        config['place'] = choice(random_place)

        with open(config['random_vacancy'], 'r') as file:
            random_vacancy = file.read()
        random_vacancy = random_vacancy.split('\n')
        config['vacancy'] = choice(random_vacancy)

    return render_template('random.html', menu=menu, random_vacancy=config['vacancy'], random_place=config['place'], title='Случайный выбор')


@app.route('/result')
def page_result():
    global result
    exchange_rate = requests.get('https://www.cbr-xml-daily.ru/latest.js').json()
    result = {
        'number': 0,
        'salary': 0,
        'num_salary': 0,
        'skills': {},
    }
    for i in range(0, int(config['pages'])):
        vacancies = response(arg=config, page=i)
        for vacancy in vacancies['items']:
            time.sleep(0.5)
            result['number'] += 1
            vacancy = response(parsing(data=vacancy, method='url'))
            information = parsing(data=vacancy, method='vacancy')
            result = info_add_result(info=information, result=result)
        result['skills'] = dict(sorted(result['skills'].items(), key=lambda item: item[1], reverse=True))
        sum_skills = sum(result['skills'].values())
    return render_template('result.html', title="Результат", menu=menu, result=result, sum_skills=sum_skills, all_skills = len(result["skills"].keys()))


@app.errorhandler(404)
def page_not_fount(error):
    return render_template('page404.html', menu=menu), 404


@app.errorhandler(500)
def page_not_fount(error):
    return render_template('page500.html', title="Ошибка сервера", menu=menu), 500


if __name__ == '__main__':
  app.run(debug=True)