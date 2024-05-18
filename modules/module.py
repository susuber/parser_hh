import json
import os
import sys
import time
from typing import Union
import argparse
import requests
import yaml
from colorama import Fore, Style


def read_config(path: str) -> dict:
    """"Чтение конфигураций
    
    Keyword arguments:
    path -- Путь до файла
    Return: конфигурации
    """
    
    with open(path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def response(arg: Union[dict, str], page=0) -> dict:
    """Получение данных с сайта
    
    Keyword arguments:
    arg -- параметры запроса
    page -- страница запроса
    Return: словарь результатов
    """
    
    if isinstance(arg, dict):        
        params = {
            'text': f'{arg["vacancy"]} {arg["place"]}',
            'page': page,
            'per_page': arg['per_page'],
        }
        return requests.get(arg['url'], params=params).json()
    elif isinstance(arg, str):
        return requests.get(arg).json()
    else:
        print(f'{Fore.RED}Error: {arg}{Style.RESET_ALL}')


def parsing(data: dict, method: str) -> Union[list, str]:
    if method == 'url':
        return data['url']

    if method == 'vacancy':
        result = {
            'salary': 0,
            'skills': []
        }
        if data['salary']:
            if isinstance(data['salary']['from'], int) and isinstance(data['salary']['to'], int):
                result['salary'] = (data['salary']['from'] + data['salary']['to']) / 2
            elif isinstance(data['salary']['from'], int):
                result['salary'] = data['salary']['from']
            elif isinstance(data['salary']['to'], int):
                result['salary'] = data['salary']['to']
            else:
                result['salary'] = None
        else:
            result['salary'] = None
        
        if 'currency' in data.keys():
            result['currency'] = data['currency']

        if data['key_skills']:
            for skill in data['key_skills']:
                result['skills'].append(skill['name'])
        else:
            result['skills'] = None
    return result


def info_add_result(info: dict, result: dict) -> dict:
    if 'salary' in info.keys():
        if not result['salary']:
            result['salary'] = info['salary']
            result['num_salary'] += 1
        else:
            if 'currency' in info.keys():
                if info['currency'] != 'RUR':
                    info['salary'] = info['salary'] / exchange_rate['rates'][info['currency']]
            if info['salary']:
                result['salary'] = (result['salary'] + info['salary']) / 2
            result['num_salary'] += 1

    if info['skills']:
        for skill in info['skills']:
            if skill in result['skills'].keys():
                result['skills'][skill] += 1
            else:
                result['skills'][skill] = 1
    
    return result
