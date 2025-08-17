# Все функции, связанные с шифрованием

# Подгружаем необходимые зависимости
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad

# Переменная, несущая в себе пароль для шифрования XOR + HEX
encrypter_password = "123"
safe_url_password = "123"

# Функция, отвечающая за расшифровку "быстрой" ссылки
def decrypt_directly(encrypted_text):
    # Преобразование из шестнадцатичного формата
    bytes_text = bytes.fromhex(encrypted_text)
    decrypted_bytes = bytes_text.decode("utf-8")
    
    decrypted_text = ""
    for char in decrypted_bytes:
        if char.isalpha():
            shift_base = 65 if char.isupper() else 97
            decrypted_char = chr((ord(char) - shift_base - 3) % 26 + shift_base)
            decrypted_text += decrypted_char
        else:
            decrypted_text += char  # не расшифровываем знаки и пробелы

    return decrypted_text

# Функция, отвечающая за шифрование строки методом XOR
def crypto_xor(message: str, secret: str) -> str:
	out = ""
	secret_len = len(secret)
	for i in range(len(message)):
		out += chr(ord(message[i]) ^ ord(secret[i % secret_len]))
	return out

# Функция, отвечающая за сжатие строки байтовым способом
def compress_str(data: str) -> str:
	# Преобразуем шестнадцатеричную строку в байты
	bytes_data = bytes.fromhex(data)
	# Кодируем в base64 и убираем padding
	encoded = base64.b64encode(bytes_data).decode().rstrip('=')
	return encoded

# Функция, отвечающая за расжатие строки байтовым способом
def decompress(compressed_data: str) -> str:
	# Добавляем padding для base64 декодирования
	padding = '=' * ((4 - len(compressed_data) % 4) % 4)
	padded_data = compressed_data + padding
	# Декодируем из base64
	decoded = base64.b64decode(padded_data)
	# Преобразуем байты обратно в шестнадцатеричную строку
	return decoded.hex()

# Функция, отвечающая за шифрование строки
def encrypt_xor(message: str, secret: str) -> str:
	return crypto_xor(message, secret).encode('utf-8').hex()

# Функция, отвечающая за дешифрование строки
def decrypt_xor(message_hex: str, secret: str) -> str:
	message = bytes.fromhex(message_hex).decode('utf-8')
	return crypto_xor(message, secret)

def encrypt_string(input_string, password):
    # Создание объекта шифрования с использованием AES
    cipher = AES.new(get_aes_key(password), AES.MODE_CBC)
    # Добавление случайного вектора инициализации
    iv = cipher.iv
    # Шифрование и кодирование в Base64
    encrypted = cipher.encrypt(pad(input_string.encode('utf-8'), AES.block_size))
    return base64.b32encode(iv + encrypted).decode('utf-8').rstrip('=')

def decrypt_string(encrypted_string, password):
	encrypted_string = encrypted_string.replace('"', '')
    # Декодирование из Base64
	padding = '=' * (4 - len(encrypted_string) % 4)
	padded_string = encrypted_string + padding
	encrypted_data = base64.b32decode(padded_string)
    # Извлечение вектора инициализации (IV)
	iv = encrypted_data[:16]  # Первые 16 байт - это IV
	encrypted_message = encrypted_data[16:]  # Остальная часть - зашифрованное сообщение
    
    # Создание объекта шифрования с использованием AES
	cipher = AES.new(get_aes_key(password), AES.MODE_CBC, iv)
    # Расшифровка и удаление отступов
	decrypted = unpad(cipher.decrypt(encrypted_message), AES.block_size)
	return decrypted.decode('utf-8')

def get_aes_key(password):
    # Получаем 32-байтный ключ с помощью SHA-256
	return hashlib.sha256(password.encode('utf-8')).digest()