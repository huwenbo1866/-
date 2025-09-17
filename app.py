from flask import Flask, request, redirect, jsonify, render_template_string,make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
from hashids import Hashids
from werkzeug.exceptions import HTTPException
from flask import abort
from flask.typing import ResponseReturnValue
import base62

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 对 str 进行 Base62 编码
def base62_encode_str(s: str) -> str:  # 定义返回类型
    # ’big‘ 表示高位在前，’little‘ 表示低位在前
    num = int.from_bytes(s.encode('utf-8'), 'big') # 先转为字节串再转为大整数
    return base62.encode(num)

# 对 Base62 编码的 str 进行解码
def base62_decode_str(s: str) -> str:  # 定义返回类型
    num = base62.decode(s)
    # 根据 bit 长度恢复字节流
    # ’//‘ 表示整除
    decoded_bytes = num.to_bytes((num.bit_length() + 7) // 8, 'big') # 先计算所需字节数（向上取整）
    return decoded_bytes.decode('utf-8') # 从字节串转回字符串


class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    original_url = db.Column(db.String(256), unique=True, nullable=False)
    short_code = db.Column(db.String(128), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)   # 点击次数
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment='创建时间'
    )
    outdate_after = db.Column(
       db.DateTime(timezone=True),
       default=lambda: datetime.now(timezone.utc)+timedelta(days=30),
       nullable=True,
       comment='过期时间'
       )
    #实例化方法
    def __init__(self, original_url: str, short_code: str = "temp"):
        self.original_url = original_url
        self.short_code = short_code

    def __repr__(self):
        return f"URLMap id={self.id} \nshort_code='{self.short_code}' \n"+\
               f"original_url='{self.original_url}' \noutdate_after: {self.outdate_after} \n"


@app.route('/')
def index():
    # 简单网页表单
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <title>URL Shortener</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body class="container py-5">
        <h2 class="mb-4">Flask URL Shortener</h2>
        <form action="/shorten" method="post" class="mb-3">
            <input type="text" name="original_url" placeholder="Enter URL for shortening" class="form-control mb-2" required>
            <button type="submit" class="btn btn-primary">Shorten</button>
        </form>
        {% if short_url %}
            <div class="alert alert-success">Short URL: <a href="{{ short_url }}" target="_blank">{{ short_url }}</a></div>
        {% endif %}
    </body>
    </html>
    ''', short_url=request.args.get("short_url"))


@app.route('/shorten', methods=['POST'])
def shorten_url():
    # 兼容 JSON 和表单
    if request.is_json:
        data = request.get_json()
        original_url = data.get("original_url")
    else:
        original_url = request.form.get("original_url")

    if not original_url:
        return abort(404, description="URL missing")
    # 检查是否已存在
    existing = URLMap.query.filter_by(original_url=original_url).first()
    if existing:
        if existing.outdate_after.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            db.session.delete(existing)
            db.session.commit()
            return abort(410,description = "URL expired")
        short_url = f"http://127.0.0.1:5000/{existing.short_code}"
    else:
        # 先插入占位
        new_entry = URLMap(original_url=original_url, short_code="temp")
        db.session.add(new_entry)
        db.session.commit()

        # 生成短码
        short_code = base62_encode_str(new_entry.original_url)
        short_code = short_code[:8]  
        new_entry.short_code = short_code
        db.session.commit()

        short_url = f"http://127.0.0.1:5000/{short_code}"

    # 如果是表单提交，跳转回首页显示结果
    if not request.is_json:
        return redirect(f"/?short_url={short_url}")

    return jsonify({"short_url": short_url}), 201


@app.route('/<short_code>')
def redirect_url(short_code):
    entry = URLMap.query.filter_by(short_code=short_code).first()
    if entry:
        entry.clicks += 1
        db.session.commit()
        print(entry)
        if not entry.original_url.startswith(("http://", "https://")):
            target_url = "http://" + entry.original_url
        else:
            target_url = entry.original_url
        return redirect(target_url, 302)
    else:
        return abort(404, description="URL NotFound")
@app.route('/stats/<short_code>')
def stats(short_code):
    entry = URLMap.query.filter_by(short_code=short_code).first()
    if entry:
        if entry.outdate_after.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
           db.session.delete(entry)
           db.session.commit()
           return abort(410,description = "URL expired")
        return jsonify({
            "original_url": entry.original_url,
            "short_code": entry.short_code,
            "clicks": entry.clicks,
            "created_at": entry.created_at.isoformat()
        }), 200
    else:
        abort(404, description="Short URL not found")

@app.errorhandler(Exception) #发生异常时调用的函数
def handle_error(e) -> ResponseReturnValue:
    if isinstance(e, HTTPException): #判断错误类型
        response = jsonify({
            "error": e.name,
            "message": str(e.description),
            "status_code": e.code,
            "path": request.path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return make_response(response, e.code)
    else:
        response = jsonify({
            "error": "InternalServerError",
            "message": str(e),
            "status_code": 500,
            "path": request.path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return make_response(response, 500)

@app.route('/registered_short_urls')
def registered_short_urls():
    all_entries = URLMap.query.all()
    result = [
        {
            "id": entry.id,
            "original_url": entry.original_url,
            "short_code": entry.short_code,
            "created_at": entry.created_at.isoformat(),
            "outdate_after": entry.outdate_after.isoformat(),
            "clicks": entry.clicks
        }
        for entry in all_entries if entry.outdate_after.replace(tzinfo=timezone.utc) >= datetime.now(timezone.utc)
    ]
    return jsonify(result), 200

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)
