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

def parse_pagination(args):
    default_size = 20
    try:
        page = int(args.get('page')) if args.get('page') is not None else None
    except:
        page = None
    try:
        size = int(args.get('size')) if args.get('size') is not None else default_size
    except:
        size = default_size
    try:
        start = int(args.get('start')) if args.get('start') is not None else None
    except:
        start = None
    try:
        end = int(args.get('end')) if args.get('end') is not None else None
    except:
        end = None

    if page is not None and page > 0:
        limit = size if size > 0 else default_size
        offset = (page - 1) * limit
    else:
        if start is None:
            start = 0
        if end is None:
            end = start + default_size - 1
        if end < start:
            end = start
        limit = end - start + 1
        offset = start
    return offset, limit

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

# /downloadFile [hashes] -> {hashes:bin64} null代表不存在
@app.route('/downloadFile', methods=['POST'])
def downloadFile():
    data = request.get_data()
    data = str(data, encoding = 'utf-8')
    try:
        filehashes=json.loads(data)
        retmap={}
        for hashk in filehashes:
            filepath=os.path.join('./data/objs/', hashk + '.bin')
            if os.path.isfile(filepath):
                with open(filepath, 'rb') as f:
                    filebin=f.read()
                    filebin64=base64.b64encode(filebin)
                    retmap[hashk]=str(filebin64, encoding='utf-8')
            else:
                retmap[hashk]=None
        return {'ret':'','files': retmap}
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}

@app.route('/deleteRelease', methods=['POST'])
def deleteRelease():
    data = request.get_data()
    data = str(data, encoding = 'utf-8')
    try:
        info=json.loads(data)
        count=c.db.delete_release(info['githash'], info['projectname'], info['owner'])
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}
    return {'ret':'', 'count': count}

@app.route('/queryRelease', methods=['POST'])
def queryRelease():
    data = request.get_data()
    data = str(data, encoding = 'utf-8')
    try:
        info=json.loads(data)
        rows=c.db.find_exact_match(info['githash'], info['projectname'], info['owner'])
        retlist=[]
        for row in rows:
            retlist.append(row)
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}
    return {'ret':'', 'releases': retlist}

#/submitRelease {git hash, hash map, 工程文件一共4个json, 日期, owner, projectname, commiter} -> {count,files} 覆盖的条目数, 文件缺失
@app.route('/submitRelease', methods=['POST'])
def submitRelease():
    data = request.get_data()
    data = str(data, encoding = 'utf-8')
    try:
        info=json.loads(data)
        count,files=c.db.submit_release(info['githash'], info['projectname'], info['owner'], info['author'], info['filehashmap'], info['projectfile'], info['time'])
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}
    return {'ret':'', 'count': count, 'files': files}

@app.route('/api/owners', methods=['GET'])
def listOwners():
    try:
        owners = c.db.list_owners()
        return {'ret':'', 'owners': owners, 'total': len(owners)}
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}

@app.route('/api/projects', methods=['GET'])
def listProjects():
    try:
        offset, limit = parse_pagination(request.args)
        total = c.db.count_projects_global()
        projects = c.db.list_projects_global(offset, limit)
        return {'ret':'', 'projects': projects, 'total': total, 'offset': offset, 'limit': limit}
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}

@app.route('/api/owners/<owner>/projects', methods=['GET'])
def listProjectsByOwner(owner):
    try:
        offset, limit = parse_pagination(request.args)
        total = c.db.count_projects_by_owner(owner)
        projects = c.db.list_projects_by_owner(owner, offset, limit)
        return {'ret':'', 'projects': projects, 'total': total, 'offset': offset, 'limit': limit}
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}

@app.route('/api/projects/<owner>/<projectname>/commits', methods=['GET'])
def listCommits(owner, projectname):
    try:
        offset, limit = parse_pagination(request.args)
        total = c.db.count_commits(owner, projectname)
        commits = c.db.list_commits(owner, projectname, offset, limit)
        return {'ret':'', 'commits': commits, 'total': total, 'offset': offset, 'limit': limit}
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}

@app.route('/api/projects/<owner>/<projectname>/<githash>', methods=['GET'])
def getCommit(owner, projectname, githash):
    try:
        releases = c.db.find_exact_match(githash, projectname, owner)
        if not releases:
            abort(404)
        # return the first match while still reporting duplicates count if any
        return {'ret':'', 'release': releases[0], 'total': len(releases)}
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}

@app.route('/raw/<owner>/<projectname>/<githash>/<path:filepath>', methods=['GET'])
def serveRaw(owner, projectname, githash, filepath):
    try:
        releases = c.db.find_exact_match(githash, projectname, owner)
        if not releases:
            abort(404)
        release = releases[0]
        filehashmap = release.get('filehashmap', {})
        if filepath not in filehashmap:
            abort(404)
        hashk = filehashmap[filepath]
        binpath = os.path.join('./data/objs/', hashk + '.bin')
        if not os.path.isfile(binpath):
            abort(404)
        content = get_file(binpath)
        mimetype = get_mimetype(filepath)
        response = Response(content, mimetype=mimetype)
        if request.args.get('download') == '1':
            response.headers['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(filepath)
        return response
    except Exception as e:
        return {'ret':c.error_format,'error':str(e)}

if __name__ == '__main__':
    p('服务已启动...')
    app.run(host = c.ip, port = c.port, debug = False)
