import sys
import os
import subprocess
import urllib.parse
import urllib.request
import time
import tempfile
import winreg
import shutil
from typing import Optional
from playwright.sync_api import sync_playwright, Page

# ---------- 1. Логирование (по умолчанию выключено) ----------
LOGGING_ENABLED = False

def get_log_path():
    if getattr(sys, 'frozen', False):
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        log_dir = os.path.join(appdata, 'BrunoClicker')
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, 'bruno_debug.log')
    except:
        return os.path.join(tempfile.gettempdir(), 'bruno_debug.log')

LOG_FILE = get_log_path()

def log(message: str):
    if not LOGGING_ENABLED:
        return
    timestamp = time.strftime('%H:%M:%S')
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        sys.stderr.write(f"[{timestamp}] {message} (file error: {e})\n")

# ---------- 2. Парсинг ссылки ----------
def parse_request_name(raw_url: str) -> Optional[str]:
    log(f"Сырой вход: {raw_url}")
    decoded = urllib.parse.unquote(raw_url)
    log(f"Декодировано: {decoded}")

    clean = decoded.replace("brunogs://", "").replace("bruno://", "")
    if "https//" in clean:
        clean = clean.replace("https//", "https://")
    if "http//" in clean:
        clean = clean.replace("http//", "http://")
    if not clean.startswith(("http://", "https://")):
        clean = "http://" + clean

    if "?" not in clean and "path=" in clean:
        clean = clean.replace("path=", "?path=")

    parsed = urllib.parse.urlparse(clean)
    params = urllib.parse.parse_qs(parsed.query)
    path_list = params.get('path', [''])
    path_param = path_list[0] if path_list else None

    if not path_param:
        log("Ошибка: параметр 'path' не найден")
        return None

    request_name = os.path.basename(path_param).replace('.yml', '').replace('.bru', '')
    log(f"Имя запроса: {request_name}")
    return request_name

def get_bruno_path_from_registry():
    """Читает путь к Bruno.exe из реестра (HKCU или HKLM)"""
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            key = winreg.OpenKey(hive, r"Software\BrunoClicker")
            path, _ = winreg.QueryValueEx(key, "BrunoPath")
            winreg.CloseKey(key)
            if os.path.exists(path):
                return path
        except:
            pass
    return None

def get_bruno_path():
    # 1. Аргумент командной строки --bruno-path или -b
    for i, arg in enumerate(sys.argv):
        if arg in ('--bruno-path', '-b') and i+1 < len(sys.argv):
            path = sys.argv[i+1]
            if os.path.exists(path):
                log(f"Используется путь к Bruno из аргумента: {path}")
                return path
            else:
                log(f"Предупреждение: указанный путь {path} не существует")

    # 2. Путь из реестра
    path = get_bruno_path_from_registry()
    if path:
        log(f"Используется путь к Bruno из реестра: {path}")
        return path

    # 3. Путь по умолчанию
    if os.path.exists(DEFAULT_BRUNO_PATH):
        log(f"Используется путь по умолчанию: {DEFAULT_BRUNO_PATH}")
        return DEFAULT_BRUNO_PATH

    # 4. Альтернативные пути (Program Files (x86))
    alt_path = r"C:\Program Files (x86)\Bruno\Bruno.exe"
    if os.path.exists(alt_path):
        log(f"Найден Bruno в альтернативной папке: {alt_path}")
        return alt_path

    # 5. Поиск в PATH
    found = shutil.which("Bruno.exe")
    if found:
        log(f"Найден Bruno через PATH: {found}")
        return found

    log(f"Bruno не найден! Будет использован путь по умолчанию: {DEFAULT_BRUNO_PATH}")
    return DEFAULT_BRUNO_PATH

# ---------- 3. Управление процессом Bruno ----------
DEFAULT_BRUNO_PATH = r"C:\Program Files\Bruno\Bruno.exe"
DEBUG_PORT = "9222"
CDP_HOST = "127.0.0.1"

url = f"http://{CDP_HOST}:{DEBUG_PORT}"

def kill_bruno_processes():
    try:
        result = subprocess.run(['taskkill', '/f', '/im', 'Bruno.exe'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log("Все процессы Bruno успешно завершены")
        else:
            log(f"Процессы Bruno не найдены или не удалось завершить: {result.stderr.strip()}")
        time.sleep(1)
    except Exception as e:
        log(f"Ошибка при завершении Bruno: {e}")

def is_cdp_port_ready(host: str, port: str) -> bool:
    try:
        url = f"http://{host}:{port}/json/version"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except:
        return False

def wait_for_cdp(host: str = CDP_HOST, port: str = DEBUG_PORT, timeout: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if is_cdp_port_ready(host, port):
            return True
        time.sleep(0.5)
    return False

def ensure_bruno_running() -> bool:
    bruno_path = get_bruno_path()
    kill_bruno_processes()
    log(f"Запуск Bruno из {bruno_path} с портом отладки...")
    subprocess.Popen([bruno_path, f"--remote-debugging-port={DEBUG_PORT}"])
    log(f"Ожидание готовности порта {DEBUG_PORT}...")
    if not wait_for_cdp(CDP_HOST, DEBUG_PORT, timeout=20):
        log("Не удалось дождаться готовности CDP-порта")
        return False
    log("Порт готов")
    return True

# ---------- 4. Подключение Playwright ----------
def connect_to_bruno() -> Optional[Page]:
    try:
        playwright = sync_playwright().start()
        for attempt in range(3):
            try:
                browser = playwright.chromium.connect_over_cdp(url)
                break
            except Exception as e:
                log(f"Попытка {attempt+1} подключения не удалась: {e}")
                if attempt == 2:
                    raise
                time.sleep(2)
        if not browser.contexts:
            log("Нет контекстов браузера")
            return None
        pages = browser.contexts[0].pages
        if not pages:
            log("Нет открытых страниц")
            return None
        page = pages[0]
        page.bring_to_front()

        log("Подключено к странице Bruno")
        setattr(page, '_playwright', playwright)
        setattr(page, '_browser', browser)

        return page
    except Exception as e:
        log(f"Ошибка подключения: {e}")
        return None

def disconnect_from_bruno(page: Page):
    try:
        browser = getattr(page, '_browser', None)
        if browser:
            browser.close()

        pw = getattr(page, '_playwright', None)
        if pw:
            pw.stop()        

        log("Соединение закрыто")
    except Exception as e:
        log(f"Ошибка при закрытии: {e}")

# ---------- 5. Работа с коллекцией ----------
def select_main_collection(page: Page) -> bool:
    try:
        collection_selector = 'div#sidebar-collection-name:has-text("Main Collection")'
        collection_item = page.locator(collection_selector).first
        collection_item.wait_for(state="visible", timeout=5000)
        collection_item.click()
        log("Коллекция 'Main Collection' выбрана")
        time.sleep(0.5)
        return True
    except Exception as e:
        log(f"Не удалось выбрать коллекцию: {e}")
        return False

# ---------- 6. Поиск и клик ----------
def open_search_field(page: Page):
    search_input = page.locator('input#search')
    if search_input.is_visible():
        log("Поле поиска уже открыто")
        return search_input
    log("Ищем кнопку поиска (лупа)...")
    search_btn = page.locator('button[title="Search requests"]')
    search_btn.wait_for(state="visible", timeout=5000)
    search_btn.click()
    log("Кнопка поиска нажата")
    search_input.wait_for(state="visible", timeout=2000)
    return search_input

def type_search_query(page: Page, request_name: str):
    search_input = open_search_field(page)
    if search_input is None:
        raise Exception("Не удалось открыть поле поиска")
    search_input.focus()
    search_input.fill("")
    time.sleep(0.2)
    search_input.fill(request_name)
    search_input.press("Enter")
    log(f"Введён запрос: {request_name}")

def click_on_request(page: Page, request_name: str) -> bool:
    try:
        page.wait_for_selector(f'span.item-name:has-text("{request_name}")', timeout=3000)
        log("Результаты поиска появились")
    except:
        log("Предупреждение: результаты не появились вовремя, пробуем клик вслепую")
    selector = f'span.item-name[title="{request_name}"]'
    target = page.locator(selector).first
    try:
        target.wait_for(state="attached", timeout=5000)
        target.click(force=True, timeout=2000)
        log("Клик по запросу выполнен")
        return True
    except Exception as e:
        log(f"Не удалось кликнуть по точному title: {e}")
        try:
            page.locator(f'span.item-name:has-text("{request_name}")').first.click(force=True)
            log("Клик по тексту выполнен")
            return True
        except Exception as e2:
            log(f"Ошибка: не удалось кликнуть даже по тексту: {e2}")
            return False

def search_and_open_request(page: Page, request_name: str) -> bool:
    try:
        type_search_query(page, request_name)
        time.sleep(0.5)
        return click_on_request(page, request_name)
    except Exception as e:
        log(f"Ошибка при поиске/открытии: {e}")
        return False

# ---------- 7. Main ----------
def main():
    global LOGGING_ENABLED
    try:
        args = sys.argv[1:]
        url_arg = None
        for arg in args:
            if arg == '--log':
                LOGGING_ENABLED = True
            elif arg.startswith(('brunogs://', 'bruno://', 'https://', 'http://')):
                url_arg = arg
            elif arg.startswith('--'):
                pass
            else:
                if not url_arg:
                    url_arg = arg

        if not url_arg:
            log("Ошибка: ссылка не передана")
            return

        log(f"Логирование включено, URL: {url_arg}")
        request_name = parse_request_name(url_arg)
        if not request_name:
            return

        if not ensure_bruno_running():
            return

        page = connect_to_bruno()
        if not page:
            return

        select_main_collection(page)
        success = search_and_open_request(page, request_name)
        disconnect_from_bruno(page)

        if success:
            log("Скрипт завершён успешно")
        else:
            log("Скрипт завершён с ошибкой при открытии запроса")
    except Exception as e:
        log(f"Критическая ошибка в main: {str(e)}")

if __name__ == "__main__":
    main()