# -*- coding: utf-8 -*-

import sys
import json
import os
import shutil
import base64

from flask import Flask, request, Response, abort
import mimetypes

import db as db_module

class c:
    ip='0.0.0.0'
    port=13496
    error_format='error format'
    db=db_module.DB()

def p(s):
    print(s)

p('')

# service part

app = Flask(__name__, static_folder='__static__')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(r):
    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Pragma'] = 'no-cache'
    r.headers['Expires'] = '0'
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

def is_sub(filename):
    try:
        return (os.path.realpath(filename) + os.sep).startswith(os.path.realpath('.') + os.sep)
    except:
        return True

def get_mimetype(path):
    return mimetypes.guess_type(path)[0] or 'application/octet-stream'

def get_file(path):
    if not os.path.isfile(path):
        abort(404)
        return None
    if not is_sub(path):
        abort(403)
        return None
    with open(path, 'rb') as f:
        content = f.read()
    return content 

@app.route('/', methods=['GET'])
def root():
    return static_file('index.html')

@app.route('/<path:path>', methods=['GET'])
def static_file(path):
    if os.path.isdir(path): 
        if not path.endswith('/'): path += '/'
        path += 'index.html'
    if not os.path.isfile(path):
        abort(404)
        return None
    mimetype = get_mimetype(path)
    response = Response(get_file(path), mimetype = mimetype)
    if mimetype.startswith('audio/'): response.headers['Accept-Ranges'] = 'bytes'
    return response

@app.route('/checkFile', methods=['POST'])
def checkFile():
    data = request.get_data()
    data = str(data, encoding = 'utf-8')
    try:
        filehashes=json.loads(data)
        ret={'ret':'','hashes': c.db.find_matching_filehash(filehashes)}
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}
    return ret

@app.route('/submitFile', methods=['POST'])
def submitFile():
    data = request.get_data()
    data = str(data, encoding = 'utf-8')
    try:
        filehash64Map=json.loads(data)
        filehashes=[]
        for hashk in filehash64Map:
            filehashes.append(hashk)
            filehash64=filehash64Map[hashk]
            with open(os.path.join('./data/objs/', hashk + '.bin'), 'wb') as f:
                f.write(base64.b64decode(filehash64))
        c.db.add_filehash(filehashes)
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}
    return {'ret':''}

if __name__ == '__main__':
    p('服务已启动...')
    app.run(host = c.ip, port = c.port, debug = False)
