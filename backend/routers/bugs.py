# Подгружаем необходимые зависимости
from fastapi import APIRouter, Form

# Переменная с подключением к базе
connection = None

# Объявление самого роутера
bugs_router = APIRouter(prefix='/api/v2/bugs')

@bugs_router.post("/create")
async def create_bug(
	title: str = Form(...),
	description: str = Form(...),
	dir_id: str = Form('-')
):
	# Создание баг-заметки

	global connection
	# Пытаемся переподключиться к базе, если это требуется
	try:
		connection.ping(reconnect=True)
	except:
		pass
	# Инициализируем курсор для работы с базой данных
	cursor = connection.cursor(dictionary=True, buffered=True)

	sql = "INSERT INTO bugs (title, description, dir_id) VALUES (%s, %s, %s)"
	# Данные для вставки
	values = (title, description, dir_id)

	# Выполнение запроса
	try:
		cursor.execute(sql, values)
		inserted_id = cursor.lastrowid
		connection.commit()
		cursor.close()

		return JSONResponse(status_code=200, content={'bug_id': inserted_id})
	except Exception as e:
		print(e)
		return JSONResponse(status_code=400, content="SQL Error")

@bugs_router.put("/dir_id/")
async def set_dir_id_to_bug(
	bug_id: int = Form(...),
	dir_id: str = Form(...)
):
	# Установка ID директории к баг-заметке по её ID

	global connection
	# Пытаемся переподключиться к базе, если это требуется
	try:
		connection.ping(reconnect=True)
	except:
		pass
	# Инициализируем курсор для работы с базой данных
	cursor = connection.cursor(dictionary=True, buffered=True)

	sql = "UPDATE bugs SET dir_id = %s WHERE id = %s"
	# Данные для вставки
	values = (dir_id, bug_id)

	# Выполнение запроса
	try:
		cursor.execute(sql, values)
		connection.commit()
		cursor.close()

		return JSONResponse(status_code=200, content="Succesfull")
	except Exception as e:
		print(e)
		return JSONResponse(status_code=400, content="SQL Error")

@bugs_router.delete("/delete/")
async def delete_bug(
	bug_id: int
):
	# Удаление баг-заметки по её ID

	global connection
	# Пытаемся переподключиться к базе, если это требуется
	try:
		connection.ping(reconnect=True)
	except:
		pass
	# Инициализируем курсор для работы с базой данных
	cursor = connection.cursor(dictionary=True, buffered=True)

	# Выполнение запроса
	try:
		cursor.execute(f"DELETE FROM bugs WHERE id = {bug_id}")
		connection.commit()
		cursor.close()

		return JSONResponse(status_code=200, content="Succesfull")
	except Exception as e:
		print(e)
		return JSONResponse(status_code=400, content="SQL Error")