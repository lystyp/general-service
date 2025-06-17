from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
import requests
import secrets
import os
import logging
import json
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-default-secret-key')

# 設定 JSON 格式的 logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # 只在 Flask 應用程式上下文中嘗試存取 g 物件
        try:
            if hasattr(g, 'request_id'):
                log_entry['request_id'] = g.request_id
            else:
                log_entry['request_id'] = None
        except RuntimeError:
            # 沒有應用程式上下文時
            log_entry['request_id'] = None
        
        # 添加額外的上下文資訊
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'http_method'):
            log_entry['http_method'] = record.http_method
        if hasattr(record, 'http_url'):
            log_entry['http_url'] = record.http_url
        if hasattr(record, 'http_status'):
            log_entry['http_status'] = record.http_status
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
            
        return json.dumps(log_entry, ensure_ascii=False)

# 配置 logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 設定自定義格式器
logger = logging.getLogger(__name__)
for handler in logger.handlers:
    handler.setFormatter(JsonFormatter())
for handler in logging.getLogger().handlers:
    handler.setFormatter(JsonFormatter())

@app.before_request
def before_request():
    """在每個請求前生成唯一的請求 ID"""
    g.request_id = str(uuid.uuid4())
    g.start_time = datetime.now(timezone.utc)
    
    # 記錄請求開始
    logger.info(
        f"Request started: {request.method} {request.url}",
        extra={
            'http_method': request.method,
            'http_url': request.url,
            'user_agent': request.headers.get('User-Agent', ''),
            'remote_addr': request.remote_addr,
            'headers': dict(request.headers)
        }
    )

@app.after_request
def after_request(response):
    """在每個請求後記錄響應詳情"""
    if hasattr(g, 'start_time'):
        response_time = (datetime.now(timezone.utc) - g.start_time).total_seconds()
    else:
        response_time = None
        
    logger.info(
        f"Request completed: {request.method} {request.url}",
        extra={
            'http_method': request.method,
            'http_url': request.url,
            'http_status': response.status_code,
            'response_time': response_time,
            'content_length': response.content_length
        }
    )
    return response

# LINE Login 設定
LINE_CHANNEL_ID = os.getenv('LINE_CHANNEL_ID')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_LOGIN_CALLBACK_URL = os.getenv('LINE_LOGIN_CALLBACK_URL', 'http://localhost:8080/callback')

# LINE API URLs
LINE_AUTH_URL = 'https://access.line.me/oauth2/v2.1/authorize'
LINE_TOKEN_URL = 'https://api.line.me/oauth2/v2.1/token'
LINE_PROFILE_URL = 'https://api.line.me/v2/profile'

@app.route('/')
def hello_world():
    return 'Hello, World! <br><a href="/login">點擊這裡進行 LINE 登入</a>'

@app.route('/login')
def login():
    """顯示登入頁面"""
    if not LINE_CHANNEL_ID:
        return "請設定 LINE_CHANNEL_ID 環境變數", 500
    
    # 生成 state 參數以防止 CSRF 攻擊
    state = secrets.token_urlsafe(32)
    session['state'] = state
    
    # 建立 LINE 登入 URL
    line_login_url = f"{LINE_AUTH_URL}?" \
                    f"response_type=code&" \
                    f"client_id={LINE_CHANNEL_ID}&" \
                    f"redirect_uri={LINE_LOGIN_CALLBACK_URL}&" \
                    f"state={state}&" \
                    f"scope=profile"
    
    return render_template('login.html', line_login_url=line_login_url)

@app.route('/callback')
def callback():
    """處理 LINE 登入回調"""
    code = request.args.get('code')
    state = request.args.get('state')
    
    # 驗證 state 參數
    if not state or state != session.get('state'):
        logger.error(
        f"State parameter mismatch: expected {session.get('state')}, got {state}",
        extra={
            'event_type': 'login_error',
            'error_type': 'state_mismatch',
            'expected_state': session.get('state'),
            'received_state': state
        }
    )
        return "登入失敗：狀態驗證錯誤", 400
    
    if not code:
        logger.error(
        "No authorization code received from LINE",
        extra={
            'event_type': 'login_error',
            'error_type': 'no_auth_code',
            'request_args': dict(request.args)
        }
    )
        return "登入失敗：未收到授權碼", 400
    
    try:
        # 獲取存取權杖
        access_token = get_access_token(code)
        if not access_token:
            return "登入失敗：無法獲取存取權杖", 400
        
        # 獲取用戶資料
        user_data = get_user_profile(access_token)
        if not user_data:
            return "登入失敗：無法獲取用戶資料", 400
        
        # 記錄用戶資料
        logger.info(
            f"User login successful: {user_data.get('displayName', 'Unknown')}",
            extra={
                'user_id': user_data.get('userId'),
                'user_name': user_data.get('displayName'),
                'user_picture': user_data.get('pictureUrl'),
                'event_type': 'user_login'
            }
        )
        
        # 儲存用戶資料到 session
        session['user_data'] = user_data
        session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return redirect(url_for('success'))
        
    except Exception as e:
        logger.error(
            f"Login process failed: {str(e)}",
            extra={
                'event_type': 'login_error',
                'error_type': 'exception',
                'error_message': str(e),
                'error_class': e.__class__.__name__
            }
        )
        return f"登入失敗：{str(e)}", 500

@app.route('/success')
def success():
    """顯示登入成功頁面"""
    user_data = session.get('user_data')
    login_time = session.get('login_time')
    
    if not user_data:
        return redirect(url_for('login'))
    
    return render_template('success.html', user_data=user_data, login_time=login_time)

@app.route('/logout')
def logout():
    """登出功能"""
    user_data = session.get('user_data', {})
    logger.info(
        f"User logout: {user_data.get('displayName', 'Unknown')}",
        extra={
            'user_id': user_data.get('userId', 'Unknown'),
            'user_name': user_data.get('displayName', 'Unknown'),
            'event_type': 'user_logout',
            'session_duration': session.get('login_time')
        }
    )
    
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/user')
def api_user():
    """API：獲取當前用戶資料"""
    user_data = session.get('user_data')
    if not user_data:
        logger.warning(
            "API access attempted without login",
            extra={
                'event_type': 'unauthorized_access',
                'endpoint': '/api/user',
                'session_id': session.get('session_id')
            }
        )
        return jsonify({'error': 'Not logged in'}), 401
    
    logger.info(
        f"API user data requested by {user_data.get('displayName', 'Unknown')}",
        extra={
            'event_type': 'api_access',
            'endpoint': '/api/user',
            'user_id': user_data.get('userId'),
            'user_name': user_data.get('displayName')
        }
    )
    
    return jsonify({
        'user': user_data,
        'login_time': session.get('login_time')
    })

def get_access_token(code):
    """使用授權碼獲取存取權杖"""
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': LINE_LOGIN_CALLBACK_URL,
        'client_id': LINE_CHANNEL_ID,
        'client_secret': LINE_CHANNEL_SECRET
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.post(LINE_TOKEN_URL, data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('access_token')
    else:
        logger.error(f"Token request failed: {response.text}")
        return None

def get_user_profile(access_token):
    """使用存取權杖獲取用戶資料"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(LINE_PROFILE_URL, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Profile request failed: {response.text}")
        return None

if __name__ == '__main__':
    logger.debug("Starting Flask app...")
    app.run(host="127.0.0.1", port=8080, debug=True)
    print("Flask app is running at http://127.0.0.1:8080")