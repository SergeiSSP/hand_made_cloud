
import threading
import json

import paramiko
from flask import Flask, request, render_template, send_from_directory
import os
import requests
from datetime import datetime

from data import Server

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

server = Server()
location = server.get_location()
name = server.get_vps_name()
ip = server.get_ip()
server_data = [name, location, ip]

hosts = {
    'VPS1 Frankfurt': {
        'host': '95.179.163.127',
        'pass': 'G!u6ivhV)3BzmQLp',
    },
    'VPS3 New Jersey': {
        'host': '66.135.4.119',
        'pass': '!5tCSS9FfV}A{UR]'
    },
    'VPS2 Singapore': {
        'host': '207.148.67.216',
        'pass': '3Az=NrPGB}B@SE3['
    },
}

@app.route('/upload/<url>', methods=['POST'])
def upload(url):
    start_time = datetime.now()
    file = os.path.join(app.config['UPLOAD_FOLDER'], file_url.split('/')[-1])
    with requests.get(file_url, stream=True) as r:
        r.raise_for_status()
        with open(file, 'wb+') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    end_time = datetime.now()
    t = threading.Thread(target=send_file, args=(server, file))
    t.start()
    download_time = end_time - start_time
    download_time = str(download_time).split('.')[0]
    return render_template('download.html', server_data=server_data, filename=file.split('/')[-1],
                           download_time=download_time, endtime=end_time.strftime('%H:%M:%S'))


    return render_template('index.html')






@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file_url = request.form['file_url']
        start_time = datetime.now()
        file = os.path.join(app.config['UPLOAD_FOLDER'], file_url.split('/')[-1])
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(file, 'wb+') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        end_time = datetime.now()
        t = threading.Thread(target=send_file, args=(server, file))
        t.start()
        download_time = end_time - start_time
        download_time = str(download_time).split('.')[0]
        return render_template('download.html', server_data=server_data, filename=file.split('/')[-1],
                               download_time=download_time, endtime=end_time.strftime('%H:%M:%S'))
    return render_template('index.html')


@app.route('/download/<filename>')
def download(filename):
    start = datetime.utcnow()
    task = send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    end = datetime.utcnow()
    delta = end - start
    delta = str(delta).split('.')[0]
    info = {'server': server.vps_name,
            'location': server.location,
            'ip': server.ip,
            'download_time': delta,
            'endtime': end.strftime("%d-%m-%Y %H:%M:%S")}
    with open(f'logs/upload/{filename}.json', 'w') as f:
        json.dump(info, f)

    return task


# @app.route('/profile/<filename>', methods=['GET'])
# def profile(filename):
#     log_path = '/var/log/nginx/access.log'
#     with open(log_path, "r") as f:
#         for line in f:
#             if re.search(filename, line):
#                 print(line.strip())



def send_file(server, file):
    info_about_replication = dict(
        zip({i for i in hosts.keys() if i.split(' ')[0] != server.vps_name}, [None] * len(hosts)))
    for i in hosts:
        if i.split(' ')[0] != server.vps_name:
            start = datetime.utcnow()
            host = hosts[i]['host']
            password = hosts[i]['pass']
            print(host, password)
            username = 'root'
            remote_dir = '/root/test_task/flaskProject/uploads'
            local_file = file

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, port=22, username=username, password=password)

            sftp = ssh.open_sftp()
            remote_file = remote_dir + '/' + local_file.split('/')[-1]
            sftp.put(file, remote_file)
            sftp.close()
            ssh.close()
            end = datetime.utcnow()
            delta = end - start
            delta = str(delta).split('.')[0]
            link = file.split('/')[-1]
            info_about_replication[i] = host, delta, end.strftime("%d-%m-%Y %H:%M:%S"), link

        else:
            continue
    file = file.split('/')[-1]
    with open(f'logs/replication/{file}.json', 'w') as f:
        json.dump(info_about_replication, f)

    return info_about_replication

@app.route('/replication/<filename>', methods=['GET'])
def show_replication(filename):
    filename = f'logs/replication/{filename}.json'
    with open(filename, 'r') as f:
        info_about_replication = json.load(f)
    response = ''
    if not info_about_replication:
        return 'Replication is not finished yet. Please, wait a few seconds'
    for i in info_about_replication:
        if info_about_replication[i] is None:
            return 'Replication is not finished yet. Please, wait a few seconds'
        host, delta, endtime, link = info_about_replication[i]
        response += f'{server.vps_name} -> {i} {host}, {delta}, {endtime},' \
        f'<a href="/download/{ link }">senkiv.online/download/{link}</a> <br>'
    return render_template('info_about_replication.html', info_about_replication=response)


@app.route('/info/<filename>', methods=['GET'])
def info_about_upload(filename):
    path = f'logs/upload/{filename}.json'
    with open(path, 'r') as f:
        info = json.load(f)
        vps_name, location, ip, download_time, endtime = info.values()
    return render_template('info_about_upload.html',
                           vps_name=vps_name,
                           location=location,
                           ip=ip,
                           download_time=download_time,
                           endtime=endtime)


