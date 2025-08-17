# Подгружаем необходимые зависимости
import os
import asyncio
import subprocess
import json
import shutil
import zipfile
import base64
import time
import random
import aiofiles

from fastapi import APIRouter, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, RedirectResponse
from typing import List
from datetime import datetime

from models.coords_data import CoordsData
from utils.encryption import decrypt_directly, compress_str, decompress, encrypt_xor, decrypt_xor, encrypt_string, decrypt_string, encrypter_password, safe_url_password
from utils.utils import folder_exists, iterfile, generate_random_name
from utils.render import create_watermark, create_coords_video, process_video_note
from utils.media import accept_only_media, image_render_formats, image_formats, video_formats

from urllib.parse import quote

from .v2 import check_pin_correct

# Получаем полный путь к корневой папке
script_path = os.path.dirname(os.path.realpath(__file__))
# Переменная с подключением к базе
connection = None
# Объект, в котором хранится кол-во просмотров страниц файлов
views = {}
# Объект для хранения соответствий между оригинальными и зашифрованными именами файлов
file_name_map = {}

# Объявление самого роутера
v1_router = APIRouter(prefix='/api')

@v1_router.post("/upload_file")
async def upload_file(life: str, files: List[UploadFile] = [], note_videos: List[str] = [], compress: bool = False, pin: str = '-', js: bool = True, safe: bool = False):
	# Загрузка файлов на сервер

	# Приём файлов, их сохранение и обработка
	if len(files) > 0 or len(note_videos) > 0:
		global connection
		folder_exists("uploaded")
		existing_folders = os.listdir(os.path.join(os.path.dirname(script_path), 'uploaded'))
		# Генерируем рандомное имя для новой директории
		new_name = random.randint(0,999999999)
		# Цикл проверки имени на уникальность
		while new_name in existing_folders:
			new_name = random.randint(0,999999999)
		# Создаем директорию,
		os.mkdir(os.path.join(os.path.dirname(script_path), f'uploaded/{new_name}'))
		try:
			connection.ping(reconnect=True)
		except:
			pass
		# Инициализируем курсор для работы с базой данных
		cursor = connection.cursor(dictionary=True, buffered=True)
		# Создаем файл life.txt и записываем туда время жизни файлов
		async with aiofiles.open(os.path.join(os.path.dirname(script_path), f'uploaded/{new_name}/life.txt'), 'w') as out_file:
			await out_file.write(life)
		# Создаем файл pin.txt и записываем туда пин-код в случае безопасной ссылки
		if pin != '-':
			async with aiofiles.open(os.path.join(os.path.dirname(script_path), f'uploaded/{new_name}/pin.txt'), 'w') as out_file:
				await out_file.write(pin)
		print(new_name)
		for file in files:
			# Создаем файлы
			type_file = "file"
			if file.filename.endswith(tuple(image_formats)):
				type_file = "image"
			if file.filename.endswith(tuple(video_formats)):
				type_file = "video"
			if accept_only_media and type_file == "file":
				continue
			async with aiofiles.open(os.path.join(os.path.dirname(script_path), f'uploaded/{new_name}/{file.filename}'), 'wb') as out_file:
					# Создаем все файлы
					content = await file.read()  # async read
					await out_file.write(content)  # async write
					if type_file == "image":
						create_watermark(os.path.join(os.path.dirname(script_path), f'uploaded/{new_name}'), file.filename)
					'''if type_file != "file" and compress and not file.filename.endswith(".gif"):
						# Проверка, что файл - медиа
						try:
							# Заносим файл в таблицу для последующего сжатия и обработки
							cursor.execute(f"INSERT INTO `processing_queue` (`dir_id`, `filename`) VALUES ('{new_name}', '{file.filename}')")
						except:
							pass'''
		if len(note_videos) > 0:
			note_videos = json.loads(note_videos[0])
			tasks = [process_video_note(url, new_name) for url in note_videos]
			# Ждем завершения всех задач
			await asyncio.gather(*tasks)
		# Коммитим изменения в базу и закрываем текущий курсор
		connection.commit()
		cursor.close()
		# Возвращаем зашифрованное сжатое имя директории
		compressed_name = compress_str(encrypt_xor(str(new_name), encrypter_password))
		if (safe):
			compressed_name = encrypt_string(compress_str(encrypt_xor(str(new_name), encrypter_password)), safe_url_password)

		if js:
			return JSONResponse(status_code=200, content={ "directory_name": compressed_name, "files": [f"/f/{compressed_name}/{file.filename}" for file in files]})
		else:
			return RedirectResponse(url=f"{request.url.scheme}://{request.url.hostname}{'' if '.black' in request.url.hostname else '.black'}/u/{compressed_name}")
	else:
		return JSONResponse(status_code=406, content="Files and note_videos is empty")

@v1_router.post("/add_files")
async def add_files(id: str, files: List[UploadFile] = [], note_videos: List[str] = [], compress: bool = False):
	# Догрузка файлов в директорию

	# Приём файлов, их сохранение и обработка
	global connection
	if len(id) <= 0:
		# Если id пустой - возврат 404
		return 404
	else:
		folder_exists("uploaded")
		if len(files) > 0 or len(note_videos) > 0:
			# Расшифровываем переданный ID директории для получения настоящего значения
			if len(id) < 15:
				id = decrypt_xor(decompress(str(id)), encrypter_password)
			else:
				decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
				decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
				id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR

			path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
			# Проверяем, что директория существует
			if os.path.isdir(path):
				try:
					connection.ping(reconnect=True)
				except:
					pass
				# Инициализируем курсор для работы с базой данных
				cursor = connection.cursor(dictionary=True, buffered=True)
				for file in files:
					# Дозагружаем файлы
					type_file = "file"
					# Проверка, что файл - изображение
					if file.filename.endswith(tuple(image_formats)):
						type_file = "image"
					# Проверка, что файл - видео
					if file.filename.endswith(tuple(video_formats)):
						type_file = "video"
					if accept_only_media and type_file == "file":
						# Отсекаем не медиа файлы и создаем их
						continue
					async with aiofiles.open(os.path.join(os.path.dirname(script_path), f"{path}/{file.filename}"), 'wb') as out_file:
						content = await file.read()  # async read
						await out_file.write(content)  # async write
						'''if type_file != "file" and not file.filename.endswith(".gif") and compress:
							try:
								# Заносим файл в таблицу для последующего сжатия и обработки
								cursor.execute(f"INSERT INTO `processing_queue` (`dir_id`, `filename`) VALUES ('{id}', '{file.filename}')")
							except:
								pass'''
				if len(note_videos) > 0:
					note_videos = json.loads(note_videos[0])

					tasks = [process_video_note(url, id) for url in note_videos]
					# Ждем завершения всех задач
					await asyncio.gather(*tasks)
				# Коммитим изменения в базу и закрываем текущий курсор
				connection.commit()
				cursor.close()
				# Возвращаем зашифрованное сжатое имя директории
				return JSONResponse(status_code=200, content="Succesfull")
			else:
				return JSONResponse(status_code=404, content="Error")
		else:
			return JSONResponse(status_code=406, content="Files and note_videos is empty")

@v1_router.post("/apply_coords")
async def apply_coords(files: List[UploadFile], coords: List[CoordsData]):
	# Наложение координат на видео

	folder_exists("notes")
	existing_folders = os.listdir("notes")
	# Генерируем рандомное имя для новой директории
	new_name = random.randint(0,999999999)
	# Цикл проверки имени на уникальность
	while new_name in existing_folders:
		new_name = random.randint(0,999999999)
	# Создаем директорию,
	os.mkdir(f"notes/{new_name}")
	path = f"notes/{new_name}"
	for file in files:
		# Загружаем файлы
		if file.filename.endswith(tuple(video_formats)):
			async with aiofiles.open(os.path.join(os.path.dirname(script_path), f"{path}/{file.filename}"), 'wb') as out_file:
				content = await file.read()  # async read
				await out_file.write(content)  # async write
	for item in coords:
		video_name = item.name
		video_path = os.path.join(os.path.dirname(script_path), f"notes/{new_name}/{video_name}")
		coords_path = os.path.join(os.path.dirname(script_path), f"notes/{new_name}/crd{video_name}.mp4")
		if os.path.isfile(video_path):
			if create_coords_video(item.coords, coords_path) == True:
				output_path = os.path.join(os.path.dirname(script_path), f"notes/{new_name}/c_{video_name}")
				subprocess.run(f"ffmpeg -i '{video_path}' -i '{coords_path}' -filter_complex 'overlay=10:main_h-overlay_h-10' '{output_path}'; rm '{video_path}'; rm '{coords_path}'; mv '{output_path}' '{video_path}';", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				return f"/api/get_note_file?id={new_name}&file_name={video_name}"
			else:
				return JSONResponse(status_code=405, content="Coords video is not created")

@v1_router.get("/get_info")
async def get_info(id: str, view: bool = False, pin: str = None):
	# Получение информации о загруженной директории и её файлах

	global connection
	encrypted_id = id
	if len(id) <= 0:
		# Если id пустой - возврат 404
		return 404
	else:
		folder_exists("uploaded")
		# Расшифровываем переданный ID директории для получения настоящего значения
		if len(id) < 15:
			id = decrypt_xor(decompress(str(id)), encrypter_password)
		else:
			decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
			decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
			id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR

		if view == True:
			# Если view == True, то засчитываем +1 просмотр
			if f"{id}" in views:
				views[f"{id}"] += 1
			else:
				views[f"{id}"] = 1

		try:
			connection.ping(reconnect=True)
		except:
			pass
		# Инициализация курсора для работы с базой данных
		cursor = connection.cursor(dictionary=True, buffered=True)
		cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

		path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
		# Проверяем, что директория существует
		if os.path.isdir(path):
			# Проверка установленного PIN-кода
			pin_file_path = os.path.join(os.path.dirname(script_path), f"{path}/pin.txt")
			pin_set = os.path.isfile(pin_file_path)  # Проверяем наличие файла pin.txt

			if pin_set:
				if pin is None:
					return JSONResponse(status_code=403, content={"pin": True})
				else:
					# Проверка PIN-кода через API
					pin_check_response = await check_pin_correct(encrypted_id, pin)  # Вызов API для проверки PIN
					if pin_check_response.status_code != 200:
						return JSONResponse(status_code=403, content={"message": "Неверный PIN-код"})

			async with aiofiles.open(os.path.join(os.path.dirname(script_path), f"{path}/life.txt"), "r") as read_file:
				# Читаем файл со сроком жизни директории
				content = await read_file.read()
				if 'infinity' in content:
					# Формируем вывод срока жизни файла
					expires_in = "infinity"
				else:
					# Формируем вывод срока жизни файла
					if "." in content:
						expires_in = int(content[0:content.index(".")]) #expires_in = datetime.utcfromtimestamp(int(content[0:content.index(".")])).strftime('%d.%m.%Y %H:%M:%S')
					else:
						expires_in = int(content) #expires_in = datetime.utcfromtimestamp(int(content)).strftime('%d.%m.%Y %H:%M:%S')
				description = None
				description_file_path = os.path.join(os.path.dirname(script_path), f"{path}/description.txt")
				if os.path.isfile(description_file_path):
					async with aiofiles.open(description_file_path, "r") as description_file:
						description = await description_file.read()
				pin_file_path = os.path.join(os.path.dirname(script_path), f"{path}/pin.txt")
				pin = os.path.isfile(pin_file_path)
				# Инициализируем объект и его параметры для отдачи на фронт
				json = {}
				json['created'] = int(os.stat(path).st_mtime) 
				#json['created'] = datetime.fromtimestamp(json['created']).strftime("%d.%m.%Y")
				json['expires_in'] = expires_in
				json['description'] = description
				json['files_count'] = 0
				json['size'] = 0
				json['pin'] = pin
				if f"{id}" in views:
					json['views'] = views[f"{id}"]
				else:
					json['views'] = 0
				json['files'] = []
				# Перебираем файлы в директории
				for file in os.listdir(path):
					# Формируем путь к файлам для более удобной работы
					local_path = path + "/" + file
					# Проверяем, что файл не life.txt и не сжатая директория
					if os.path.isfile(local_path) and not f"{id}.zip" in local_path and not "life.txt" in local_path and not "description.txt" in local_path and not "pin.txt" in local_path:
						# Прибавляем файл в счетчик
						json['files_count'] += 1
						# Получаем размер файла
						local_size = os.path.getsize(local_path)
						# Прибавляем счетчик общего размера директории
						json['size'] += local_size
						# Получаем имя файла
						filename = os.path.basename(local_path)
						real_name = filename
						if any('а' <= char <= 'я' or 'А' <= char <= 'Я' for char in filename):
							#if filename not in file_name_map:
							name, ext = os.path.splitext(filename)
							new_name = f"{generate_random_name()}{ext}"
							file_name_map[filename] = new_name
							#else:
							#	new_name = file_name_map[filename]
							filename = new_name

						special_chars = set('!№;%')
						if any(char in special_chars for char in filename):
							new_name = quote(filename)
							file_name_map[filename] = new_name
							filename = new_name
					
						upload_date = os.stat(local_path).st_mtime
						upload_date = datetime.fromtimestamp(upload_date).strftime("%d.%m.%Y %H:%M")
						type_file = "file"
						for ext in image_formats:
							# Проверка, что файл - изображение
							if ext in local_path:
								type_file = "image"
								break
						for ext in video_formats:
							# Проверка, что файл - видео
							if ext in local_path:
								type_file = "video"
								break
						# Добавляем в список файлов текущий файл и информацию о нём
						json['files'].append({filename: f"/f/{encrypted_id}/{filename}", "real_name": real_name, "type_file": type_file, "file_size": local_size, 'upload_date': upload_date})
				# Возвращаем информацию о директории
				return json
		else:
			return 404

@v1_router.get("/get_file")
async def get_file(id: str, file_name: str, ios: bool = False):
	# Получение файла

	folder_exists("uploaded")
	if id.isnumeric() == False:
		# Если ID передан зашифрованынй - расшифровываем
		if len(id) < 15:
			id = decrypt_xor(decompress(str(id)), encrypter_password)
		else:
			decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
			decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
			id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR

	encrypted_name = file_name
	print(encrypted_name)
	if file_name in file_name_map.values():
		file_name = next((key for key, value in file_name_map.items() if value == file_name), file_name)

	# Формируем путь для более удобной работы
	path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}/{file_name}")
	if os.path.isfile(path):
		type_file = "file"
		if file_name.endswith(tuple(image_render_formats)):
			type_file = "image/jpeg"
		if file_name.endswith(tuple(video_formats)):
			type_file = "video/mp4"
		if type_file == "file" or ios == True:
			# Если есть файл, возвращаем его
			return FileResponse(path=path, filename=encrypted_name)
		else:
			return StreamingResponse(iterfile(path), media_type=type_file)
	else:
		# Если файла нет, возвращаем ошибку
		return JSONResponse(status_code=404, content="File is not exists")

@v1_router.get("/delete_dir")
async def delete_dir(id: str):
	# Удаление директории

	folder_exists("uploaded")
	# Расшифровываем переданный ID
	if len(id) < 15:
		id = decrypt_xor(decompress(str(id)), encrypter_password)
	else:
		decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
		decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
		id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR
	# Формируем путь для более удобной работы
	path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
	if not path.endswith("uploaded/"):
		try:
			# Удаляем директорию
			shutil.rmtree(path)
			# Возвращаем статус 200
			return JSONResponse(status_code=200, content="Succesfull")
		except Exception as e:
			# Показываем и возвращаем ошибку
			print(e)
			return JSONResponse(status_code=404, content="Error")

@v1_router.get("/delete_dir_directly")
async def delete_dir_directly(id: str, request: Request):
	# Удаление директории прямой ссылкой

	try:
		folder_exists("uploaded")
		# Расшифровываем переданный ID
		if len(id) < 15:
			id = decrypt_xor(decompress(str(id)), encrypter_password)
		else:
			decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
			decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
			id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR
		# Формируем путь для более удобной работы
		path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
		hostname = request.url.hostname
		redirect_path = f"{request.url.scheme}://{hostname}{'' if '.black' in hostname else '.black'}"
		if not path.endswith("uploaded/"):
			try:
				# Удаляем директорию
				shutil.rmtree(path)
				# Возвращаем статус 200
				return RedirectResponse(url=redirect_path)
			except Exception as e:
				# Показываем и возвращаем ошибку
				print(e)
				return RedirectResponse(url=redirect_path)
	except:
		return RedirectResponse(url=redirect_path)

@v1_router.delete("/delete_dirs")
async def delete_dirs(ids: List[str]):
	# Удаление нескольких директорий

	try:
		folder_exists("uploaded")
		for id in ids:
			if id.isnumeric() == False:
				# Если ID передан зашифрованынй - расшифровываем
				if len(id) < 15:
					id = decrypt_xor(decompress(str(id)), encrypter_password)
				else:
					decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
					decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
					id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR
			path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
			if not path.endswith("uploaded/"):
				try:
					shutil.rmtree(path)
				except Exception as e:
					print(e)
					pass
		return JSONResponse(status_code=200, content="Succesfull")
	except Exception as e:
		print(e)
		return JSONResponse(status_code=404, content="Error")

@v1_router.delete("/delete_file")
async def delete_file(id: str, filename: str):
	# Удаление файла из директории

	folder_exists("uploaded")
	# Расшифровываем переданный ID
	if len(id) < 15:
		id = decrypt_xor(decompress(str(id)), encrypter_password)
	else:
		decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
		decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
		id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR
	# Формируем путь для более удобной работы
	path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
	if not path.endswith("uploaded/"):
		if os.path.isdir(path):
			inverted_file_name_map = {v: k for k, v in file_name_map.items()}
			original_filename = inverted_file_name_map.get(filename, filename)
			file_path = f"{path}/{original_filename}"
			
			print(file_name_map)
			print(filename)
			print(file_path)
			print(os.path.isfile(file_path))

			if os.path.isfile(file_path):
				try:
					# Удаляем директорию
					os.remove(file_path)
					# Возвращаем статус 200
					return JSONResponse(status_code=200, content="Succesfull")
				except Exception as e:
					# Показываем и возвращаем ошибку
					print(e)
					return JSONResponse(status_code=404, content="Error")
			else:
				return JSONResponse(status_code=402, content="File is not exists")
		else:
			return JSONResponse(status_code=401, content="Directory is not exists")

@v1_router.get("/get_files")
async def get_files(id: str):
	# Скачать директорию 

	folder_exists("uploaded")
	encrypted_id = id
	# Расшифровываем переданный ID
	if len(id) < 15:
		id = decrypt_xor(decompress(str(id)), encrypter_password)
	else:
		decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
		decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
		id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR

	print('nd:')
	print(id)
	# Формируем путь для более удобной работы
	path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
	# Проверяем, что директория существует
	if os.path.isdir(path):
		files = os.listdir(path)
		files = [file for file in files if file not in ['life.txt', 'description.txt', 'pin.txt']]
		# Если в директории только один файл, возвращаем его напрямую
		if len(files) == 1:
			single_file_path = os.path.join(path, files[0])
			return FileResponse(path=single_file_path, filename=files[0])
			
		# Формируем путь к сжатой в архив директории для более удобной работы
		zip_path = f"{path}/{id}.zip"
		# Проверяем, что сжатый архив не существует
		if os.path.isfile(zip_path) == False:
			# Создаем архив директории
			zf = zipfile.ZipFile(zip_path, "w")
			# Получаем список файлов
			files = os.listdir(path)
			# Перебираем каждый файл и добавляем его в архив
			for file in files:
				filepath = path + "/" + file
				if os.path.isfile(filepath) and not ".zip" in filepath and not ".txt" in filepath:
					zf.write(filepath, file)
			# Убираем архив из памяти и работы
			zf.close()
		# Возвращаем архив с помещенными внутрь файлами
		return FileResponse(path=zip_path, filename=f"{encrypted_id}.zip")
	else:
		# Если директории нет, выводим ошибку
		return JSONResponse(status_code=404, content="Error")

@v1_router.get("/get_files_directly")
async def get_files_directly(id: str, request: Request):
	# Скачать директорию напрямую
	try:
		hostname = request.url.hostname
		redirect_path = f"{request.url.scheme}://{hostname}{'' if '.black' in hostname else '.black'}"
		if len(id) == 0:
			return RedirectResponse(url=redirect_path)
		folder_exists("uploaded")
		encrypted_id = id

		# Расшифровываем переданный ID
		if len(id) < 15:
			id = decrypt_xor(decompress(str(id)), encrypter_password)
		else:
			decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
			decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
			id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR

		print('nd:')
		print(id)
		# Формируем путь для более удобной работы
		path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
		# Проверяем, что директория существует
		if os.path.isdir(path):
			files = os.listdir(path)
			files = [file for file in files if file not in ['life.txt', 'description.txt', 'pin.txt']]
			# Если в директории только один файл, возвращаем его напрямую
			if len(files) == 1:
				single_file_path = os.path.join(path, files[0])
				return FileResponse(path=single_file_path, filename=files[0])
				
			# Формируем путь к сжатой в архив директории для более удобной работы
			zip_path = f"{path}/{id}.zip"
			# Проверяем, что сжатый архив не существует
			if os.path.isfile(zip_path) == False:
				# Создаем архив директории
				zf = zipfile.ZipFile(zip_path, "w")
				# Получаем список файлов
				files = os.listdir(path)
				# Перебираем каждый файл и добавляем его в архив
				for file in files:
					filepath = path + "/" + file
					if os.path.isfile(filepath) and not ".zip" in filepath and not ".txt" in filepath:
						zf.write(filepath, file)
				# Убираем архив из памяти и работы
				zf.close()
			# Возвращаем архив с помещенными внутрь файлами
			return FileResponse(path=zip_path, filename=f"{encrypted_id}.zip")
		else:
			# Если директории нет, выводим ошибку
			return RedirectResponse(url=redirect_path)
	except Exception as e:
		print(e)
		return RedirectResponse(url=redirect_path)

@v1_router.post("/get_dirs")
async def get_dirs(ids: List[str]):
	# Скачать несколько директорий

	if len(ids) <= 0:
		return JSONResponse(status_code=406, content="IDs is empty")
	try:
		folder_exists("uploaded")
		folder_exists("zips")
		zip_name = int(time.time())
		zip_path = os.path.join(os.path.dirname(script_path), f"zips/{zip_name}.zip")
		# Создаем архив директорий
		zf = zipfile.ZipFile(zip_path, "w")
		for id in ids:
			# Сохраняем изначальный ID для дальнейшей работы
			encrypted_id = id
			if id.isnumeric() == False:
				# Если ID передан зашифрованынй - расшифровываем
				if len(id) < 15:
					id = decrypt_xor(decompress(str(id)), encrypter_password)
				else:
					decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
					decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
					id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR
			# Формируем путь для более удобной работы
			path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}")
			# Проверяем, что директория существует
			if os.path.isdir(path):
				# Получаем список файлов
				files = os.listdir(path)
				# Перебираем каждый файл и добавляем его в архив
				for file in files:
					filepath = path + "/" + file
					if os.path.isfile(filepath) and not ".zip" in filepath and not ".txt" in filepath:
						zf.write(filepath, f"{encrypted_id}/{file}")
		# Убираем архив из памяти и работы
		zf.close()
		base = "Error"
		with open(zip_path, "rb") as f:
			bytes = f.read()
			base = base64.b64encode(bytes)
		os.remove(zip_path)
		return base#FileResponse(path=zip_path, filename=f"{zip_name}.zip")
	except Exception as e:
		print(e)
		return JSONResponse(status_code=404, content="Error")

@v1_router.get("/get_note_file")
async def get_note_file(id: str, file_name: str):
	# Получение файла из директории с заметкой

	folder_exists("notes")
	# Формируем путь для более удобной работы
	path = os.path.join(os.path.dirname(script_path), f"notes/{id}/{file_name}")
	if os.path.isfile(path):
		return FileResponse(path=path, filename=file_name)
	else:
		# Если файла нет, возвращаем ошибку
		return JSONResponse(status_code=404, content="File is not exists")

@v1_router.patch("/lifetime")
async def change_lifetime(id: str, life: str):
	# Изменить время хранения директории

	folder_exists("uploaded")
	if id.isnumeric() == False:
		# Если ID передан зашифрованынй - расшифровываем
		if len(id) < 15:
			id = decrypt_xor(decompress(str(id)), encrypter_password)
		else:
			decrypted_compressed_name = decrypt_string(id, safe_url_password)  # Расшифровываем
			decompressed_name = decompress(decrypted_compressed_name)  # Декомпрессируем
			id = decrypt_xor(decompressed_name, encrypter_password)  # Расшифровываем с помощью XOR

	path = os.path.join(os.path.dirname(script_path), f"uploaded/{id}/life.txt")

	if os.path.isfile(path):
		async with aiofiles.open(path, 'w') as out_file:
			await out_file.write(life)

		return JSONResponse(status_code=200, content="Succesfull")
	else:
		return JSONResponse(status_code=404, content="File not found")