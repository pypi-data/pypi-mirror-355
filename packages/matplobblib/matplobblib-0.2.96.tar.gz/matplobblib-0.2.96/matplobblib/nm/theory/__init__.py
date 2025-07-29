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
    
import importlib.resources
import pathlib
from typing import List, Dict, Set

def get_all_packaged_html_files(package_data_config: Dict[str, List[str]]) -> List[str]:
    """
    Составляет список имен всех уникальных HTML-файлов, найденных во всех директориях,
    указанных в конфигурации типа package_data, доступных изнутри установленного пакета.
    Возвращаются только имена файлов, а не полные пути.

    Args:
        package_data_config: Словарь, аналогичный параметру `package_data` в setup.py.
                             Ключи - это имена пакетов верхнего уровня (например, 'matplobblib').
                             Значения - это списки строк с путями относительно корня пакета,
                             обычно заканчивающиеся маской, такой как '*.html'.
                             Пример: {'matplobblib': ['matplobblib/nm/theory/htmls/*.html', 'other_data/*.html']}

    Returns:
        Отсортированный список уникальных имен HTML-файлов (например, ['page1.html', 'index.html']).
    """
    all_html_file_names: Set[str] = set()

    for package_name, path_patterns in package_data_config.items():
        try:
            # Получаем Traversable для корня пакета
            package_root_traversable = importlib.resources.files(package_name)
        except (ModuleNotFoundError, TypeError):
            # Пакет не найден или не является валидным контейнером ресурсов
            # Можно добавить логирование предупреждения, если необходимо
            print(f"Предупреждение: Пакет '{package_name}' не найден или не является корректным контейнером ресурсов.")
            continue

        for pattern_str in path_patterns:
            # Нормализуем разделители пути для pathlib
            normalized_pattern = pattern_str.replace("\\", r'/')
            
            # Получаем директорию из шаблона пути
            # Например, для 'sub_pkg/data/htmls/*.html', parent_dir_str будет 'sub_pkg/data/htmls'
            # Для '*.html', parent_dir_str будет '.'
            path_obj_for_parent = pathlib.Path(normalized_pattern)
            parent_dir_str = str(path_obj_for_parent.parent)

            current_traversable = package_root_traversable
            is_valid_target_dir = True

            # Переходим к целевой директории, если это не корень пакета ('.')
            if parent_dir_str != '.':
                path_segments = parent_dir_str.split('/')
                for segment in path_segments:
                    if not segment: # Пропускаем пустые сегменты (маловероятно при корректных путях)
                        continue
                    try:
                        current_traversable = current_traversable.joinpath(segment)
                        # Важно проверять is_dir() после каждого шага, если это промежуточный сегмент
                        if not current_traversable.is_dir():
                            is_valid_target_dir = False
                            break
                    except (FileNotFoundError, NotADirectoryError):
                        is_valid_target_dir = False
                        break
            
            if not is_valid_target_dir or not current_traversable.is_dir():
                # Целевая директория не найдена или не является директорией
                print(f"Предупреждение: Директория '{parent_dir_str}' не найдена или не является директорией в пакете '{package_name}'.")
                continue

            # Теперь ищем .html файлы в этой директории (current_traversable)
            try:
                for item in current_traversable.iterdir():
                    # item.name содержит имя файла (например, "page.html")
                    if item.is_file() and item.name.lower().endswith('.html'):
                        all_html_file_names.add(item.name)
            except Exception:
                # Обработка возможных ошибок при итерации по директории
                print(f"Предупреждение: Ошибка при итерации по директории в пакете '{package_name}', путь '{parent_dir_str}'.")
                pass
                
    return sorted(list(all_html_file_names))



package_data={
        'matplobblib': ['nm/theory/htmls/*.html'],
    }

print(get_all_packaged_html_files(package_data))