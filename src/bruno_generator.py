import os
import sys
import json
import urllib.parse
import pyperclip
import ctypes
import yaml
import urllib.parse
from pathlib import Path  # Современный стандарт работы с путями (объектно-ориентированный)

def alert(msg, is_error=False):
    """
    Выводит системное окно Windows (MessageBox).
    Полезно для GUI-приложений без консоли (--noconsole).
    """
    # 16 - иконка ошибки (Red Cross), 64 - иконка информации (Blue i)
    style = 16 if is_error else 64
    # Вызов нативного Windows API через ctypes
    ctypes.windll.user32.MessageBoxW(0, str(msg), "Bruno Link Generator", style)

def find_collection_root(yml_path):
    """
    Ищет корень коллекции, поднимаясь от файла вверх по дереву папок.
    Аналог поиска .git папки.
    """
    # resolve() делает путь абсолютным, Path превращает строку в объект
    current = Path(yml_path).resolve()
    
    # Если на вход пришел файл, берем его родительскую папку
    if current.is_file():
        current = current.parent
        
    # Цикл "пока не дошли до корня диска"
    while current != current.parent:
        # Проверяем наличие маркеров коллекции Bruno разных версий
        if (current / "bruno.json").exists():
            return current, "json"
        if (current / "opencollection.yml").exists():
            return current, "yaml"
        # Поднимаемся на уровень выше (cd ..)
        current = current.parent
        
    return None, None

def get_collection_info(root_path, file_type):
    """
    Читает файл конфигурации и извлекает имя коллекции и URL репозитория.
    """
    try:
        # Блок 'with' гарантирует закрытие файла после чтения (авто-dispose)
        if file_type == "json":
            with open(root_path / "bruno.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            name = data.get('name')
        else:
            with open(root_path / "opencollection.yml", 'r', encoding='utf-8') as f:
                # safe_load защищает от выполнения произвольного кода из YAML
                data = yaml.safe_load(f)
            # .get() безопаснее, чем обращение по индексу data['info'], так как не падает, если ключа нет
            name = data.get('info', {}).get('name')
        
        # Если в конфиге имя не задано, используем название папки (fallback)
        if not name:
            name = root_path.name

        # Пытаемся найти URL репозитория в разных возможных местах
        # Оператор 'or' в Python вернет первое непустое (True) значение
        url = data.get('git', {}).get('url') or \
              data.get('repository', {}).get('url') or \
              data.get('extensions', {}).get('bruno', {}).get('repo_url')
            
        return name, url
    except Exception as e:
        # Если файл поврежден или нет прав доступа
        alert(f"Ошибка при чтении конфигурации: {e}", True)
        return root_path.name, None

def make_link(yml_path, root_path, collection_name, repo_url):
    """
    Собирает финальную строку ссылки brunogs://
    """
    # Вычисляем относительный путь от корня коллекции до выбранного файла
    rel_path = Path(yml_path).relative_to(root_path)
    
    # as_posix() превращает системные слеши (\) в универсальные (/) для URL
    rel_path_str = rel_path.as_posix()
    
    # Экранируем спецсимволы в пути (пробелы, кириллицу и т.д.)
    encoded_path = urllib.parse.quote(rel_path_str)
    
    # Гарантируем, что путь начинается со слеша
    if not encoded_path.startswith('/'):
        encoded_path = '/' + encoded_path
        
    # Формируем 'хост' части ссылки. Приоритет у URL репозитория.
    host = repo_url if repo_url else collection_name
    
    # Очищаем хост от протоколов, чтобы получить чистый адрес/имя
    host = host.replace('https://', '').replace('http://', '').strip('/')

    host_encoded = urllib.parse.quote(host)
        
    return f"brunogs://{host_encoded}?path={encoded_path}"

# Точка входа в скрипт
if __name__ == "__main__":
    # sys.argv - это массив аргументов командной строки.
    # argv[0] - это путь к самому скрипту/exe, argv[1] - первый переданный параметр.
    if len(sys.argv) < 2:
        alert("Файл не передан! Используйте контекстное меню проводника.", True)
        sys.exit(1)

    target_file = sys.argv[1]
    
    try:
        # 1. Ищем корень проекта
        root, f_type = find_collection_root(target_file)
        
        if not root:
            alert("Файл не является частью коллекции Bruno (не найден конфиг).", True)
            sys.exit(1)
            
        # 2. Собираем данные из конфига
        col_name, url = get_collection_info(root, f_type)
        
        # 3. Генерируем ссылку
        link = make_link(target_file, root, col_name, url)

        # 4. Копируем результат в буфер обмена Windows
        pyperclip.copy(link)
        
        # Если нужно визуальное подтверждение, можно раскомментировать:
        # alert(f"Ссылка скопирована в буфер!\n{link}")
        
    except Exception as e:
        # Глобальный перехват ошибок, чтобы EXE не закрывался "молча"
        alert(f"Критический сбой программы: {e}", True)