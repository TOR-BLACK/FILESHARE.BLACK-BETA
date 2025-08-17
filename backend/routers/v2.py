# Подгружаем необходимые зависимости
import os
import shutil
import aiofiles
import random

from urllib.parse import unquote
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

from utils.encryption import compress_str, decompress, encrypt_xor, decrypt_xor, encrypt_string, decrypt_string, encrypter_password, safe_url_password
from utils.utils import folder_exists
from utils.pin_attempts import pin_attempt_manager

# Получаем полный путь к корневой папке
script_path = os.path.dirname(os.path.realpath(__file__))
# Переменная с подключением к базе
connection = None

v2_router = APIRouter(prefix='/api/v2')

@v2_router.delete("/delete_temp_dir/")
async def delete_temp_dir(
	dirname: str
):
	# Удаление временной директории
	dirname = unquote(dirname)
	if len(dirname) < 15:
		dirname = decrypt_xor(decompress(str(dirname)), encrypter_password)
	else:
		decrypted_compressed_name = decrypt_string(dirname, safe_url_password)  # Расшифровываем
		decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
		dirname = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR

	directory_path = os.path.join(os.path.dirname(script_path), f'tmp/{dirname}')
	try:
		if os.path.isdir(directory_path):
			shutil.rmtree(directory_path)
		else:
			return JSONResponse(status_code=404, content="Directory not found")
		return JSONResponse(status_code=200, content="Succesfull")
	except Exception as e:
		print(e)
		return JSONResponse(status_code=400, content="Error")

@v2_router.post("/upload_chunk/")
async def upload_chunk(
	chunk: UploadFile = File(...),
	filename: str = Form(...),
	chunk_index: int = Form(...),
	total_chunks: int = Form(...),
	life: str = Form(None),
	dirname: str = Form(None),
	pin: str = Form(None)
):
	# Загрузка файлов в директории чанковым способом

	folder_exists("tmp")
	folder_exists("uploaded")
	new_name = dirname
	if dirname == None:
		existing_folders = os.listdir(os.path.join(os.path.dirname(script_path), f'uploaded'))
		new_name = random.randint(0,999999999)
		while new_name in existing_folders:
			new_name = random.randint(0,999999999)
		os.mkdir(os.path.join(os.path.dirname(script_path), f'tmp/{new_name}'))
		os.mkdir(os.path.join(os.path.dirname(script_path), f"uploaded/{new_name}"))
		async with aiofiles.open(os.path.join(os.path.dirname(script_path), f"uploaded/{new_name}/life.txt"), 'w') as out_file:
			await out_file.write(life)
		if pin != None:
			async with aiofiles.open(os.path.join(os.path.dirname(script_path), f"uploaded/{new_name}/pin.txt"), 'w') as out_file:
				await out_file.write(pin)
	else:
		if len(new_name) < 15:
			new_name = decrypt_xor(decompress(str(new_name)), encrypter_password)
		else:
			decrypted_compressed_name = decrypt_string(new_name, safe_url_password)  # Расшифровываем
			decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
			new_name = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR
	file_path = os.path.join(os.path.join(os.path.dirname(script_path), f"tmp/{new_name}"), filename)

	folder_exists(f"tmp/{new_name}")
	# Сохранение чанка
	with open(file_path + f".part{chunk_index}", "wb") as f:
		content = await chunk.read()
		f.write(content)

	# Проверка, завершена ли загрузка всех чанков
	if int(chunk_index) == int(total_chunks) - 1:
		# Объявляем путь к финальному файлу
		final_path = os.path.join(os.path.join(os.path.dirname(script_path), f"uploaded/{new_name}"), filename)
		# Объединяем все части в один файл
		with open(final_path, "wb") as final_file:
			for i in range(int(total_chunks)):
				part_file_path = file_path + f".part{i}"
				with open(part_file_path, "rb") as part_file:
					final_file.write(part_file.read())
				os.remove(part_file_path) # Удаление временной части
	if chunk_index == 0:
		return {"filename": filename, "chunk_index": chunk_index, "dirname": compress_str(encrypt_xor(str(new_name), encrypter_password))}
	else:
		return {"filename": filename, "chunk_index": chunk_index}

@v2_router.put("/description/")
async def put_description(
	dirname: str = Form(...),
	description: str = Form(...)
):
	# Установить описание к директории

	folder_exists("uploaded")
	if len(dirname) < 15:
		dirname = decrypt_xor(decompress(str(dirname)), encrypter_password)
	else:
		decrypted_compressed_name = decrypt_string(dirname, safe_url_password)  # Расшифровываем
		decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
		dirname = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR
	directory_path = os.path.join(os.path.dirname(script_path), f'uploaded/{dirname}')
	try:
		if os.path.isdir(directory_path):
			async with aiofiles.open(os.path.join(os.path.dirname(script_path), f"uploaded/{dirname}/description.txt"), 'w') as out_file:
				await out_file.write(description)
		else:
			return JSONResponse(status_code=404, content="Directory not found")
		return JSONResponse(status_code=200, content="Succesfull")
	except Exception as e:
		print(e)
		return JSONResponse(status_code=400, content="Error")

@v2_router.post("/check_pin/")
async def check_pin_correct(
	dirname: str = Form(...),
	pin: str = Form(...)
):
	# Проверка пин-кода на валидность

	# до проверки пин-кода надо узнать. а можно ли вообще пытаться
	encoded_dirname = dirname
	attempt_status = pin_attempt_manager.check_attempts(encoded_dirname)
	if not attempt_status['allowed']:
		return JSONResponse(
			status_code=429, 
			content={
				"message": attempt_status.get('message', 'Too many attempts'),
				"block_remaining": attempt_status.get('block_remaining', 0)
			}
		)

	folder_exists("uploaded")
	if len(dirname) < 15:
		dirname = decrypt_xor(decompress(str(dirname)), encrypter_password)
	else:
		decrypted_compressed_name = decrypt_string(dirname, safe_url_password)  # Расшифровываем
		decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
		dirname = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR
	directory_path = os.path.join(os.path.dirname(script_path), f'uploaded/{dirname}')
	try:
		if os.path.isdir(directory_path):
			pin_file_path = os.path.join(os.path.dirname(script_path), f"{directory_path}/pin.txt")
			if os.path.isfile(pin_file_path):
				async with aiofiles.open(pin_file_path, "r") as read_file:
					# Читаем файл со сроком жизни директории
					content = await read_file.read()
					
					if str(content) == pin:
						pin_attempt_manager.reset_attempts(encoded_dirname)
						return JSONResponse(status_code=200, content="Pin correct")
					else:
						pin_attempt_manager.increment_attempts(encoded_dirname)
						return JSONResponse(status_code=401, content="Pin not correct")
			else:
				return JSONResponse(status_code=200, content="Pin file don't exists")
		else:
			return JSONResponse(status_code=404, content="Directory not found")
	except Exception as e:
		print(e)
		return JSONResponse(status_code=400, content="Error")

@v2_router.post("/update_pin")
async def update_pin(dirname: str = Form(...), pin: str = Form(...)):
    try:
        folder_exists("uploaded")

		# до проверки пин-кода надо узнать. а можно ли вообще пытаться
        attempt_status = pin_attempt_manager.check_attempts(dirname)
        if not attempt_status['allowed']:
            return JSONResponse(
            	status_code=429, 
				content={
					"message": attempt_status.get('message', 'Too many attempts'),
					"block_remaining": attempt_status.get('block_remaining', 0)
			}
		)

        if len(dirname) < 15:
            dirname = decrypt_xor(decompress(str(dirname)), encrypter_password)
        else:
            decrypted_compressed_name = decrypt_string(dirname, safe_url_password)
            decompressed_name = decompress(decrypted_compressed_name)
            dirname = decrypt_xor(decompressed_name, encrypter_password)

        directory_path = os.path.join(os.path.dirname(script_path), f'uploaded/{dirname}')
        
        if not os.path.isdir(directory_path):
            return JSONResponse(status_code=404, content="Directory not found")
        
        pin_file_path = os.path.join(directory_path, "pin.txt")

        async with aiofiles.open(pin_file_path, "w") as write_file:
            await write_file.write(pin)
        return JSONResponse(status_code=200, content="Pin updated successfully")

    except Exception as e:
        print(e)
        return JSONResponse(status_code=400, content="Error")