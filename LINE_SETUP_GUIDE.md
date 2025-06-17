# LINE Login 設定詳細指南

## 第一步：創建 LINE Login Channel

1. 訪問 [LINE Developers Console](https://developers.line.biz/)
2. 登入您的 LINE 帳號
3. 點擊 "Create a new provider" 或選擇現有的 Provider
4. 點擊 "Create a channel"
5. 選擇 "LINE Login"
6. 填寫以下資訊：
   - **Channel name**: 您的應用程式名稱
   - **Channel description**: 應用程式描述
   - **App types**: Web app
   - **Email address**: 您的聯絡信箱

## 第二步：設定 Channel

1. 在 Channel 基本設定頁面，找到：
   - **Channel ID**: 複製這個 ID
   - **Channel secret**: 點擊 "Issue" 生成並複製

2. 在 "LINE Login settings" 頁籤中：
   - **Callback URL**: 添加 `http://localhost:8080/callback`
   - **App types**: 確保勾選 "Web app"
   - **OpenID Connect**: 可選擇開啟

## 第三步：更新環境變數

編輯您的 `.env` 文件：

```bash
# 將以下值替換為您實際的 LINE Channel 資訊
LINE_CHANNEL_ID=您的Channel_ID
LINE_CHANNEL_SECRET=您的Channel_Secret
LINE_LOGIN_CALLBACK_URL=http://localhost:8080/callback
FLASK_SECRET_KEY=請生成一個隨機的長字串作為密鑰
```

## 測試流程

1. 啟動應用程式：`python main.py`
2. 訪問 http://127.0.0.1:8080/login
3. 點擊 "使用 LINE 帳號登入"
4. 在 LINE 授權頁面同意授權
5. 查看登入成功頁面和用戶資訊

## 故障排除

### 常見錯誤：

1. **"請設定 LINE_CHANNEL_ID 環境變數"**
   - 確保 `.env` 文件存在且包含正確的 Channel ID

2. **"登入失敗：狀態驗證錯誤"**
   - 可能是 CSRF 攻擊或會話過期，請重新嘗試登入

3. **"登入失敗：無法獲取存取權杖"**
   - 檢查 Channel Secret 是否正確
   - 確認 Callback URL 設定是否一致

4. **LINE 授權頁面顯示錯誤**
   - 檢查 Channel ID 是否正確
   - 確認 Callback URL 在 LINE Console 中已正確設定

## 生產環境部署注意事項

1. **使用 HTTPS**：
   - 更新 Callback URL 為 `https://yourdomain.com/callback`
   - 在 LINE Console 中更新相應設定

2. **環境變數管理**：
   - 使用更安全的方式管理環境變數
   - 不要將 `.env` 文件提交到版本控制

3. **錯誤處理**：
   - 添加更詳細的錯誤頁面
   - 實作更完善的日志系統
