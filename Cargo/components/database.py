import os
from dotenv import load_dotenv


load_dotenv()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', 5432),
        'OPTIONS': {
            # Нужно явно указать схемы, с которыми будет работать приложение.
            'options': '-c search_path=content,public'
        }
    }
}