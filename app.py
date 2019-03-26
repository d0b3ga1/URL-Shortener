# -*- coding:utf-8 -*-
import os
import string
import base64
import sqlite3
import string
from math import floor
from random import choice
from datetime import datetime
from urllib.parse import urlparse
from sqlite3 import OperationalError
from werkzeug.exceptions import HTTPException, NotFound
from flask import redirect, url_for, request, abort, jsonify
from flask import Flask, render_template, send_file, send_from_directory

try:
    from urllib.parse import urlparse  # Python 3
    str_encode = str.encode
except ImportError:
    from urlparse import urlparse  # Python 2
    str_encode = str
try:
    from string import ascii_lowercase
    from string import ascii_uppercase
except ImportError:
    from string import lowercase as ascii_lowercase
    from string import uppercase as ascii_uppercase
import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "urls.db")


app = Flask(__name__)
app.debug = True
host = 'http://localhost:5000/'

def table_check():
    ''' Kiểm tra và tạo database nếu chưa tồn tại
        Có 1 bảng WEB_URL gồm 4 trường:
            ID      : ID được chọn ngẫu nhiên từ hàm gen(c)
            URL     : URI gốc
            HITS    : lượt truy cập
            CREATED : thời gian tạo link rút gọn đó
    '''
    create_table = """
        CREATE TABLE WEB_URL(
            ID TEXT NOT NULL PRIMARY KEY
            ,URL TEXT NOT NULL
            ,HITS INTEGER NOT NULL
            ,CREATED TEXT NOT NULL
        );
        """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(create_table)
        except OperationalError:
            pass


@app.route('/', methods=['GET', 'POST'])
def home():
    ''' GET req : trả về trang chủ
        POST req: tạo link rút gọn và lưu vào db(SQLite3)
    '''
    if request.method == 'POST':
        def gen(c):
            '''Hàm tạo index cho link, tự tạo ngãu nhiên 
            gồm 6 kí tự số và chữ cái và kết hợp thành một string
            đã kiểm tra để không trùng lặp trong db
            @param
                c: là sqlite3.connect(db_path).cursor()
            '''
            chars = string.ascii_letters + string.digits
            length = 6
            code = ''.join(choice(chars) for x in range(length))
            # print("verifying", code)
            checkpoint = len(c.execute('SELECT * FROM WEB_URL WHERE ID=?', (code,)).fetchall())
            if checkpoint == 0: return code
            else:               gen(c)

        original_url = request.form.get('old')
        conn = sqlite3.connect('urls.db')
        c = conn.cursor()
        index_str = gen(c)
        
        if urlparse(original_url).scheme == '': url = 'http://' + original_url
        else                                  : url = original_url
        data = ( index_str, url, 0, str(datetime.now()) )
        c.execute(
            'INSERT INTO WEB_URL(ID, URL, HITS, CREATED) VALUES (?,?,?,?)'
            , data)
        conn.commit()

        return render_template(
            'index.html'
            , short_url=str(host + index_str)
            , old=url)
    return render_template("index.html")


@app.route('/<index_str>', methods=['GET'])
def redirect_short_url(index_str):
    url = host 
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    res = c.execute(
        'SELECT * FROM WEB_URL WHERE ID=?'
        , [index_str]).fetchone()
    try:
        if res is not None:
            c.execute(
                'UPDATE WEB_URL SET HITS = HITS + 1 WHERE ID=?', (res[0],))
            conn.commit()
            return redirect(res[1])
        else:
            return render_template('404.html'), 404
    except Exception:
        return render_template('404.html'), 404

@app.route('/stats', methods=['GET'])
def stats(offset=0):
    url = host
    offset=int(offset)
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    command = '''
        SELECT * FROM WEB_URL
        LIMIT 4 OFFSET ?;'''
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    stats = c.execute(command, (offset,)).fetchall()

    stats_all = c.execute('SELECT * FROM WEB_URL').fetchall()
    return render_template(
        "stats.html"
        , stats=stats
        , prev_num = ''
        , next_num = url+'stats/'+str(offset+4) if offset < len(stats_all) else '')

@app.route('/stats/<offset>', methods=['GET'])
def paginator(offset=0):
    url = host
    offset=int(offset)
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    command = '''
        SELECT * FROM WEB_URL
        LIMIT 4 OFFSET ?;'''
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    stats = c.execute(command, (offset,)).fetchall()

    stats_all = c.execute('SELECT * FROM WEB_URL').fetchall()
    return render_template(
        "stats.html"
        , stats=stats
        , prev_num = url+'stats/'+str(offset-4) if offset != 0 else ''
        , next_num = url+'stats/'+str(offset+4) if offset < len(stats_all) else '')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


if __name__ == '__main__':
    # This code checks whether database table is created or not
    table_check()
    app.run(host='0.0.0.0')
