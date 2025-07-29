import requests
import os
from pathlib import Path
from typing import Dict, List, Set
from io import BytesIO
from PIL import Image
import IPython.display as display
from ...forall import *
# Список для хранения динамически созданных функций отображения теории.

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Проверяет наличие интернет-соединения.
    """
    import socket
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False

THEORY = []

def list_subdirectories():
    """
    Получает список подкаталогов из репозитория GitHub, имена которых начинаются с 'NM'.
    """
    if not check_internet_connection():
        print("Ошибка: Для выполнения этой функции требуется интернет-соединение.")
        return []
    url = "https://api.github.com/repos/Ackrome/matplobblib/contents/pdfs"
    response = requests.get(url)
    if response.status_code == 200:
        contents = response.json()
        return [item['name'] for item in contents if item['type'] == 'dir' and item['name'].startswith('NM')]
    else:
        print(f"Ошибка при получении подпапок: {response.status_code}")
        return []

def get_png_files_from_subdir(subdir):
    """
    Получает список URL-адресов PNG-файлов из указанного подкаталога в репозитории GitHub.
    """
    if not check_internet_connection():
        print("Ошибка: Для выполнения этой функции требуется интернет-соединение.")
        return []
    url = f"https://api.github.com/repos/Ackrome/matplobblib/contents/pdfs/{subdir}"
    response = requests.get(url)
    if response.status_code == 200:
        contents = response.json()
        png_files = [item['name'] for item in contents if item['name'].endswith('.png')]
        return [f"https://raw.githubusercontent.com/Ackrome/matplobblib/master/pdfs/{subdir}/{file}" for file in png_files]
    else:
        print(f"Ошибка доступа к {subdir}: {response.status_code}")
        return []

def display_png_files_from_subdir(subdir):
    """
    Отображает PNG-файлы из указанного подкаталога.
    """
    if not check_internet_connection():
        print("Ошибка: Для выполнения этой функции требуется интернет-соединение.")
        return
    png_urls = get_png_files_from_subdir(subdir)
    for url in png_urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            display.display(img)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка загрузки {url}: {e}")

# Динамическое создание функций для каждого подкаталога
def create_subdir_function(subdir):
    """
    Динамически создает функцию для отображения PNG-файлов из заданного подкаталога.
    Функция именуется display_{subdir}.
    """
    global THEORY
    # Динамическое определение функции
    def display_function():
        """
        Автоматически сгенерированная функция для отображения PNG-файлов.
        """
        display_png_files_from_subdir(subdir)
    
    # Динамическое присвоение имени функции
    display_function.__name__ = f"display_{subdir}"
    
    # Добавление описательной строки документации
    display_function.__doc__ = (
        f"Вывести все страницы из файла с теорией '{subdir.replace('_','-')}'.\n"
        f"Эта функция сгенерирована автоматически из файла '{subdir.replace('_','-')+'.pdf'}' "
        f"из внутрибиблиотечного каталога файлов с теорией."
    )
    
    # Добавление функции в глобальное пространство имен
    globals()[display_function.__name__] = display_function
    THEORY.append(display_function)

# Динамическое получение списка подкаталогов
subdirs = list_subdirectories()
# Динамическое создание функций для каждого подкаталога
for subdir in subdirs:
    create_subdir_function(subdir)
    

import os
from pathlib import Path
from typing import Dict, List, Set


def group_html_files_by_package_data_dirs(
    package_data_config: Dict[str, List[str]],
    project_root_dir: str = "."
) -> Dict[str, List[str]]:
    """
    Составляет словарь HTML-файлов, сгруппированных по директориям,
    указанным в конфигурации типа package_data.

    Ключи словаря - это относительные пути к директориям, как они указаны
    в шаблонах glob из package_data (часть шаблона до имени файла/wildcard).
    Значения - отсортированные списки имен HTML-файлов в этих директориях.

    Args:
        package_data_config: Словарь, аналогичный `package_data` в setup.py.
                             Ключи - имена пакетов (строки).
                             Значения - списки строк с glob-шаблонами файлов,
                             относительно директории соответствующего пакета.
        project_root_dir: Корневая директория проекта, относительно которой
                          расположены директории пакетов. По умолчанию ".".

    Returns:
        Словарь, где ключи - это строки путей к директориям из шаблонов,
        а значения - списки имен HTML-файлов.
    """
    output_dict: Dict[str, Set[str]] = {}
    resolved_project_root = Path(project_root_dir).resolve()

    for package_name, patterns_list in package_data_config.items():
        package_actual_root = resolved_project_root / package_name

        # Проверяем, существует ли директория пакета
        if not package_actual_root.is_dir():
            # Можно добавить предупреждение, если нужно
            print(f"Предупреждение: Директория пакета '{package_actual_root}' не найдена.")
            continue

        for pattern_glob_str in patterns_list:
            # Ключ словаря - это родительская директория из строки шаблона
            # Например, для 'data/htmls/*.html', ключ будет 'data/htmls'
            # Для '*.html', ключ будет '.'
            
            key_dir_from_pattern = str(Path(pattern_glob_str).parent)
            
            # Ищем файлы, используя glob относительно директории пакета
            # Path.glob(pattern) ищет относительно пути, на котором он вызван
            for found_file_path in package_actual_root.glob(pattern_glob_str):
                if found_file_path.is_file() and found_file_path.suffix.lower() == '.html':
                    if key_dir_from_pattern not in output_dict:
                        output_dict[key_dir_from_pattern] = set()
                    output_dict[key_dir_from_pattern].add(found_file_path.name)

    # Преобразуем множества в отсортированные списки для консистентности
    final_result: Dict[str, List[str]] = {
        key: sorted(list(filenames)) for key, filenames in output_dict.items()
    }
    return final_result

package_data={
        'matplobblib': ['matplobblib/nm/theory/htmls/*.html'],
    }

print(group_html_files_by_package_data_dirs(package_data))