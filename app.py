import os, sqlite3
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string, session, send_file, Response
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'demo-secret-key')
DB = os.path.join(os.path.dirname(__file__), 'data.db')
ME_NAME='野口'; ME_EMAIL='volca7000@gmail.com'

BASE_CSS = '''
<style>
:root{--bg:#f4f6fb;--nav:#1f2937;--primary:#2563eb;--line:#d8dee8;--muted:#64748b;--text:#0f172a;--card:#fff;}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:15px}.layout{display:flex;min-height:100vh}.side{width:245px;background:var(--nav);color:white;padding:26px 18px;flex-shrink:0}.side h2{font-size:20px;line-height:1.35;margin:0 0 28px}.side a{display:block;color:white;text-decoration:none;padding:12px 14px;border-radius:10px;margin-bottom:8px;font-weight:700}.side a:hover,.side a.active{background:#374151}.main{flex:1;padding:42px 46px}.top{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:20px}h1{font-size:28px;margin:0}.btn{border:1px solid #cfd7e3;background:white;color:#0f172a;text-decoration:none;border-radius:10px;padding:10px 16px;font-weight:800;cursor:pointer;display:inline-block}.btn.primary,button.primary{background:var(--primary);color:#fff;border-color:var(--primary)}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0 20px}.tabs a{padding:9px 14px;border-radius:999px;text-decoration:none;border:1px solid #cfd7e3;background:white;color:#0f172a}.tabs a.active{background:var(--primary);color:white}.mail-list{background:white;border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 8px 22px rgba(15,23,42,.05)}.mailrow{display:grid;grid-template-columns:86px 1fr 150px;gap:14px;text-decoration:none;color:#0f172a;padding:16px 18px;border-bottom:1px solid #e5eaf1}.mailrow:last-child{border-bottom:none}.mailrow:hover{background:#f8fafc}.badge{display:inline-block;font-size:12px;border-radius:999px;padding:4px 10px;font-weight:800}.badge.received{background:#ecfeff;color:#0e7490;border:1px solid #a5f3fc}.badge.sent{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe}.subject{font-size:16px;font-weight:900;margin-bottom:5px}.meta{font-size:13px;color:var(--muted);margin-bottom:7px}.preview{font-size:14px;color:#334155;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:780px}.right{text-align:right;font-size:12px;color:var(--muted)}.status{display:inline-block;margin-top:7px;font-size:12px;border:1px solid #cbd5e1;border-radius:999px;padding:3px 9px;background:#f8fafc;color:#334155}.pager{display:flex;justify-content:center;gap:8px;margin-top:24px}.pager a,.pager span{padding:9px 14px;border-radius:10px;border:1px solid #cfd7e3;background:#fff;color:#0f172a;text-decoration:none;font-weight:800}.pager .active{background:#2563eb;color:#fff}.pager .disabled{color:#94a3b8;background:#f8fafc}.thread-head{max-width:980px;margin:0 auto 16px}.bubble{max-width:900px;background:white;border:1px solid var(--line);border-radius:16px;margin:0 auto 18px;overflow:hidden;box-shadow:0 8px 22px rgba(15,23,42,.05)}.bubble.sent{margin-right:0}.bubble.received{margin-left:0}.bubble-head{display:flex;justify-content:space-between;gap:10px;padding:13px 16px;border-bottom:1px solid #e5eaf1;background:#f8fafc;align-items:center}.bubble-body{padding:18px;white-space:pre-wrap;line-height:1.75}.attach{display:inline-block;margin-top:12px;padding:9px 13px;border-radius:10px;background:#fff7ed;border:1px solid #fdba74;color:#9a3412;text-decoration:none;font-weight:800}.statusbox,.reply,.card{max-width:980px;margin:0 auto 18px;padding:18px;border-radius:16px;background:white;border:1px solid var(--line);box-shadow:0 8px 22px rgba(15,23,42,.05)}.statusbox{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.full{grid-column:1/-1}label{display:block;font-weight:800;margin-bottom:7px}input,textarea{width:100%;border:1px solid #cfd7e3;border-radius:11px;padding:12px;font-size:15px}textarea{min-height:170px;line-height:1.7;resize:vertical}.actions{display:flex;justify-content:flex-end;gap:10px;margin-top:16px}.count{font-size:13px;color:#64748b;margin-bottom:10px}.login{max-width:420px;margin:12vh auto;background:#fff;border:1px solid var(--line);border-radius:18px;padding:26px;box-shadow:0 10px 28px rgba(15,23,42,.08)}
@media(max-width:760px){.layout{display:block}.side{width:auto;padding:16px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}.side h2{width:100%;font-size:18px;margin:0 0 8px}.side a{margin:0;padding:9px 10px;font-size:13px}.main{padding:18px 12px}.top{align-items:flex-start}h1{font-size:22px}.tabs{gap:6px}.tabs a{font-size:13px;padding:8px 10px}.mailrow{grid-template-columns:1fr;padding:14px;gap:7px}.right{text-align:left}.preview{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}.bubble{margin-left:0!important;margin-right:0!important}.bubble-head{display:block}.grid{grid-template-columns:1fr}.actions{display:block}.actions .btn,.actions button{width:100%;margin-top:8px}.statusbox,.reply,.card{padding:14px}.thread-head{margin:0 0 14px}}
</style>
'''

def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; return con

def init_db():
    con=db()
    con.execute('CREATE TABLE IF NOT EXISTS mail_threads(id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, contact_name TEXT, contact_email TEXT, subject TEXT, related_code TEXT, status TEXT, updated_at TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS mail_messages(id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id INTEGER, direction TEXT, sent_at TEXT, sender_name TEXT, sender_email TEXT, recipient_name TEXT, recipient_email TEXT, body TEXT, attachment_name TEXT)')
    n=con.execute('SELECT COUNT(*) c FROM mail_threads').fetchone()['c']
    if n<25:
        con.execute('DELETE FROM mail_messages'); con.execute('DELETE FROM mail_threads')
        seed(con)
    con.commit(); con.close()

def insert_thread(con, client, name, email, subject, code, status, updated, body, attachment='', reply=False):
    cur=con.execute('INSERT INTO mail_threads(client,contact_name,contact_email,subject,related_code,status,updated_at) VALUES(?,?,?,?,?,?,?)',(client,name,email,subject,code,status,updated))
    tid=cur.lastrowid
    con.execute('INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name) VALUES(?,?,?,?,?,?,?,?,?)',(tid,'received',updated,name,email,ME_NAME,ME_EMAIL,body,attachment))
    if reply or status=='返信済み':
        rt=updated[:11]+'18:30'
        rb=f'{client}\n{name}様\n\nお世話になっております。\n株式会社M.T DICEの野口です。\n\nご連絡ありがとうございます。\n内容確認いたしました。\n引き続きよろしくお願いいたします。'
        con.execute('INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name) VALUES(?,?,?,?,?,?,?,?,?)',(tid,'sent',rt,ME_NAME,ME_EMAIL,name,email,rb,''))
        con.execute('UPDATE mail_threads SET updated_at=? WHERE id=?',(rt,tid))

def seed(con):
    base=[
('ソラボルジュエリー','金','taku@soraboljewelry.com','発注書SBJ-20260508-001の確認','SBJ-20260508-001','返信済み','2026/05/08 10:15','株式会社M.T DICE\n野口様\n\nK18製品用ブレスレットパーツ、PT900リング製品、SV925クロスチャーム製品について発注書を添付します。\n納品予定日は2026年5月15日でお願いいたします。','SBJ-20260508-001_ソラボルジュエリー_発注書.pdf'),
('ソラボルジュエリー','金','taku@soraboljewelry.com','請求書B021の送付','B021','返信済み','2026/05/18 13:37','野口様\n\n請求書確認いたしました。\n内容問題ございません。6月末支払い予定で進めます。','B021_ソラボルジュエリー_請求書.pdf'),
('リベルタ','井上','ayaka@libertaty.jp','D011 請求書送付の件','D011','未対応','2026/05/29 16:12','野口様\n\n請求書受領しました。\nPT900パーツの次回分についても近日中に相談させてください。','D011_リベルタ_請求書.pdf'),
('URUOI商事','綾田','tayata@uluoi.com','INV-202605-01 請求書送付','INV-202605-01','確認中','2026/05/10 18:06','野口様\n\n請求書ありがとうございます。社内確認して週明けに改めてご連絡します。\nペンダントトップの仕上がり、かなり良かったです。','INV-202605-01_URUOI商事_請求書.pdf'),
]
    for x in base: insert_thread(con,*x,reply=True)
    clients=[('ソラボルジュエリー','金','taku@soraboljewelry.com'),('リベルタ','井上','ayaka@libertaty.jp'),('URUOI商事','綾田','tayata@uluoi.com')]
    subjects=['K18丸カン追加加工のご相談','SV925パーツの数量変更について','OEM製造分のデザイン確認について','PT900リング製品のサイズ確認','18kパーツ試作分の確認','CADデザイン修正の件','ロジウムメッキ仕上げの濃さについて','PT900パーツ見積りのお願い','ルビーペンダントトップ中枠の確認','納品予定日の調整について','SV925パーツの仕上げ確認','OEM製造分の納品スケジュール','K18プレート刻印の件','請求書作成前の内容確認','石留め加工の仕上がり確認','GW明けの納品について','D011関連の確認','B021支払予定の確認','次回PT900加工のご相談','6月分OEMの事前相談','小さいチャームの加工相談','先日のパーツ確認ありがとうございました','リング画像確認しました','雑談：御徒町の件','K18チャーム追加分の概算について','SV925パーツ再加工の相談','OEM追加ロットの件','納品書の控えについて','18kパーツ次回数量について']
    for i,s in enumerate(subjects):
        c=clients[i%3]; month=12+(i//5); year=2025 if month<=12 else 2026; m=month if month<=12 else month-12; day=8+(i*3)%21
        date=f'{year}/{m:02d}/{day:02d} {9+i%9:02d}:{10+i*7%50:02d}'
        status=['未対応','確認中','返信済み'][i%3]
        body=f'野口様\n\nお世話になっております。\n{s}について確認です。\n加工内容・納期・金額感を一度確認させてください。\n\nたまに御徒町の話も混ざりますが、引き続きよろしくお願いいたします。'
        attach='' if i%4 else ['K18_ブレスレットパーツ_加工画像.svg','PT900_リング仕上げ画像.svg','SV925_クロスチャーム画像.svg','Pt900_ルビーペンダント画像.svg'][i%4]
        insert_thread(con,c[0],c[1],c[2],s,f'DMY-{i+1:03d}',status,date,body,attach,reply=(status=='返信済み'))

@app.before_request
def setup():
    init_db()

def logged_in(): return session.get('login')

def layout(content, active='mail'):
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>M.T DICE Mail</title>{BASE_CSS}</head><body><div class="layout"><aside class="side"><h2>M.T DICE<br>Mail Manager</h2><a class="{"active" if active=="dash" else ""}" href="/dashboard">ダッシュボード</a><a class="{"active" if active=="mail" else ""}" href="/mail">メール</a><a class="{"active" if active=="compose" else ""}" href="/mail/compose">新規作成</a></aside><main class="main">{content}</main></div></body></html>'

@app.route('/health')
def health(): return {'ok':True}

@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form.get('username') in ['admin','demo'] and request.form.get('password') in ['demo1234','admin']:
            session['login']=True; return redirect('/mail')
    return f'<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">{BASE_CSS}</head><body><div class="login"><h1>ログイン</h1><form method="post"><label>ID</label><input name="username" value="admin"><label>PW</label><input name="password" type="password" value="demo1234"><div class="actions"><button class="btn primary">ログイン</button></div></form></div></body></html>'

@app.route('/dashboard')
def dashboard():
    if not logged_in(): return redirect('/login')
    return layout('<div class="top"><h1>ダッシュボード</h1></div><div class="card">ジュエリー加工管理・メール管理システム</div>','dash')

@app.route('/mail')
def mail_list():
    if not logged_in(): return redirect('/login')
    box=request.args.get('box','all'); page=max(1,int(request.args.get('page',1))); per=10; off=(page-1)*per
    wh=''; title='すべてのメール'
    if box=='inbox': wh="WHERE EXISTS(SELECT 1 FROM mail_messages m WHERE m.thread_id=t.id AND m.direction='received')"; title='受信箱'
    elif box=='sent': wh="WHERE EXISTS(SELECT 1 FROM mail_messages m WHERE m.thread_id=t.id AND m.direction='sent')"; title='送信済み'
    elif box=='open': wh="WHERE t.status IS NULL OR t.status='' OR t.status='未対応' OR t.status='確認中'"; title='未対応'
    elif box=='replied': wh="WHERE t.status='返信済み'"; title='返信済み'
    con=db(); total=con.execute('SELECT COUNT(*) c FROM mail_threads t '+wh).fetchone()['c']; pages=max(1,(total+per-1)//per)
    page=min(page,pages); off=(page-1)*per
    rows=con.execute(f'''SELECT t.*, lm.body latest_body, lm.direction latest_direction, lm.sent_at latest_sent_at FROM mail_threads t LEFT JOIN mail_messages lm ON lm.id=(SELECT id FROM mail_messages m2 WHERE m2.thread_id=t.id ORDER BY id DESC LIMIT 1) {wh} ORDER BY t.updated_at DESC LIMIT ? OFFSET ?''',(per,off)).fetchall(); con.close()
    tabs=''.join([f'<a class="{"active" if box==b else ""}" href="/mail?box={b}">{n}</a>' for b,n in [('inbox','受信箱'),('sent','送信済み'),('all','すべてのメール'),('open','未対応'),('replied','返信済み')]])
    items=''.join([f'''<a class="mailrow" href="/mail/thread/{r['id']}"><div><span class="badge {'sent' if r['latest_direction']=='sent' else 'received'}">{'送信' if r['latest_direction']=='sent' else '受信'}</span></div><div><div class="subject">{r['subject']}</div><div class="meta">{r['client']} ｜ {r['contact_name']} &lt;{r['contact_email']}&gt; ｜ 関連番号：{r['related_code']}</div><div class="preview">{(r['latest_body'] or '').replace(chr(10),' ')}</div></div><div class="right"><div>{r['latest_sent_at'] or r['updated_at']}</div><span class="status">{r['status'] or '未対応'}</span></div></a>''' for r in rows]) or '<div class="card">該当するメールはありません。</div>'
    pager='<div class="pager">' + (f'<a href="/mail?box={box}&page={page-1}">前へ</a>' if page>1 else '<span class="disabled">前へ</span>') + ''.join([f'<span class="active">{p}</span>' if p==page else f'<a href="/mail?box={box}&page={p}">{p}</a>' for p in range(1,pages+1)]) + (f'<a href="/mail?box={box}&page={page+1}">次へ</a>' if page<pages else '<span class="disabled">次へ</span>') + '</div>'
    return layout(f'<div class="top"><h1>{title}</h1><a class="btn primary" href="/mail/compose">＋ 新規メール</a></div><div class="count">全 {total} 件 / {page}ページ目（全{pages}ページ）</div><div class="tabs">{tabs}</div><div class="mail-list">{items}</div>{pager}','mail')

@app.route('/mail/thread/<int:tid>', methods=['GET','POST'])
def thread(tid):
    if not logged_in(): return redirect('/login')
    con=db(); th=con.execute('SELECT * FROM mail_threads WHERE id=?',(tid,)).fetchone()
    if request.method=='POST':
        body=request.form.get('body','').strip(); attach=request.form.get('attachment_name','')
        if body or attach:
            now=datetime.now().strftime('%Y/%m/%d %H:%M')
            con.execute('INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name) VALUES(?,?,?,?,?,?,?,?,?)',(tid,'sent',now,ME_NAME,ME_EMAIL,th['contact_name'],th['contact_email'],body,attach))
            con.execute('UPDATE mail_threads SET status=?,updated_at=? WHERE id=?',('返信済み',now,tid)); con.commit()
        con.close(); return redirect(url_for('thread',tid=tid))
    msgs=con.execute('SELECT * FROM mail_messages WHERE thread_id=? ORDER BY id',(tid,)).fetchall(); con.close()
    statusbox=f'''<div class="statusbox"><strong>ステータス：{th['status'] or '未対応'}</strong>{''.join([f'<form method="post" action="/mail/thread/{tid}/status"><input type="hidden" name="status" value="{s}"><button class="btn">{s}にする</button></form>' for s in ['未対応','確認中','返信済み']])}</div>'''
    bubbles=''.join([f'''<div class="bubble {m['direction']}"><div class="bubble-head"><div><strong>{'送信' if m['direction']=='sent' else '受信'}</strong>　{m['sent_at']}</div><div class="meta">From {m['sender_name']} &lt;{m['sender_email']}&gt; → {m['recipient_name']} &lt;{m['recipient_email']}&gt; <form method="post" action="/mail/message/{m['id']}/delete" style="display:inline" onsubmit="return confirm('このメールを削除しますか？')"><button class="btn" style="padding:4px 8px;color:#dc2626">削除</button></form></div></div><div class="bubble-body">{m['body']}{f'<br><a class="attach" target="_blank" href="/mail/attachment/{m["attachment_name"]}">📎 {m["attachment_name"]}</a>' if m['attachment_name'] else ''}</div></div>''' for m in msgs])
    reply=f'''<div class="reply"><h2>メール返信</h2><form method="post"><label>添付資料名</label><input name="attachment_name" placeholder="例：見積書PDF、画像ファイル名など"><label>本文</label><textarea name="body" placeholder="返信内容を入力してください"></textarea><div class="actions"><button class="btn primary">送信する</button></div></form></div>'''
    return layout(f'<div class="thread-head"><div class="top"><div><h1>{th["subject"]}</h1><div class="meta">{th["client"]} ｜ {th["contact_name"]} ｜ {th["contact_email"]} ｜ 関連番号：{th["related_code"]}</div></div><a class="btn" href="/mail">戻る</a></div></div>{statusbox}{bubbles}{reply}','mail')

@app.route('/mail/thread/<int:tid>/status', methods=['POST'])
def upd_status(tid):
    if not logged_in(): return redirect('/login')
    s=request.form.get('status','未対応'); con=db(); con.execute('UPDATE mail_threads SET status=?,updated_at=? WHERE id=?',(s,datetime.now().strftime('%Y/%m/%d %H:%M'),tid)); con.commit(); con.close(); return redirect(url_for('thread',tid=tid))

@app.route('/mail/message/<int:mid>/delete', methods=['POST'])
def del_msg(mid):
    if not logged_in(): return redirect('/login')
    con=db(); row=con.execute('SELECT thread_id FROM mail_messages WHERE id=?',(mid,)).fetchone(); tid=row['thread_id'] if row else 1; con.execute('DELETE FROM mail_messages WHERE id=?',(mid,)); con.commit(); con.close(); return redirect(url_for('thread',tid=tid))

@app.route('/mail/compose', methods=['GET','POST'])
def compose():
    if not logged_in(): return redirect('/login')
    if request.method=='POST':
        client=request.form.get('client'); name=request.form.get('contact_name'); email=request.form.get('contact_email'); subject=request.form.get('subject'); code=request.form.get('related_code'); body=request.form.get('body'); attach=request.form.get('attachment_name','')
        con=db(); now=datetime.now().strftime('%Y/%m/%d %H:%M'); cur=con.execute('INSERT INTO mail_threads(client,contact_name,contact_email,subject,related_code,status,updated_at) VALUES(?,?,?,?,?,?,?)',(client,name,email,subject,code,'返信済み',now)); tid=cur.lastrowid
        con.execute('INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name) VALUES(?,?,?,?,?,?,?,?,?)',(tid,'sent',now,ME_NAME,ME_EMAIL,name,email,body,attach)); con.commit(); con.close(); return redirect(url_for('thread',tid=tid))
    form='''<div class="top"><h1>新規メール作成</h1><a class="btn" href="/mail">戻る</a></div><div class="card"><form method="post"><div class="grid"><div><label>宛先会社名</label><input name="client" value="ソラボルジュエリー"></div><div><label>担当者名</label><input name="contact_name" value="金様"></div><div><label>メールアドレス</label><input name="contact_email" value="taku@soraboljewelry.com"></div><div><label>関連番号</label><input name="related_code" value="MTD-202605-001"></div><div class="full"><label>件名</label><input name="subject" value="加工品確認の件"></div><div class="full"><label>本文</label><textarea name="body">ソラボルジュエリー株式会社\n金様\n\nお世話になっております。\n株式会社M.T DICEの野口です。\n\n下記加工品につきまして、内容をご確認いただけますでしょうか。\n\n・K18製作用パーツ\n・Pt900/SV925製品\n・納品予定日：2026年5月15日\n\nご確認のほど、よろしくお願いいたします。</textarea></div><div class="full"><label>添付資料名</label><input name="attachment_name" placeholder="例：見積書PDF、発注書PDF"></div></div><div class="actions"><a class="btn" href="/mail">キャンセル</a><button class="btn primary">送信済みとして保存</button></div></form></div>'''
    return layout(form,'compose')

@app.route('/mail/attachment/<path:name>')
def attachment(name):
    if name.lower().endswith('.svg'):
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600"><rect width="900" height="600" fill="#f8fafc"/><rect x="70" y="70" width="760" height="460" rx="28" fill="#fff" stroke="#cbd5e1" stroke-width="3"/><circle cx="320" cy="290" r="90" fill="none" stroke="#d4af37" stroke-width="18"/><circle cx="470" cy="290" r="70" fill="none" stroke="#94a3b8" stroke-width="14"/><text x="90" y="130" font-size="34" font-family="Arial" fill="#0f172a">{name}</text><text x="90" y="500" font-size="24" font-family="Arial" fill="#334155">ジュエリー加工確認用ダミー画像</text></svg>'
        return Response(svg, mimetype='image/svg+xml')
    pdf=b'%PDF-1.4\n1 0 obj<< /Type /Catalog /Pages 2 0 R>>endobj\n2 0 obj<< /Type /Pages /Kids[3 0 R]/Count 1>>endobj\n3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox[0 0 595 842] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R>>>>>>endobj\n4 0 obj<< /Length 80>>stream\nBT /F1 18 Tf 50 780 Td (Attachment PDF) Tj 0 -30 Td (Dummy file) Tj ET\nendstream endobj\n5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica>>endobj\ntrailer<< /Root 1 0 R>>\n%%EOF'
    return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition':f'inline; filename="{name}"'})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',8300)), debug=True)
