import os
import sys

# Добавляем путь к проекту
path ='/home/lizyakulan/quote_project'
if path not in sys.path:
    sys.path.append(path)

# Указываем настройки Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'quote_project.settings'

# Загружаем приложение
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()