# Все функции, связанные с обработкой медиа

# Подгружаем необходимые зависимости
import os
import cv2
import aiofiles.os

from moviepy.editor import *
from PIL import Image

# Получаем полный путь к корневой папке
script_path = os.path.dirname(os.path.realpath(__file__))

# Функция, отвечающая за наложение вотермарка на медиа
def create_watermark(path, video_name):
	try:
		input_watermark_path = os.path.join(os.path.dirname(script_path), 'watermark.png')
		output_watermark_path = os.path.join(os.path.dirname(script_path), 'water.png')
		input_video_path = os.path.join(os.path.dirname(script_path), f'{path}/{video_name}')
		output_video_path = os.path.join(os.path.dirname(script_path), f'{path}/w_{video_name}')
		vid = cv2.VideoCapture(input_video_path)
		height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
		width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))

		im = Image.open(input_watermark_path)
		im.thumbnail((width,height),Image.Resampling.LANCZOS)
		im.save(output_watermark_path, "PNG")
		subprocess.run(f"ffmpeg -i '{input_video_path}' -i '{output_watermark_path}' -filter_complex 'overlay=(W-w)/2:(H-h)/2' '{output_video_path}'; rm '{input_video_path}'; rm '{output_watermark_path}'; mv '{output_video_path}' '{input_video_path}';", shell=True)
	except:
		pass

# Функция, отвечающая за наложение блока координат на видео
def create_coords_video(coords, path):
	try:
		clip = ColorClip((150,90), (255,255,255), duration=len(coords)) 
		movie_texts = []
		last_sec = 0
		for item in coords:
			txt = TextClip(item, fontsize=10, align="West", color='black', font="NimbusSans-Bold")  
			txt = txt.set_start(last_sec).set_end(last_sec+1)
			movie_texts.append(txt)
			last_sec += 1
		
		# Overlay the text clip on the first video clip  
		texts = CompositeVideoClip(movie_texts).set_pos((5, 5))
		video = CompositeVideoClip([clip, texts])  
			
		# showing video  
		video.write_videofile(path, fps=25)
		return True
	except Exception as e:
		print(e)
		return False

# Функция, отвечающая за обработку видео в заметке
async def process_video_note(url, name):
	url = url.replace("/api/get_note_file?", "")
	url = url.split("&")
	dir_id = url[0].replace("id=", "")
	file_name = url[1].replace("file_name=", "")
	folder_exists("uploaded")
	folder_exists("notes")
	path = os.path.join(os.path.dirname(script_path), f'notes/{dir_id}/{file_name}')
	destination_path = os.path.join(os.path.dirname(script_path), f"uploaded/{name}/{file_name}")
	async with aiofiles.open(path, 'rb') as in_file:
		async with aiofiles.open(destination_path, 'wb+') as out_file:
			content = await in_file.read()
			await out_file.write(content)
	await aiofiles.os.remove(path)
	create_watermark(os.path.join(os.path.dirname(script_path), f'uploaded/{name}'), file_name)