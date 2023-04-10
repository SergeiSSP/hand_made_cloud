from flask import Flask, request, render_template, send_from_directory
import os
import requests
from datetime import datetime

from werkzeug.middleware.profiler import ProfilerMiddleware

from data import Server
from replication import replication

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'


server = Server()
location = server.get_location()
name = server.get_vps_name()
ip = server.get_ip()
server_data = [name, location, ip]


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Получаем ссылку на файл
        file_url = request.form['file_url']
        # Скачиваем файл в папку uploads и измеряем время скачивания
        start_time = datetime.now()
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file_url.split('/')[-1])
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb+') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
        end_time = datetime.now()
        download_time = end_time - start_time
        download_time = str(download_time).split('.')[0]
        response = replication(filename, server)
        # Возвращаем ссылку на скачанный файл и время скачивания
        return render_template('download.html',response=response, server_data=server_data, filename=(filename).split('/')[-1],
                               download_time=download_time, endtime=end_time.strftime('%H:%M:%S'))
    # Если метод GET, отображаем форму для ввода ссылки на файл
    return render_template('index.html')

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/profile/<filename>', methods=['GET'])
def profile(filename):
    with open(log_path, "r") as f:
        for line in f:
            if re.search(filename, line):
                print(line.strip())

#TODO написать код для отображения информации по файлам из логов nginx, настроить отдельную функциию для отображения всех трех тестовых заданий