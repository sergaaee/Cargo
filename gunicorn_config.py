# gunicorn_config.py

import multiprocessing

# Количество воркеров (рекомендуется количество ядер процессора * 2 + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# Привязка к порту, на котором будет работать Gunicorn
bind = "0.0.0.0:8000"

# Таймаут соединения (в секундах)
timeout = 120

# Уровень логирования
loglevel = "info"

# Путь к логам Gunicorn
accesslog = "/code/gunicorn_access.log"
errorlog = "/code/gunicorn_error.log"

# Имя приложения WSGI для запуска
wsgi_app = "Cargo.wsgi:application"

# Перезапускать воркеры при изменениях в коде (для разработки)
reload = True
