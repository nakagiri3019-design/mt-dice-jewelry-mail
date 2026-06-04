M.T DICE ジュエリー加工管理システム WEB版スマホ確認用

ログイン:
ID: admin
PW: demo1234

Render設定:
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app

主な修正:
- WEB公開用の /health 追加
- スマホ対応CSS追加
- メール受信箱 10件表示 + 3ページ相当のダミーメール
- 受信箱 / 送信済み / すべて / 未対応 / 返信済み
- スレッド返信、削除、ステータス変更
- 添付PDF/画像の表示とクリック開封
- 返信欄の定型文を空欄化
