# Flask Hello World Server with LINE Login

一個結合 LINE Login 功能的 Flask 伺服器應用程式。

## 功能特色

- LINE 登入整合
- 用戶資料顯示
- 登入/登出功能
- 用戶資料記錄
- 響應式 UI 設計

## 設定步驟

### 1. 安裝相依套件

```bash
pip install -r requirements.txt
```

### 2. 設定 LINE Login

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立一個新的 Channel (LINE Login)
3. 取得以下資訊：
   - Channel ID
   - Channel Secret
4. 在 Channel 設定中添加 Callback URL: `http://localhost:8080/callback`

### 3. 環境變數設定

複製 `.env.example` 為 `.env` 並填入您的 LINE Login 資訊：

```bash
cp .env.example .env
```

編輯 `.env` 文件：

```
LINE_CHANNEL_ID=your_channel_id_here
LINE_CHANNEL_SECRET=your_channel_secret_here
LINE_LOGIN_CALLBACK_URL=http://localhost:8080/callback
FLASK_SECRET_KEY=your_secret_key_here
```

### 4. 執行應用程式

```bash
python main.py
```

### 5. 測試

開啟瀏覽器並訪問：
- 主頁面：[http://127.0.0.1:8080/](http://127.0.0.1:8080/)
- 登入頁面：[http://127.0.0.1:8080/login](http://127.0.0.1:8080/login)

## API 端點

- `GET /` - 主頁面
- `GET /login` - 登入頁面
- `GET /callback` - LINE Login 回調處理
- `GET /success` - 登入成功頁面
- `GET /logout` - 登出
- `GET /api/user` - 獲取當前用戶資料 (JSON API)

## 記錄功能

應用程式會記錄以下用戶活動：
- 用戶登入時的完整資料
- 用戶登出活動
- 錯誤和異常情況

## 注意事項

1. 確保在 LINE Developers Console 中正確設定 Callback URL
2. 在生產環境中，請使用 HTTPS 並更新相應的 URL
3. 保護好您的 Channel Secret，不要將其提交到版本控制系統中
