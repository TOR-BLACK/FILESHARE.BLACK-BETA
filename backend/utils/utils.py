# Все функции, связанные с прочим

# Подгружаем необходимые зависимости
import os
import random
import string
import secrets

# Получаем полный путь к корневой папке
script_path = os.path.dirname(os.path.realpath(__file__))

# Функция, отвечающая за проверку наличия директории
def folder_exists(path):
	if os.path.isdir(os.path.join(os.path.dirname(script_path), path)) == False:
		os.mkdir(os.path.join(os.path.dirname(script_path), path))

# Функция, отвечающая за побайтовую итерацию по содержимому файла
def iterfile(path):  # 
	with open(path, mode="rb") as file_like:  # 
		yield from file_like  # 

def generate_random_name(length=5):
    """Генерирует случайное имя из латинских букв."""
    alphabet = string.ascii_letters
    return ''.join(secrets.choice(alphabet) for _ in range(length))