from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import secrets
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-default-secret-key')

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error("State parameter mismatch")
        return "登入失敗：狀態驗證錯誤", 400
    
    if not code:
        logger.error("No authorization code received")
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
        logger.info(f"User login: {user_data}")
        
        # 儲存用戶資料到 session
        session['user_data'] = user_data
        session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return redirect(url_for('success'))
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
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
    logger.info(f"User logout: {user_data.get('displayName', 'Unknown')} ({user_data.get('userId', 'Unknown')})")
    
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/user')
def api_user():
    """API：獲取當前用戶資料"""
    user_data = session.get('user_data')
    if not user_data:
        return jsonify({'error': 'Not logged in'}), 401
    
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
    app.run(host="127.0.0.1", port=8080, debug=True)
