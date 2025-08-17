# Подгружаем необходимые зависимости
import os
import dotenv
import mysql.connector

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Подгружаем роуты из папки routers
from routers import v1_router, v2_router, bugs_router

# Объявляем фастапи приложение
app = FastAPI(docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")

# Добавляем CORS-настройки
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # Разрешить все источники
	allow_credentials=True,  # Разрешить учетные данные
	allow_methods=["*"],  # Разрешить все методы
	allow_headers=["*"],  # Разрешить все заголовки
)

# Подгрузка .env файла
dotenv.load_dotenv()

# Инициализация коннекта с базой данных
connection = mysql.connector.connect(
	host=os.getenv("MYSQL_HOST"),
	database=os.getenv("MYSQL_DATABASE"),
	user=os.getenv("MYSQL_USER"),
	password=os.getenv("MYSQL_PASSWORD"),
	auth_plugin='mysql_native_password'
)

@app.on_event("startup")
async def on_startup():
	global connection

	# Событие после инициализации фастапи
	print('Startup event - initialising')
	app.include_router(v1_router, tags=['v1'])
	app.include_router(v2_router, tags=['v2'])
	app.include_router(bugs_router, tags=['bugs'])

	import routers.v1
	import routers.v2
	import routers.bugs
	routers.v1.connection = connection
	routers.v2.connection = connection
	routers.bugs.connection = connection