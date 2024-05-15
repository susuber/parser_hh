import json
import os
import sys
import time
from typing import Union
import argparse
import requests
import yaml
from colorama import Fore, Style
from tqdm import tqdm


def main():
    os.system('cls||clear')
    print('Получение курсов валют...    ', end='')
    exchange_rate = requests.get('https://www.cbr-xml-daily.ru/latest.js').json()
    print(f'{Fore.GREEN}OK{Style.RESET_ALL}')

    result = {
        'number': 0,
        'salary': 0,
        'num_salary': 0,
        'skills': {},
    }

    params = load_params_cmd()
    conf = read_config(params['path'])
    for i in range(0, params['pages']):
        print('Получение информации...      ', end='')
        vacancies = response(arg=conf, page=i)
        print(f'{Fore.GREEN}OK{Style.RESET_ALL}')

        print('Обработка списка вакансий...    ')
        for vacancy in tqdm(vacancies['items']):
            time.sleep(1)
            result['number'] += 1
            vacancy = response(parsing(data=vacancy, method='url'))
            information = parsing(data=vacancy, method='vacancy')

            result = info_add_result(info=information, result=result)
            
    result['skills'] = dict(sorted(result['skills'].items(), key=lambda item: item[1], reverse=True))
    print_result(result)
    print()
    save_to_file(result)


def info_add_result(info: dict, result: dict) -> dict:
    if 'salary' in info.keys():
        if result['salary'] == 0:
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


def print_result(result: dict):
    os.system('cls||clear')
    print(f'{Fore.LIGHTGREEN_EX}Результат анализа {result["number"]} записей{Style.RESET_ALL}')
    print(f'Средняя зарабтная плота:                     {Fore.GREEN} {result["salary"]}{Style.RESET_ALL}')
    print(f'Процент вакансий с заработной платой         {Fore.GREEN} {result["num_salary"] / result["number"]}{Style.RESET_ALL}')
    sum_skills = sum(result['skills'].values())
    print(f'Требуемые навыки: {Fore.GREEN}абсолютное значение {Fore.RED}относительно всех навыков {Fore.BLUE}относительно уникальных{Style.RESET_ALL}')
    for skill in result['skills'].items():
        print(f'        {skill[0]}: {Fore.GREEN}{skill[1]} {Fore.RED}{round((skill[1] / sum_skills) * 100, 2)} {Fore.YELLOW}{round((skill[1] / len(result["skills"].keys())) * 100, 2)}{Style.RESET_ALL}')    


def save_to_file(result: dict):
    print('Сохранение отчета...    ', end='')
    with open(f"result.json", "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)
    print(f'{Fore.GREEN}OK{Style.RESET_ALL}')


def read_config(path: str) -> dict:
    with open(path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def response(arg: Union[dict, str], page=0) -> dict:
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


def create_parser() -> object:
    """
    Функция сбора параметров из shell
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pages', default=1)
    parser.add_argument('-c', '--config', default='etc/config.yml')
    return parser


def load_params_cmd() -> dict:
    """
    Функция преобразования параметров из shell в словарь
    """
    params = {}

    parser_cmd = create_parser()
    arguments = parser_cmd.parse_args(sys.argv[1:])

    params['pages'] = int(arguments.pages)
    params['path'] = arguments.config
    return params


if __name__ == '__main__':
    main()
