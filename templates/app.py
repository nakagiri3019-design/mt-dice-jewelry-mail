from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, Response
from jinja2 import DictLoader
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3, os, csv, io


# Embedded templates for Render flat upload (prevents missing template/folder upload issues)
EMBEDDED_TEMPLATES = {'login.html': '<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>ログイン｜M.T DICE</title>\n<style>\nbody{margin:0;min-height:100vh;display:grid;place-items:center;background:#eef2f7;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif;color:#1f2937}\n.box{width:min(430px,92vw);background:#fff;border:1px solid #dbe2ea;border-radius:18px;padding:30px;box-shadow:0 14px 38px rgba(15,23,42,.14)}\nh1{font-size:23px;margin:0 0 8px}.sub{color:#6b7280;font-size:13px;margin-bottom:22px}\nlabel{font-size:12px;color:#6b7280;font-weight:700;display:block;margin:12px 0 6px}\ninput{width:100%;padding:12px;border:1px solid #dbe2ea;border-radius:10px;font:inherit}\nbutton{width:100%;margin-top:18px;padding:12px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:800;font:inherit}\n.err{background:#fef2f2;color:#dc2626;border:1px solid #fecaca;border-radius:10px;padding:10px;font-size:13px;margin-bottom:12px}\n.demo{margin-top:15px;color:#6b7280;font-size:12px;line-height:1.6;background:#f8fafc;padding:12px;border-radius:10px}\n</style>\n</head>\n<body><div class="box">\n<h1>M.T DICE Processing Manager</h1><div class="sub">ジュエリー加工管理システム 実用版</div>\n{% if error %}<div class="err">{{ error }}</div>{% endif %}\n<form method="post"><label>ユーザー名</label><input name="username" value="admin"><label>パスワード</label><input name="password" type="password" value="demo1234"><button>ログイン</button></form>\n<div class="demo">デモID：admin<br>デモPW：demo1234</div>\n</div></body></html>', 'dashboard.html': '<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>M.T DICE｜実用版v2</title>\n<style>:root{--bg:#f4f6f9;--nav:#1f2937;--nav2:#111827;--primary:#2563eb;--primary2:#1d4ed8;--text:#1f2937;--muted:#6b7280;--line:#dbe2ea;--card:#fff;--soft:#f8fafc;--green:#059669;--green-bg:#ecfdf5;--blue:#2563eb;--blue-bg:#eff6ff;--orange:#ea580c;--orange-bg:#fff7ed;--gray-bg:#f3f4f6;--red:#dc2626;--shadow:0 8px 24px rgba(15,23,42,.08)}\n*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif}.app{display:grid;grid-template-columns:245px 1fr;min-height:100vh}.sidebar{background:linear-gradient(180deg,var(--nav),var(--nav2));color:#fff;padding:22px 16px;position:sticky;top:0;height:100vh}.logo{font-weight:800;font-size:18px;line-height:1.4;margin-bottom:22px}.logo span{display:block;font-size:12px;color:#cbd5e1;font-weight:500;margin-top:4px}.menu{display:grid;gap:8px}.menu a{display:block;color:#e5e7eb;text-decoration:none;padding:11px 12px;border-radius:10px;font-size:14px}.menu a.active,.menu a:hover{background:rgba(255,255,255,.12)}.main{min-width:0}.topbar{background:#fff;border-bottom:1px solid var(--line);padding:18px 24px;display:flex;justify-content:space-between;align-items:center;gap:14px;position:sticky;top:0;z-index:5}.topbar h1{font-size:22px;margin:0}.topbar p{margin:5px 0 0;color:var(--muted);font-size:13px}.userbox{font-size:13px;color:var(--muted);text-align:right}.userbox strong{color:var(--text)}.content{padding:22px 24px;max-width:1520px}.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:18px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow)}.card-label{font-size:12px;color:var(--muted);margin-bottom:8px}.card-value{font-size:25px;font-weight:800}.card-value small{font-size:13px;color:var(--muted);font-weight:500}.toolbar{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:16px}.toolbar-left,.toolbar-right{display:flex;gap:8px;flex-wrap:wrap}button,input,select,textarea{font:inherit}button,.btn{border:1px solid var(--line);background:#fff;color:var(--text);border-radius:9px;padding:9px 12px;cursor:pointer;font-weight:700;font-size:13px;text-decoration:none;display:inline-block}button:hover,.btn:hover{border-color:#93c5fd;background:#f8fbff}button.primary,.btn.primary{background:var(--primary);border-color:var(--primary);color:#fff}.btn.primary:hover{background:var(--primary2)}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:18px}.panel-head{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;align-items:center;background:#fff}.panel-head h2{font-size:17px;margin:0}.panel-head span{font-size:12px;color:var(--muted)}.form-grid{padding:16px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px;background:var(--soft);border-bottom:1px solid var(--line)}.form-grid.three{grid-template-columns:repeat(3,1fr)}.field label{font-size:12px;color:var(--muted);display:block;margin-bottom:5px;font-weight:700}.field input,.field select,.field textarea{width:100%;border:1px solid var(--line);background:#fff;border-radius:9px;padding:10px;color:var(--text)}.field.wide{grid-column:span 3}.field.full{grid-column:1/-1}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px;min-width:1120px}th,td{border-bottom:1px solid var(--line);padding:11px 10px;text-align:left;vertical-align:middle}th{background:#f8fafc;color:#475569;font-size:12px;white-space:nowrap}tbody tr:hover td{background:#f9fbff}.num{text-align:right;white-space:nowrap}.status{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:12px;font-weight:800;white-space:nowrap}.s預り{background:var(--gray-bg);color:#374151}.s加工中{background:var(--blue-bg);color:var(--blue)}.s納品準備{background:var(--orange-bg);color:var(--orange)}.s納品済,.s請求済{background:var(--green-bg);color:var(--green)}.actions{display:flex;gap:6px;flex-wrap:wrap}.actions button,.actions .btn{padding:6px 8px;font-size:12px;border-radius:8px}.danger{color:var(--red)!important;border-color:#fecaca!important;background:#fff!important}.note{padding:14px 16px;color:#475569;font-size:13px;line-height:1.7;background:#fbfdff}.mail-row{cursor:pointer}.mail-row:hover td{background:#eef6ff!important}.hint{font-size:12px;color:#6b7280;margin-left:8px}.footer{color:var(--muted);font-size:12px;text-align:right;padding:2px 4px 18px}.logout{color:#fff;background:#475569;border-color:#475569;text-decoration:none;border-radius:8px;padding:8px 10px}.searchbar{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:10px;padding:14px 16px;background:#fff;border-bottom:1px solid var(--line)}@media(max-width:1100px){.app{grid-template-columns:1fr}.sidebar{display:none}.cards{grid-template-columns:repeat(2,1fr)}.form-grid,.form-grid.three,.searchbar{grid-template-columns:repeat(2,1fr)}.field.wide{grid-column:span 2}}@media(max-width:640px){.cards{grid-template-columns:1fr}.form-grid,.form-grid.three,.searchbar{grid-template-columns:1fr}.field.wide{grid-column:span 1}}@media print{.sidebar,.topbar,.toolbar,.form-grid,.actions,.searchbar{display:none!important}.app{display:block}body{background:#fff}.content{padding:0}.panel,.card{box-shadow:none;border:1px solid #bbb}table{min-width:0;font-size:11px}th,td{padding:6px}}</style>\n</head>\n<body>\n<div class="app">\n<aside class="sidebar">\n  <div class="logo">M.T DICE<br>Processing Manager<span>実用版 v2</span></div>\n  <nav class="menu">\n    <a class="active" href="#">ダッシュボード</a>\n    <a href="#clients">取引先</a>\n    <a href="#ledger">預り品台帳</a>\n    <a href="/mail">メール受信箱</a><a href="#mail">メール履歴</a>\n    <a href="#files">添付資料</a>\n    <a href="#invoice">納品・請求</a>\n    <a href="/report" target="_blank">提出用レポート</a><a href="/payment_schedule" target="_blank">入金予定一覧</a>\n  </nav>\n</aside>\n<main class="main">\n<div class="topbar">\n  <div><h1>ジュエリー加工管理</h1><p>預り品・加工進捗・納品請求・メール履歴・添付資料管理</p></div>\n  <div class="userbox">確認者：<strong>野口修造</strong><br>最終更新：{{ updated }}\u3000<a class="logout" href="/logout">ログアウト</a></div>\n</div>\n<div class="content">\n<div class="cards">\n  <div class="card"><div class="card-label">預り件数</div><div class="card-value">{{ total }}<small> 件</small></div></div>\n  <div class="card"><div class="card-label">加工中</div><div class="card-value">{{ progress }}<small> 件</small></div></div>\n  <div class="card"><div class="card-label">納品・請求済</div><div class="card-value">{{ done }}<small> 件</small></div></div>\n  <div class="card"><div class="card-label">全体請求予定額</div><div class="card-value">{{ amount|yen }}</div></div>\n  <div class="card"><div class="card-label">請求済対象額</div><div class="card-value">{{ due_amount|yen }}</div></div>\n</div>\n\n<div class="toolbar">\n  <div class="toolbar-left">\n    <a class="btn primary" href="#addPanel">＋ 預り登録</a>\n    <a class="btn" href="/report" target="_blank">提出用レポート</a>\n    <a class="btn" href="/payment_schedule" target="_blank">入金予定一覧</a>\n    <a class="btn" href="/backup">バックアップCSV</a>\n    <a class="btn" href="/csv/items">台帳CSV</a>\n    <a class="btn" href="/csv/messages">履歴CSV</a>\n    <button onclick="window.print()">画面PDF/印刷</button>\n  </div>\n</div>\n\n<section class="panel">\n  <div class="panel-head"><div><h2>検索・絞り込み</h2><span>取引先・品目・管理番号・ステータスで検索できます</span></div></div>\n  <form class="searchbar" method="get" action="/dashboard">\n    <input name="q" placeholder="キーワード検索" value="{{ q }}">\n    <select name="status"><option value="">全ステータス</option>{% for s in statuses %}<option value="{{s}}" {% if status_filter==s %}selected{% endif %}>{{s}}</option>{% endfor %}</select>\n    <select name="client"><option value="">全取引先</option>{% for c in clients %}<option value="{{c.name}}" {% if client_filter==c.name %}selected{% endif %}>{{c.name}}</option>{% endfor %}</select>\n    <button class="primary">検索</button>\n  </form>\n</section>\n\n<section class="panel" id="clients">\n<div class="panel-head"><div><h2>取引先マスター</h2><span>担当者・連絡先・締日・入金サイトを管理</span></div></div>\n<form method="post" action="/add_client" class="form-grid">\n  <div class="field"><label>取引先名</label><input name="name"></div>\n  <div class="field"><label>担当者</label><input name="person"></div>\n  <div class="field"><label>メール</label><input name="email"></div>\n  <div class="field"><label>電話</label><input name="phone"></div>\n  <div class="field"><label>締日</label><input name="closing_day" value="月末"></div>\n  <div class="field"><label>入金サイト</label><input name="payment_site" value="翌月末"></div>\n  <div class="field wide"><label>メモ</label><input name="memo"></div>\n  <div class="field"><button class="primary">取引先を追加</button></div>\n</form>\n<div class="table-wrap"><table>\n<thead><tr><th>取引先</th><th>担当者</th><th>メール</th><th>電話</th><th>締日</th><th>入金サイト</th><th>メモ</th></tr></thead>\n<tbody>{% for c in clients %}<tr><td>{{c.name}}</td><td>{{c.person}}</td><td>{{c.email}}</td><td>{{c.phone}}</td><td>{{c.closing_day}}</td><td>{{c.payment_site}}</td><td>{{c.memo}}</td></tr>{% endfor %}</tbody>\n</table></div></section>\n\n<section class="panel" id="addPanel">\n<div class="panel-head"><div><h2>新規預り登録</h2><span>受注加工・預かり加工の内容を登録します</span></div></div>\n<form method="post" action="/add_item" class="form-grid">\n  <div class="field"><label>管理番号（空欄可）</label><input name="code" placeholder="自動採番"></div>\n  <div class="field"><label>取引先</label><input name="client" value="リベルタ"></div>\n  <div class="field"><label>品目</label><input name="item" value="18Kパーツ"></div>\n  <div class="field"><label>素材</label><input name="material" value="18K"></div>\n  <div class="field"><label>数量</label><input name="qty" type="number" value="6"></div>\n  <div class="field"><label>加工内容</label><input name="work" value="パーツ加工・仕上げ"></div>\n  <div class="field"><label>預り日</label><input name="date" value="2026/06/04"></div>\n  <div class="field"><label>予定納品日</label><input name="due" value="2026/06/30"></div>\n  <div class="field"><label>請求予定額（税込）</label><input name="amount" type="number" value="220000"></div>\n  <div class="field"><label>状態</label><select name="status">{% for s in statuses %}<option>{{s}}</option>{% endfor %}</select></div>\n  <div class="field wide"><label>メモ</label><input name="memo"></div>\n  <div class="field"><button class="primary">登録する</button></div>\n</form></section>\n\n<section class="panel" id="ledger">\n<div class="panel-head"><div><h2>預り品・加工進捗台帳</h2><span>ステータス変更ボタンで進捗を更新できます</span></div></div>\n<div class="table-wrap"><table>\n<thead><tr><th>管理番号</th><th>預り日</th><th>取引先</th><th>品目</th><th>素材</th><th>数量</th><th>加工内容</th><th>予定納品日</th><th>請求予定額</th><th>状態</th><th>確認者</th><th>操作</th></tr></thead>\n<tbody>{% for x in items %}\n<tr><td>{{x.code}}</td><td>{{x.date}}</td><td>{{x.client}}</td><td>{{x.item}}</td><td>{{x.material}}</td><td class="num">{{x.qty}}</td><td>{{x.work}}</td><td>{{x.due}}</td><td class="num">{{x.amount|yen}}</td><td><span class="status s{{x.status}}">{{x.status}}</span></td><td>{{x.checker}}</td><td><div class="actions"><a href="/status/{{x.code}}/加工中"><button type="button">加工中</button></a><a href="/status/{{x.code}}/納品準備"><button type="button">納品準備</button></a><a href="/status/{{x.code}}/納品済"><button type="button">納品済</button></a><a href="/status/{{x.code}}/請求済"><button type="button">請求済</button></a><a class="btn" href="/edit_item/{{x.code}}">編集</a><a class="btn" href="/document/delivery/{{x.code}}" target="_blank">納品書</a><a class="btn" href="/document/invoice/{{x.code}}" target="_blank">請求書</a><a class="btn danger" href="/delete_item/{{x.code}}" onclick="return confirm(\'削除しますか？\')">削除</a></div></td></tr>\n{% endfor %}</tbody></table></div></section>\n\n<section class="panel" id="mail">\n<div class="panel-head"><div><h2>メール・連絡履歴 <span class="hint">※行をダブルクリックで詳細表示</span></h2><span>発注確認・納期確認・納品確認を案件ごとに記録</span></div></div>\n<form method="post" action="/add_message" class="form-grid three">\n  <div class="field"><label>日時</label><input name="date" placeholder="空欄なら現在時刻"></div>\n  <div class="field"><label>取引先</label><input name="client" value="リベルタ"></div>\n  <div class="field"><label>関連管理番号</label><input name="related_code" placeholder="MTD-202606-001"></div>\n  <div class="field"><label>分類</label><select name="kind"><option>受注確認</option><option>納期確認</option><option>納品確認</option><option>請求確認</option><option>その他</option></select></div>\n  <div class="field"><label>件名</label><input name="subject" value="加工内容確認の件"></div>\n  <div class="field"><label>担当者</label><input name="person" value="担当者"></div>\n  <div class="field"><label>添付資料名</label><input name="attachment_name" value="加工依頼書"></div>\n  <div class="field wide"><label>内容メモ</label><textarea name="body" rows="3">加工内容、数量、納品予定について確認済み。</textarea></div>\n  <div class="field"><button class="primary">履歴を追加</button></div>\n</form>\n<div class="table-wrap"><table><thead><tr><th>詳細</th><th>日時</th><th>取引先</th><th>関連番号</th><th>分類</th><th>件名</th><th>担当者</th><th>内容メモ</th><th>添付資料</th><th>操作</th></tr></thead>\n<tbody>{% for m in messages %}\n<tr class="mail-row" onclick="location.href=\'/message/{{m.id}}\'" title="クリックで詳細を表示">\n  <td onclick="event.stopPropagation()"><a class="btn primary" href="/message/{{m.id}}">詳細</a></td>\n  <td>{{m.date}}</td>\n  <td>{{m.client}}</td>\n  <td>{{m.related_code}}</td>\n  <td>{{m.kind}}</td>\n  <td>{{m.subject}}</td>\n  <td>{{m.person}}</td>\n  <td>{{m.body}}</td>\n  <td>{{m.attachment_name}}</td>\n  <td onclick="event.stopPropagation()">\n    <div class="actions">\n      <a class="btn" href="/edit_message/{{m.id}}">編集</a>\n      <a class="btn danger" href="/delete_message/{{m.id}}" onclick="return confirm(\'削除しますか？\')">削除</a>\n    </div>\n  </td>\n</tr>\n{% endfor %}</tbody></table></div></section>\n\n<section class="panel" id="files">\n<div class="panel-head"><div><h2>添付資料管理</h2><span>写真・PDF・請求書・納品書などを案件に紐付け</span></div></div>\n<form method="post" action="/upload_file" enctype="multipart/form-data" class="form-grid">\n  <div class="field"><label>管理番号</label><input name="item_code" placeholder="MTD-202606-001"></div>\n  <div class="field"><label>取引先</label><input name="client" value="リベルタ"></div>\n  <div class="field"><label>資料区分</label><select name="category"><option>加工写真</option><option>請求書</option><option>納品書</option><option>加工依頼書</option><option>メール写し</option><option>その他</option></select></div>\n  <div class="field"><label>ファイル</label><input type="file" name="file"></div>\n  <div class="field"><button class="primary">アップロード</button></div>\n</form>\n<div class="table-wrap"><table><thead><tr><th>登録日時</th><th>管理番号</th><th>取引先</th><th>区分</th><th>ファイル名</th></tr></thead><tbody>{% for f in files %}<tr><td>{{f.uploaded_at}}</td><td>{{f.item_code}}</td><td>{{f.client}}</td><td>{{f.category}}</td><td><a href="/uploads/{{f.stored_name}}" target="_blank">{{f.original_name}}</a></td></tr>{% endfor %}</tbody></table></div></section>\n\n<section class="panel" id="invoice">\n<div class="panel-head"><div><h2>納品・請求管理</h2><span>納品済・請求済の案件を請求予定として一覧化</span></div></div>\n<div class="table-wrap"><table><thead><tr><th>請求書番号</th><th>取引先</th><th>請求対象</th><th>入金予定日</th><th>請求額（税込）</th><th>状態</th></tr></thead>\n<tbody>{% for x in items if x.status in ["納品済","請求済"] %}<tr><td>{% if "ソラボル" in x.client %}MTD-SOL-202606{% else %}MTD-LIB-202606{% endif %}</td><td>{{x.client}}</td><td>{{x.item}} / {{x.work}}</td><td>{{x.due}}</td><td class="num">{{x.amount|yen}}</td><td><span class="status s{{x.status}}">{{x.status}}</span></td></tr>{% endfor %}</tbody></table></div>\n<div class="note"><strong>提出用説明メモ：</strong><br>ジュエリー案件は在庫販売ではなく、受注加工・預かり加工が中心のため、通常の在庫表ではなく、預り品台帳・加工進捗・納品請求管理にて管理しております。取引先との発注確認・納期確認・納品確認はメール・連絡履歴として案件ごとに記録しています。</div></section>\n\n<div class="footer">株式会社M.T DICE｜Jewelry Processing Management System practical v2</div>\n</div></main></div></body></html>', 'report.html': '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><title>提出用レポート</title>\n<style>body{font-family:"Noto Sans JP",sans-serif;color:#111;margin:28px}h1{font-size:22px;border-bottom:2px solid #111;padding-bottom:8px}h2{font-size:16px;margin-top:24px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #bbb;padding:6px;text-align:left}th{background:#f2f2f2}.right{text-align:right}.meta{text-align:right;font-size:12px;color:#555}.note{font-size:12px;line-height:1.7;margin-top:12px}button{padding:8px 12px}@media print{button{display:none}}</style></head>\n<body><button onclick="window.print()">PDF保存/印刷</button><div class="meta">出力日時：{{updated}}\u3000確認者：野口修造</div><h1>株式会社M.T DICE ジュエリー加工管理 提出用レポート</h1>\n<h2>取引先一覧</h2><table><thead><tr><th>取引先</th><th>担当者</th><th>締日</th><th>入金サイト</th><th>メモ</th></tr></thead><tbody>{% for c in clients %}<tr><td>{{c.name}}</td><td>{{c.person}}</td><td>{{c.closing_day}}</td><td>{{c.payment_site}}</td><td>{{c.memo}}</td></tr>{% endfor %}</tbody></table>\n<h2>預り品・加工進捗台帳</h2><table><thead><tr><th>管理番号</th><th>預り日</th><th>取引先</th><th>品目</th><th>素材</th><th>数量</th><th>加工内容</th><th>予定納品日</th><th>金額</th><th>状態</th></tr></thead><tbody>{% for x in items %}<tr><td>{{x.code}}</td><td>{{x.date}}</td><td>{{x.client}}</td><td>{{x.item}}</td><td>{{x.material}}</td><td class="right">{{x.qty}}</td><td>{{x.work}}</td><td>{{x.due}}</td><td class="right">{{x.amount|yen}}</td><td>{{x.status}}</td></tr>{% endfor %}</tbody></table>\n<h2>メール・連絡履歴</h2><table><thead><tr><th>日時</th><th>取引先</th><th>関連番号</th><th>分類</th><th>件名</th><th>内容</th><th>添付</th></tr></thead><tbody>{% for m in messages %}<tr><td>{{m.date}}</td><td>{{m.client}}</td><td>{{m.related_code}}</td><td>{{m.kind}}</td><td>{{m.subject}}</td><td>{{m.body}}</td><td>{{m.attachment_name}}</td></tr>{% endfor %}</tbody></table>\n<h2>添付資料一覧</h2><table><thead><tr><th>登録日時</th><th>管理番号</th><th>取引先</th><th>区分</th><th>ファイル名</th></tr></thead><tbody>{% for f in files %}<tr><td>{{f.uploaded_at}}</td><td>{{f.item_code}}</td><td>{{f.client}}</td><td>{{f.category}}</td><td>{{f.original_name}}</td></tr>{% endfor %}</tbody></table>\n<div class="note">ジュエリー案件は在庫販売ではなく、受注加工・預かり加工が中心のため、通常の在庫表ではなく、預り品台帳・加工進捗・納品請求管理にて管理しております。</div></body></html>', 'edit_item.html': '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>預り品編集</title>\n<style>\nbody{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif;background:#f4f6f9;color:#1f2937;margin:0}\n.wrap{max-width:900px;margin:28px auto;background:#fff;border:1px solid #dbe2ea;border-radius:16px;padding:24px;box-shadow:0 8px 24px rgba(15,23,42,.08)}\nh1{margin:0 0 18px;font-size:22px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}\nlabel{font-size:12px;color:#6b7280;font-weight:700;display:block;margin-bottom:5px}\ninput,select,textarea{width:100%;padding:10px;border:1px solid #dbe2ea;border-radius:9px;font:inherit}\n.full{grid-column:1/-1}.actions{margin-top:18px;display:flex;gap:10px}\nbutton,a{padding:10px 14px;border-radius:9px;text-decoration:none;font-weight:700}\nbutton{border:0;background:#2563eb;color:#fff}a{border:1px solid #dbe2ea;color:#1f2937;background:#fff}\n</style></head><body><div class="wrap">\n<h1>預り品編集：{{ item.code }}</h1>\n<form method="post" class="grid">\n<div><label>預り日</label><input name="date" value="{{item.date}}"></div>\n<div><label>取引先</label><input name="client" value="{{item.client}}"></div>\n<div><label>品目</label><input name="item" value="{{item.item}}"></div>\n<div><label>素材</label><input name="material" value="{{item.material}}"></div>\n<div><label>数量</label><input name="qty" type="number" value="{{item.qty}}"></div>\n<div><label>予定納品日/入金予定日</label><input name="due" value="{{item.due}}"></div>\n<div><label>請求予定額</label><input name="amount" type="number" value="{{item.amount}}"></div>\n<div><label>状態</label><select name="status">{% for s in statuses %}<option {% if item.status==s %}selected{% endif %}>{{s}}</option>{% endfor %}</select></div>\n<div><label>確認者</label><input name="checker" value="{{item.checker}}"></div>\n<div class="full"><label>加工内容</label><input name="work" value="{{item.work}}"></div>\n<div class="full"><label>メモ</label><textarea name="memo" rows="4">{{item.memo}}</textarea></div>\n<div class="actions full"><button>保存</button><a href="/dashboard">戻る</a></div>\n</form></div></body></html>', 'payment_schedule.html': '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><title>入金予定一覧</title>\n<style>\nbody{font-family:"Noto Sans JP",sans-serif;margin:28px;color:#111}h1{font-size:22px;border-bottom:2px solid #111;padding-bottom:8px}.meta{text-align:right;color:#555;font-size:12px}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border:1px solid #bbb;padding:8px}th{background:#f2f2f2}.right{text-align:right}.total{font-weight:bold;background:#fafafa}button{padding:8px 12px}@media print{button{display:none}}</style>\n</head><body><button onclick="window.print()">PDF保存/印刷</button><div class="meta">出力日時：{{updated}}\u3000確認者：野口修造</div><h1>入金予定一覧</h1>\n<table><thead><tr><th>入金予定日</th><th>取引先</th><th>管理番号</th><th>内容</th><th>金額</th><th>状態</th></tr></thead><tbody>\n{% for r in rows %}<tr><td>{{r.due}}</td><td>{{r.client}}</td><td>{{r.code}}</td><td>{{r.item}}</td><td class="right">{{r.amount|yen}}</td><td>{{r.status}}</td></tr>{% endfor %}\n<tr class="total"><td colspan="4">合計</td><td class="right">{{total|yen}}</td><td></td></tr>\n</tbody></table></body></html>', 'document.html': '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><title>{{title}}</title>\n<style>\nbody{font-family:"Noto Sans JP",sans-serif;margin:36px;color:#111}.doc{max-width:760px;margin:auto}h1{text-align:center;letter-spacing:.2em}.top{display:flex;justify-content:space-between;margin-top:26px}.to{font-size:18px;border-bottom:1px solid #111;display:inline-block;padding-right:40px}.meta{text-align:right;font-size:13px;line-height:1.8}table{width:100%;border-collapse:collapse;margin-top:28px}th,td{border:1px solid #999;padding:10px}th{background:#f2f2f2}.right{text-align:right}.total{font-size:18px;font-weight:bold}.note{margin-top:24px;line-height:1.7}.stamp{margin-top:36px;text-align:right}.box{display:inline-block;border:1px solid #999;width:90px;height:90px;text-align:center;line-height:90px;color:#777}button{padding:8px 12px}@media print{button{display:none}}</style>\n</head><body><button onclick="window.print()">PDF保存/印刷</button><div class="doc">\n<h1>{{title}}</h1>\n<div class="top"><div><div class="to">{{item.client}} 御中</div><p>下記の通り{% if doc_type=="delivery" %}納品{% else %}ご請求{% endif %}申し上げます。</p></div>\n<div class="meta">発行日：{{updated}}<br>管理番号：{{item.code}}<br>株式会社M.T DICE<br>代表取締役\u3000野口修造</div></div>\n<table><thead><tr><th>品目</th><th>素材</th><th>加工内容</th><th>数量</th><th>金額</th></tr></thead>\n<tbody><tr><td>{{item.item}}</td><td>{{item.material}}</td><td>{{item.work}}</td><td class="right">{{item.qty}}</td><td class="right">{{item.amount|yen}}</td></tr>\n<tr><td colspan="4" class="right total">合計（税込）</td><td class="right total">{{item.amount|yen}}</td></tr></tbody></table>\n<div class="note">納品予定日／入金予定日：{{item.due}}<br>備考：{{item.memo}}</div>\n<div class="stamp">確認印欄<br><div class="box">社印</div></div>\n</div></body></html>', 'message_detail.html': '<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>メール詳細</title>\n<style>\nbody{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif;background:#f4f6f9;color:#1f2937;margin:0}\n.wrap{max-width:980px;margin:28px auto;padding:0 16px}\n.card{background:#fff;border:1px solid #dbe2ea;border-radius:16px;box-shadow:0 8px 24px rgba(15,23,42,.08);overflow:hidden;margin-bottom:16px}\n.head{padding:18px 20px;border-bottom:1px solid #dbe2ea;background:#fff;display:flex;justify-content:space-between;gap:16px}\nh1{font-size:22px;margin:0}.muted{color:#6b7280;font-size:13px}\n.body{padding:20px}.grid{display:grid;grid-template-columns:160px 1fr;gap:10px 16px;font-size:14px}.label{color:#6b7280;font-weight:700}\n.content{white-space:pre-wrap;line-height:1.8;background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:14px;margin-top:12px}\n.actions{display:flex;gap:8px;flex-wrap:wrap}.btn,button{border:1px solid #dbe2ea;background:#fff;color:#1f2937;border-radius:9px;padding:9px 12px;text-decoration:none;font-weight:700;font-size:13px}.primary{background:#2563eb;color:#fff;border-color:#2563eb}.danger{color:#dc2626;border-color:#fecaca}\ntable{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #e5e7eb;padding:10px;text-align:left}th{background:#f8fafc;color:#475569}\n@media print{.actions,.top-actions{display:none}.wrap{margin:0;max-width:none}.card{box-shadow:none;border:1px solid #aaa}}\n</style>\n</head>\n<body>\n<div class="wrap">\n  <div class="top-actions actions" style="margin-bottom:12px">\n    <a class="btn" href="/dashboard#mail">戻る</a>\n    <a class="btn" href="/edit_message/{{message.id}}">編集</a>\n    <button onclick="window.print()">PDF保存/印刷</button>\n  </div>\n\n  <div class="card">\n    <div class="head">\n      <div>\n        <h1>{{ message.subject }}</h1>\n        <div class="muted">{{ message.date }}\u3000｜\u3000{{ message.client }}\u3000｜\u3000{{ message.kind }}</div>\n      </div>\n      <div class="actions">\n        <span class="btn">関連番号：{{ message.related_code or "未設定" }}</span>\n      </div>\n    </div>\n    <div class="body">\n      <div class="grid">\n        <div class="label">取引先</div><div>{{ message.client }}</div>\n        <div class="label">担当者</div><div>{{ message.person }}</div>\n        <div class="label">分類</div><div>{{ message.kind }}</div>\n        <div class="label">添付資料名</div><div>{{ message.attachment_name }}</div>\n      </div>\n      <div class="content">{{ message.body }}</div>\n    </div>\n  </div>\n\n  {% if related_item %}\n  <div class="card">\n    <div class="head"><h1>関連する加工案件</h1></div>\n    <div class="body">\n      <table>\n        <tr><th>管理番号</th><th>取引先</th><th>品目</th><th>加工内容</th><th>予定日</th><th>金額</th><th>状態</th></tr>\n        <tr>\n          <td>{{ related_item.code }}</td><td>{{ related_item.client }}</td><td>{{ related_item.item }}</td>\n          <td>{{ related_item.work }}</td><td>{{ related_item.due }}</td><td>{{ related_item.amount|yen }}</td><td>{{ related_item.status }}</td>\n        </tr>\n      </table>\n    </div>\n  </div>\n  {% endif %}\n\n  <div class="card">\n    <div class="head"><h1>関連添付資料</h1><div class="muted">同じ管理番号または取引先に紐づく資料</div></div>\n    <div class="body">\n      <table>\n        <tr><th>登録日時</th><th>管理番号</th><th>区分</th><th>ファイル名</th></tr>\n        {% for f in related_files %}\n        <tr><td>{{f.uploaded_at}}</td><td>{{f.item_code}}</td><td>{{f.category}}</td><td><a href="/uploads/{{f.stored_name}}" target="_blank">{{f.original_name}}</a></td></tr>\n        {% else %}\n        <tr><td colspan="4">関連資料はまだ登録されていません。</td></tr>\n        {% endfor %}\n      </table>\n    </div>\n  </div>\n</div>\n</body>\n</html>', 'edit_message.html': '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n<title>メール履歴編集</title>\n<style>\nbody{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif;background:#f4f6f9;color:#1f2937;margin:0}\n.wrap{max-width:900px;margin:28px auto;background:#fff;border:1px solid #dbe2ea;border-radius:16px;padding:24px;box-shadow:0 8px 24px rgba(15,23,42,.08)}\nh1{margin:0 0 18px;font-size:22px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}\nlabel{font-size:12px;color:#6b7280;font-weight:700;display:block;margin-bottom:5px}\ninput,select,textarea{width:100%;padding:10px;border:1px solid #dbe2ea;border-radius:9px;font:inherit}\n.full{grid-column:1/-1}.actions{margin-top:18px;display:flex;gap:10px}\nbutton,a{padding:10px 14px;border-radius:9px;text-decoration:none;font-weight:700}\nbutton{border:0;background:#2563eb;color:#fff}a{border:1px solid #dbe2ea;color:#1f2937;background:#fff}\n</style></head><body><div class="wrap">\n<h1>メール履歴編集</h1>\n<form method="post" class="grid">\n<div><label>日時</label><input name="date" value="{{message.date}}"></div>\n<div><label>取引先</label><input name="client" value="{{message.client}}"></div>\n<div><label>関連管理番号</label><input name="related_code" value="{{message.related_code}}"></div>\n<div><label>分類</label><select name="kind">{% for k in ["受注確認","納期確認","納品確認","請求確認","その他"] %}<option {% if message.kind==k %}selected{% endif %}>{{k}}</option>{% endfor %}</select></div>\n<div class="full"><label>件名</label><input name="subject" value="{{message.subject}}"></div>\n<div><label>担当者</label><input name="person" value="{{message.person}}"></div>\n<div><label>添付資料名</label><input name="attachment_name" value="{{message.attachment_name}}"></div>\n<div class="full"><label>本文・内容メモ</label><textarea name="body" rows="8">{{message.body}}</textarea></div>\n<div class="actions full"><button>保存</button><a href="/message/{{message.id}}">戻る</a></div>\n</form></div></body></html>', 'mailbox.html': '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{ title or \'メール\' }}</title><style>\n:root{--bg:#f4f6f9;--nav:#1f2937;--primary:#2563eb;--text:#0f172a;--muted:#64748b;--line:#dbe2ea;--card:#fff;--soft:#f8fafc;--shadow:0 8px 24px rgba(15,23,42,.07)}\n*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif}.layout{display:grid;grid-template-columns:245px 1fr;min-height:100vh}.side{background:#1f2937;color:#fff;padding:24px 16px}.logo{font-weight:800;font-size:19px;line-height:1.35;margin-bottom:30px}.menu{display:grid;gap:8px}.menu a{color:#e5e7eb;text-decoration:none;padding:12px 14px;border-radius:10px}.menu a.active,.menu a:hover{background:rgba(255,255,255,.13)}.main{padding:48px 46px}.head{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}h1{margin:0;font-size:28px}.btn{border:1px solid var(--line);background:#fff;color:#1f2937;border-radius:10px;padding:10px 16px;text-decoration:none;font-weight:800;font-size:14px;display:inline-flex;align-items:center;gap:6px}.primary{background:var(--primary)!important;color:#fff!important;border-color:var(--primary)!important}.tabs{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0 20px}.tabs a{padding:10px 15px;border-radius:999px;text-decoration:none;border:1px solid #cfd7e3;background:#fff;color:#0f172a}.tabs a.active{background:#2563eb;color:#fff;border-color:#2563eb}.count{font-size:13px;color:var(--muted);margin:0 0 10px}.panel{background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);overflow:hidden}.mail-row{display:grid;grid-template-columns:86px 1fr 150px;gap:16px;padding:16px 18px;border-bottom:1px solid #e5eaf1;text-decoration:none;color:inherit;align-items:start}.mail-row:last-child{border-bottom:none}.mail-row:hover{background:#f8fafc}.badge{display:inline-block;font-size:12px;border-radius:999px;padding:4px 10px;font-weight:800}.badge.received{background:#ecfeff;color:#0e7490;border:1px solid #a5f3fc}.badge.sent{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe}.subject{font-size:16px;font-weight:850;margin-bottom:5px}.meta{font-size:13px;color:var(--muted);margin-bottom:7px}.preview{font-size:14px;color:#334155;line-height:1.45;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:820px}.right{text-align:right;font-size:12px;color:var(--muted)}.status{display:inline-block;margin-top:8px;font-size:12px;border:1px solid #cbd5e1;border-radius:999px;padding:3px 9px;background:#f8fafc;color:#334155}.pager{display:flex;justify-content:center;align-items:center;gap:8px;margin-top:24px}.pager a,.pager span{padding:9px 14px;border-radius:10px;border:1px solid #cfd7e3;background:#fff;color:#0f172a;text-decoration:none;font-weight:800}.pager .active{background:#2563eb;color:#fff;border-color:#2563eb}.pager .disabled{color:#94a3b8;background:#f8fafc}.empty{background:#fff;border:1px dashed #cbd5e1;border-radius:14px;padding:30px;color:var(--muted)}\n@media(max-width:900px){.layout{display:block}.side{position:sticky;top:0;z-index:10;width:auto;padding:14px 14px}.logo{font-size:16px;margin-bottom:10px}.menu{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}.menu a{white-space:nowrap;padding:9px 12px}.main{padding:22px 14px 32px}.head{align-items:flex-start;gap:12px}.head h1{font-size:24px}.btn{padding:10px 12px}.tabs{gap:7px;overflow-x:auto;flex-wrap:nowrap;padding-bottom:4px}.tabs a{white-space:nowrap;padding:8px 12px}.mail-row{grid-template-columns:1fr;gap:8px;padding:15px}.right{text-align:left;display:flex;gap:10px;align-items:center;justify-content:space-between}.preview{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}.pager{flex-wrap:wrap}.count{font-size:12px}}\n</style></head><body><div class="layout"><aside class="side"><div class="logo">M.T DICE<br>Mail Manager</div><nav class="menu"><a href="/dashboard">ダッシュボード</a><a class="active" href="{{ url_for(\'mail_inbox\', box=\'inbox\') }}">メール</a><a href="/mail/compose">新規作成</a></nav></aside><main class="main"><div class="head"><h1>{{ title or \'メール\' }}</h1><a class="btn primary" href="/mail/compose">＋ 新規メール</a></div><div class="count">全 {{ total }} 件 / {{ page }}ページ目（全{{ total_pages }}ページ）</div><div class="tabs"><a href="{{ url_for(\'mail_inbox\', box=\'inbox\') }}" class="{% if box==\'inbox\' %}active{% endif %}">受信箱</a><a href="{{ url_for(\'mail_inbox\', box=\'sent\') }}" class="{% if box==\'sent\' %}active{% endif %}">送信済み</a><a href="{{ url_for(\'mail_inbox\', box=\'all\') }}" class="{% if box==\'all\' %}active{% endif %}">すべてのメール</a><a href="{{ url_for(\'mail_inbox\', box=\'open\') }}" class="{% if box==\'open\' %}active{% endif %}">未対応</a><a href="{{ url_for(\'mail_inbox\', box=\'replied\') }}" class="{% if box==\'replied\' %}active{% endif %}">返信済み</a></div>{% if threads %}<div class="panel">{% for t in threads %}<a class="mail-row" href="{{ url_for(\'mail_thread\', thread_id=t.id) }}"><div>{% if t.latest_direction == \'sent\' %}<span class="badge sent">送信</span>{% else %}<span class="badge received">受信</span>{% endif %}</div><div><div class="subject">{{ t.subject }}</div><div class="meta">{{ t.client }} ｜ {{ t.contact_name }} &lt;{{ t.contact_email }}&gt;{% if t.related_code %} ｜ 関連番号：{{ t.related_code }}{% endif %}</div><div class="preview">{{ (t.last_body or \'本文なし\') | replace(\'\\\\n\',\' \') | replace(\'\\n\',\' \') }}</div></div><div class="right"><div>{{ t.last_at or t.updated_at }}</div><span class="status">{{ t.status or \'未対応\' }}</span></div></a>{% endfor %}</div>{% else %}<div class="empty">該当するメールはありません。</div>{% endif %}{% if total_pages > 1 %}<div class="pager">{% if page > 1 %}<a href="{{ url_for(\'mail_inbox\', box=box, page=page-1) }}">前へ</a>{% else %}<span class="disabled">前へ</span>{% endif %}{% for p in range(1,total_pages+1) %}{% if p==page %}<span class="active">{{p}}</span>{% else %}<a href="{{ url_for(\'mail_inbox\', box=box, page=p) }}">{{p}}</a>{% endif %}{% endfor %}{% if page < total_pages %}<a href="{{ url_for(\'mail_inbox\', box=box, page=page+1) }}">次へ</a>{% else %}<span class="disabled">次へ</span>{% endif %}</div>{% endif %}</main></div></body></html>', 'mail_thread.html': '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{{thread.subject}}</title><style>\n:root{--bg:#f4f6f9;--nav:#1f2937;--primary:#2563eb;--text:#0f172a;--muted:#64748b;--line:#dbe2ea;--card:#fff;--soft:#f8fafc;--shadow:0 8px 24px rgba(15,23,42,.07)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif}.layout{display:grid;grid-template-columns:245px 1fr;min-height:100vh}.side{background:#1f2937;color:#fff;padding:24px 16px}.logo{font-weight:800;font-size:19px;line-height:1.35;margin-bottom:30px}.menu{display:grid;gap:8px}.menu a{color:#e5e7eb;text-decoration:none;padding:12px 14px;border-radius:10px}.menu a.active,.menu a:hover{background:rgba(255,255,255,.13)}.main{padding:32px 46px}.thread{max-width:980px;margin:0 auto}.head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}h1{margin:0;font-size:26px}.meta{color:var(--muted);font-size:13px}.btn,button{border:1px solid var(--line);background:#fff;color:#1f2937;border-radius:9px;padding:9px 12px;text-decoration:none;font-weight:800;font-size:13px;cursor:pointer}.statusbox{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:16px;box-shadow:var(--shadow)}.bubble{background:#fff;border:1px solid var(--line);border-radius:16px;margin-bottom:14px;box-shadow:var(--shadow);overflow:hidden}.bubble.sent{margin-left:80px}.bubble.received{margin-right:80px}.bubble-head{padding:12px 16px;background:#f8fafc;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:10px;align-items:center}.bubble-body{padding:18px;white-space:pre-wrap;line-height:1.75}.attach{display:inline-block;margin-top:12px;background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:8px 11px;color:#9a3412;font-weight:800;text-decoration:none}.delete{border:1px solid #dc2626;color:#dc2626;background:#fff;border-radius:8px;padding:4px 10px;font-size:12px}.reply{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow);margin-top:18px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}.full{grid-column:1/-1}textarea,input{width:100%;border:1px solid var(--line);border-radius:10px;padding:10px;font:inherit}textarea{min-height:170px;line-height:1.7}.primary{background:#2563eb!important;color:white!important;border-color:#2563eb!important}\n@media(max-width:900px){.layout{display:block}.side{position:sticky;top:0;z-index:10;width:auto;padding:14px}.logo{font-size:16px;margin-bottom:10px}.menu{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}.menu a{white-space:nowrap;padding:9px 12px}.main{padding:20px 12px 32px}.head{display:block}.head h1{font-size:22px;margin-bottom:8px}.head>div:last-child{display:flex;gap:8px;margin-top:12px}.bubble.sent,.bubble.received{margin-left:0;margin-right:0}.bubble-head{display:block}.bubble-head .meta{margin-top:8px;word-break:break-all}.statusbox{align-items:flex-start}.grid{grid-template-columns:1fr}.reply{padding:14px}.attach{max-width:100%;overflow:hidden;text-overflow:ellipsis}.btn,button{padding:9px 11px}}\n@media print{.side,.head .btn,.head button,.reply,.statusbox,.delete{display:none}.layout{display:block}.main{padding:0}.bubble{box-shadow:none;border:1px solid #aaa}.bubble.sent,.bubble.received{margin-left:0;margin-right:0}}\n</style></head><body><div class="layout"><aside class="side"><div class="logo">M.T DICE<br>Mail Manager</div><nav class="menu"><a href="/dashboard">ダッシュボード</a><a class="active" href="/mail">メール</a><a href="/mail/compose">新規作成</a></nav></aside><main class="main"><div class="thread"><div class="head"><div><h1>{{thread.subject}}</h1><div class="meta">{{thread.client}}｜{{thread.contact_name}}｜{{thread.contact_email}}｜関連番号：{{thread.related_code}}</div></div><div><a class="btn" href="/mail">戻る</a><button onclick="window.print()">PDF保存/印刷</button></div></div><div class="statusbox"><strong>ステータス：{{ thread.status or \'未対応\' }}</strong>{% for s in [\'未対応\',\'確認中\',\'返信済み\'] %}<form method="post" action="{{ url_for(\'update_mail_thread_status\', thread_id=thread.id) }}" style="display:inline"><input type="hidden" name="status" value="{{s}}"><button type="submit">{{s}}にする</button></form>{% endfor %}</div>{% for m in mail_messages %}<div class="bubble {{m.direction}}"><div class="bubble-head"><div><strong>{% if m.direction==\'sent\' %}送信{% else %}受信{% endif %}</strong>\u3000{{m.sent_at}}</div><div class="meta">From {{m.sender_name}} &lt;{{m.sender_email}}&gt; → {{m.recipient_name}} &lt;{{m.recipient_email}}&gt; <form method="post" action="{{ url_for(\'delete_mail_message\', message_id=m.id) }}" onsubmit="return confirm(\'このメールを削除しますか？\');" style="display:inline"><button class="delete" type="submit">削除</button></form></div></div><div class="bubble-body">{{m.body | replace(\'\\\\n\',\'\\n\')}}{% if m.attachment_name %}<br><a class="attach" href="{{ url_for(\'mail_attachment\', filename=m.attachment_name) }}" target="_blank">📎 {{ attachment_display_name(m.attachment_name) }}</a>{% endif %}</div></div>{% endfor %}<div class="reply"><h2>メール返信</h2><form method="post" enctype="multipart/form-data"><div class="grid"><div class="full"><label>添付ファイル</label><input type="file" name="attachment_file" accept=".pdf,.png,.jpg,.jpeg,.svg,.xlsx,.xls,.docx,.doc"></div><div class="full"><label>本文</label><textarea name="body" placeholder="返信内容を入力してください"></textarea></div></div><button class="primary" type="submit">送信する</button></form></div></div></main></div></body></html>', 'mail_compose.html': '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>新規メール作成</title><style>\n:root{--bg:#f4f6f9;--nav:#1f2937;--primary:#2563eb;--text:#0f172a;--muted:#64748b;--line:#dbe2ea;--shadow:0 8px 24px rgba(15,23,42,.07)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif}.layout{display:grid;grid-template-columns:245px 1fr;min-height:100vh}.side{background:#1f2937;color:#fff;padding:24px 16px}.logo{font-weight:800;font-size:19px;line-height:1.35;margin-bottom:30px}.menu{display:grid;gap:8px}.menu a{color:#e5e7eb;text-decoration:none;padding:12px 14px;border-radius:10px}.menu a.active,.menu a:hover{background:rgba(255,255,255,.13)}.main{padding:48px 46px}.head{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}h1{font-size:28px;margin:0}.back{background:#fff;color:#1f2937;text-decoration:none;border:1px solid #cfd7e3;border-radius:10px;padding:10px 16px;font-weight:800}.card{max-width:980px;background:#fff;border:1px solid #d8dee8;border-radius:18px;padding:26px;box-shadow:var(--shadow)}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.full{grid-column:1/-1}label{display:block;font-size:14px;font-weight:800;margin-bottom:7px;color:#334155}input,textarea{width:100%;box-sizing:border-box;border:1px solid #cfd7e3;border-radius:11px;padding:12px 13px;font-size:15px;background:#fff}textarea{min-height:230px;line-height:1.75;resize:vertical}.hint{font-size:12px;color:#64748b;margin-top:5px}.actions{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}.btn{border:none;border-radius:11px;padding:12px 22px;font-weight:800;cursor:pointer;font-size:15px;text-decoration:none}.primary{background:#2563eb;color:#fff}.secondary{background:#fff;color:#1f2937;border:1px solid #cfd7e3}.sample{margin-top:18px;background:#f8fafc;border:1px dashed #cbd5e1;border-radius:14px;padding:14px 16px;color:#475569;font-size:13px;line-height:1.7}\n@media(max-width:900px){.layout{display:block}.side{position:sticky;top:0;z-index:10;width:auto;padding:14px}.logo{font-size:16px;margin-bottom:10px}.menu{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}.menu a{white-space:nowrap;padding:9px 12px}.main{padding:22px 14px 32px}.head{gap:12px}.head h1{font-size:24px}.card{padding:16px;border-radius:16px}.grid{grid-template-columns:1fr;gap:13px}textarea{min-height:220px}.actions{position:sticky;bottom:0;background:#fff;padding-top:12px}.btn{padding:11px 14px}}\n</style></head><body><div class="layout"><aside class="side"><div class="logo">M.T DICE<br>Mail Manager</div><nav class="menu"><a href="/dashboard">ダッシュボード</a><a href="/mail">メール</a><a class="active" href="/mail/compose">新規作成</a></nav></aside><main class="main"><div class="head"><h1>新規メール作成</h1><a class="back" href="/mail">戻る</a></div><div class="card"><form method="post" enctype="multipart/form-data"><div class="grid"><div><label>宛先会社名</label><input name="client" value="ソラボルジュエリー" placeholder="例：ソラボルジュエリー株式会社"></div><div><label>担当者名</label><input name="contact_name" value="金" placeholder="例：金"></div><div><label>メールアドレス</label><input name="contact_email" value="taku@soraboljewelry.com" placeholder="例：taku@soraboljewelry.com"></div><div><label>関連番号</label><input name="related_code" value="MTD-202605-001" placeholder="例：MTD-202605-001"></div><div class="full"><label>件名</label><input name="subject" value="加工品確認の件" placeholder="例：K18製作用パーツ・Pt900/SV925製品の件"></div><div class="full"><label>本文</label><textarea name="body">ソラボルジュエリー株式会社\n金様\n\nお世話になっております。\n株式会社M.T DICEの野口です。\n\n下記加工品につきまして、内容をご確認いただけますでしょうか。\n\n・K18製作用パーツ\n・Pt900/SV925製品\n・納品予定日：2026年5月15日\n\nご確認のほど、よろしくお願いいたします。</textarea><div class="hint">改行はそのままメール履歴に反映されます。</div></div><div class="full"><label>添付ファイル</label><input type="file" name="attachment_file" accept=".pdf,.png,.jpg,.jpeg,.svg,.xlsx,.xls,.docx,.doc"><div class="hint">PDF、画像、Excel、Wordなどを添付できます。</div></div></div><div class="sample">保存すると、送信済みメールとして新しいスレッドが作成されます。その後はスレッド画面で返信・削除・ステータス変更ができます。</div><div class="actions"><a class="btn secondary" href="/mail">キャンセル</a><button class="btn primary" type="submit">送信済みとして保存</button></div></form></div></main></div></body></html>'}

app = Flask(__name__)
app.jinja_loader = DictLoader(EMBEDDED_TEMPLATES)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
DB_PATH = os.environ.get("DB_PATH", "data.db")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DEMO_USER = os.environ.get("DEMO_USER", "admin")
DEMO_PASS = os.environ.get("DEMO_PASS", "demo1234")

STATUSES = ["預り", "加工中", "納品準備", "納品済", "請求済"]

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        person TEXT,
        email TEXT,
        phone TEXT,
        closing_day TEXT,
        payment_site TEXT,
        memo TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        date TEXT,
        client TEXT,
        item TEXT,
        material TEXT,
        qty INTEGER,
        work TEXT,
        due TEXT,
        amount INTEGER,
        status TEXT,
        checker TEXT,
        memo TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        client TEXT,
        kind TEXT,
        subject TEXT,
        person TEXT,
        body TEXT,
        attachment_name TEXT,
        related_code TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT,
        client TEXT,
        category TEXT,
        original_name TEXT,
        stored_name TEXT,
        uploaded_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mail_threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client TEXT,
        contact_name TEXT,
        contact_email TEXT,
        subject TEXT,
        related_code TEXT,
        status TEXT,
        updated_at TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mail_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id INTEGER,
        direction TEXT,
        sent_at TEXT,
        sender_name TEXT,
        sender_email TEXT,
        recipient_name TEXT,
        recipient_email TEXT,
        body TEXT,
        attachment_name TEXT
    )
    """)

    # WEB版スマホ確認用：受信箱が3ページ程度になるダミーメールを追加
    extra_threads = [
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "K18丸カン追加加工のご相談", "SBJ-202512-010", "未対応", "2025/12/18 09:22", "野口様\n\nお世話になっております。\nK18丸カンの追加加工について相談です。\n前回より少し小さめのサイズで検討しています。\n\n一度概算をいただけますでしょうか。", ""),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "SV925パーツの数量変更について", "LBT-202512-011", "返信済み", "2025/12/22 14:10", "野口様\n\nSV925パーツの数量を少し増やす可能性があります。\n年明けに正式な数量をお送りします。\n\n今年もお世話になりました。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "年明けOEM案件の打ち合わせ", "ULU-202601-003", "確認中", "2026/01/07 11:35", "野口様\n\n明けましておめでとうございます。\n年明けのOEM案件について、リングとペンダントを中心に進めたいです。\n\n今月中に一度内容を整理したいです。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "PT900リング製品のサイズ確認", "SBJ-202601-014", "返信済み", "2026/01/16 16:08", "野口様\n\nPT900リング製品のサイズについて確認です。\n3点のうち1点だけサイズを変更したい可能性があります。\n\n加工前に確認お願いします。", ""),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "18kパーツ試作分の確認", "LBT-202601-018", "未対応", "2026/01/24 10:40", "野口様\n\n18kパーツ試作分について、仕上がりイメージを確認したいです。\n可能でしたら、途中段階の写真をいただけますか。", "K18_ブレスレットパーツ_加工画像.svg"),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "CADデザイン修正の件", "ULU-202602-007", "返信済み", "2026/02/08 13:55", "野口様\n\nCADデザインの件、石座の高さを少し抑えた形で修正できますでしょうか。\n急ぎではありませんが、次回確認時に反映いただけると助かります。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "ロジウムメッキ仕上げの濃さについて", "SBJ-202602-009", "確認中", "2026/02/18 15:18", "野口様\n\nSV925クロスチャームのロジウムメッキ仕上げについて、前回より少し明るめにしたいです。\nいぶしは控えめでお願いします。", "SV925_クロスチャーム画像.svg"),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "PT900パーツ見積りのお願い", "LBT-202602-012", "返信済み", "2026/02/26 09:50", "野口様\n\nPT900パーツ4点分の見積りをお願いします。\n納期は5月末くらいを想定しています。\n\nよろしくお願いいたします。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "ルビーペンダントトップ中枠の確認", "ULU-202603-004", "未対応", "2026/03/04 12:12", "野口様\n\nPt900天然ルビーペンダントトップの中枠について確認です。\n石の高さに合わせて少しだけ余裕を持たせたいです。", "Pt900_ルビーペンダント画像.svg"),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "納品予定日の調整について", "SBJ-202603-011", "返信済み", "2026/03/13 17:21", "野口様\n\n次回納品分ですが、15日納品で問題ありません。\n午前中より午後のほうが受け取りやすいです。\n\nよろしくお願いいたします。", ""),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "SV925パーツの仕上げ確認", "LBT-202603-017", "確認中", "2026/03/22 10:04", "野口様\n\nSV925パーツの仕上げについて、少しマット寄りにできますか。\nブランドイメージ的に光りすぎない方が良さそうです。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "OEM製造分の納品スケジュール", "ULU-202604-002", "返信済み", "2026/04/02 16:36", "野口様\n\nOEM製造分の納品スケジュールを確認したいです。\n5月中旬までに一部だけ先に納品できますでしょうか。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "K18プレート刻印の件", "SBJ-202604-006", "未対応", "2026/04/07 09:31", "野口様\n\nK18プレートの刻印ですが、今回は小さめの刻印でお願いします。\n文字が潰れない程度で調整いただけると助かります。", ""),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "請求書作成前の内容確認", "LBT-202604-010", "返信済み", "2026/04/15 14:44", "野口様\n\n請求書作成前に内容だけ確認させてください。\n18kパーツ6点、SV925パーツ10点、PT900パーツ4点で合っていますでしょうか。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "石留め加工の仕上がり確認", "ULU-202604-013", "確認中", "2026/04/23 18:05", "野口様\n\n石留め加工の仕上がり、とても良かったです。\nレーザー刻印の位置だけ、次回少し内側に寄せられるか確認したいです。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "GW明けの納品について", "SBJ-202605-002", "返信済み", "2026/05/02 11:28", "野口様\n\nGW明けの納品について確認です。\n5月15日納品予定で進めていただければ大丈夫です。\n\n連休中はお休み取れそうですか？", ""),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "D011関連の確認", "LBT-202605-004", "未対応", "2026/05/12 15:19", "野口様\n\nD011の請求書に入れる内容ですが、18kパーツ、SV925パーツ、PT900パーツでお願いします。\n支払期日は6月30日で大丈夫です。", "D011_リベルタ_請求書.pdf"),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "請求書INV-202605-01の件", "ULU-202605-005", "返信済み", "2026/05/16 13:07", "野口様\n\nINV-202605-01の請求書について確認しました。\n金額2,607,000円で問題ありません。\n社内処理を進めます。", "INV-202605-01_URUOI商事_請求書.pdf"),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "B021支払予定の確認", "SBJ-202605-009", "確認中", "2026/05/21 10:58", "野口様\n\nB021の支払予定について、6月30日で処理予定です。\n念のため経理にも共有しておきます。", "B021_ソラボルジュエリー_請求書.pdf"),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "次回PT900加工のご相談", "LBT-202605-013", "未対応", "2026/05/27 17:46", "野口様\n\n次回のPT900加工について相談です。\nまだ正式ではありませんが、6月中に追加でお願いする可能性があります。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "6月分OEMの事前相談", "ULU-202606-001", "未対応", "2026/06/01 09:12", "野口様\n\n6月分のOEMについて、前回と近い内容で追加相談したいです。\nまた整理できたら仕様を送ります。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "小さいチャームの加工相談", "SBJ-202606-004", "未対応", "2026/06/04 12:20", "野口様\n\n小さいチャームの加工について相談です。\nK18とSV925で数種類作るかもしれません。\nまずは概算だけお願いできますか。", ""),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "先日のパーツ確認ありがとうございました", "LBT-202606-006", "返信済み", "2026/06/05 09:18", "野口様\n\n先日のパーツ確認ありがとうございました。\n次回分も同じ流れでお願いできると助かります。\n\n最近かなり暑いので、外回りお気をつけください。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "リング画像確認しました", "ULU-202606-008", "返信済み", "2026/06/05 13:32", "野口様\n\nリング画像確認しました。\n仕上がりの方向性は問題ありません。\n次はペンダントトップ側も同じ雰囲気でお願いします。", "PT900_リング仕上げ画像.svg"),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "雑談：御徒町の件", "SBJ-202606-010", "未対応", "2026/06/05 18:45", "野口様\n\nお疲れ様です。\n今日御徒町に行ったらかなり混んでいました。\n前に話していた工具のお店、少し安くなっていましたよ。\n\nまた近いうちに加工の件で連絡します。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "K18チャーム追加分の概算について", "SBJ-202606-011", "未対応", "2026/06/06 09:18", "野口様\n\nK18チャーム追加分について、正式発注前に概算だけ確認したいです。\n小さいチャームを3〜5種類ほど検討しています。\n\nよろしくお願いいたします。", ""),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "SV925パーツ再加工の相談", "LBT-202606-012", "確認中", "2026/06/06 10:42", "野口様\n\nSV925パーツの一部について、再加工が可能か確認したいです。\n大きな修正ではなく、表面の仕上げを少し整える程度です。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "OEM追加ロットの件", "ULU-202606-013", "未対応", "2026/06/06 13:05", "野口様\n\nOEM製造分について、追加ロットを検討しています。\n前回と同じデザインをベースに、石違いで進める案が出ています。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "納品書の控えについて", "SBJ-202606-014", "返信済み", "2026/06/07 11:22", "野口様\n\n先日の納品書の控えですが、社内確認用にもう一度見られるようにしておきたいです。", "ND-20260515-001_ソラボルジュエリー_納品書.pdf"),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "18kパーツ次回数量について", "LBT-202606-015", "未対応", "2026/06/07 15:36", "野口様\n\n18kパーツの次回数量ですが、前回より少し増えるかもしれません。\n6点から8点程度になる可能性があります。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "ルビーペンダントトップ画像の件", "ULU-202606-016", "返信済み", "2026/06/08 09:48", "野口様\n\nルビーペンダントトップの画像確認しました。\n中枠の見え方は問題ありません。", "Pt900_ルビーペンダント画像.svg"),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "検品確認書の記載について", "SBJ-202606-017", "確認中", "2026/06/08 14:11", "野口様\n\n検品確認書の記載について一点確認です。\nロジウムメッキ仕上げの項目は、対象品のみで問題ありません。", "CHK-20260515-001_検品仕上げ確認書.pdf"),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "PT900パーツ写真確認", "LBT-202606-018", "未対応", "2026/06/09 10:27", "野口様\n\nPT900パーツの写真確認をお願いしたいです。\n仕上げ前と仕上げ後で比較できると助かります。", "PT900_リング仕上げ画像.svg"),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "3D CADデータ確認日程", "ULU-202606-019", "確認中", "2026/06/09 16:54", "野口様\n\n3D CADデータの確認ですが、来週前半で一度見られそうです。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "雑談：工具店の件", "SBJ-202606-020", "未対応", "2026/06/10 12:06", "野口様\n\nお疲れ様です。\nこの前話していた工具店ですが、新しいルーペが入っていました。\n加工確認に使いやすそうでしたよ。", ""),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "請求書D011の社内確認", "LBT-202606-021", "返信済み", "2026/06/10 17:30", "野口様\n\n請求書D011の件、社内確認が進んでいます。\n支払期日は6月30日予定で問題ありません。", "D011_リベルタ_請求書.pdf"),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "次回OEMの石違い案", "ULU-202606-022", "未対応", "2026/06/11 09:15", "野口様\n\n次回OEMの石違い案について、社内でいくつか候補が出ています。\nルビー以外にサファイア系も検討中です。", ""),
        ("ソラボルジュエリー", "金", "taku@soraboljewelry.com", "SV925クロスチャーム次回分", "SBJ-202606-023", "確認中", "2026/06/11 14:48", "野口様\n\nSV925クロスチャームの次回分について、前回と同じ仕様で追加する可能性があります。\n数量はまだ未定ですが、5〜10点くらいになりそうです。", "SV925_クロスチャーム画像.svg"),
        ("リベルタ", "井上", "ayaka@libertaty.jp", "加工スケジュールの確認", "LBT-202606-024", "未対応", "2026/06/12 10:03", "野口様\n\n6月後半の加工スケジュールについて確認です。\n追加分を入れる場合、いつ頃までに内容を確定すればよいでしょうか。", ""),
        ("URUOI商事", "綾田", "tayata@uluoi.com", "仕上げ加工の追加相談", "ULU-202606-025", "返信済み", "2026/06/12 18:12", "野口様\n\n仕上げ加工について追加相談です。\nレーザー刻印と最終研磨をセットでお願いする形になるかもしれません。", ""),
    ]

    for client, name, email, subject, code, status, updated_at, body, attachment in extra_threads:
        exists = cur.execute("SELECT id FROM mail_threads WHERE related_code=?", (code,)).fetchone()
        if exists:
            continue
        cur.execute("""INSERT INTO mail_threads(client,contact_name,contact_email,subject,related_code,status,updated_at)
                       VALUES (?,?,?,?,?,?,?)""", (client, name, email, subject, code, status, updated_at))
        tid = cur.lastrowid
        cur.execute("""INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name)
                       VALUES (?,?,?,?,?,?,?,?,?)""", (tid, "received", updated_at, name, email, "野口", "volca7000@gmail.com", body, attachment))
        if status in ("返信済", "返信済み"):
            reply_at = updated_at[:11] + "18:40"
            reply_body = f"{client}\n{name}様\n\nお世話になっております。\n株式会社M.T DICEの野口です。\n\nご連絡ありがとうございます。\n内容確認いたしました。\n引き続きよろしくお願いいたします。"
            cur.execute("""INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name)
                           VALUES (?,?,?,?,?,?,?,?,?)""", (tid, "sent", reply_at, "野口", "volca7000@gmail.com", name, email, reply_body, ""))
            cur.execute("UPDATE mail_threads SET updated_at=? WHERE id=?", (reply_at, tid))

    con.commit()

    if cur.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0:
        seed_items = [
            ("MTD-202605-001","2026/05/08","ソラボルジュエリー","22Kネックレス","22K",2,"検品・チェーン調整・仕上げ","2026/06/30",660000,"請求済","野口修造","納品済み。請求対象。"),
            ("MTD-202605-002","2026/05/09","ソラボルジュエリー","ルビーチャーム","22K / ルビー",2,"石留め確認・磨き","2026/06/30",230000,"請求済","野口修造","納品済み。請求対象。"),
            ("MTD-202605-003","2026/05/10","ソラボルジュエリー","ダイヤモンドチャーム","22K / ダイヤ",1,"石留め・最終検品","2026/06/30",240000,"請求済","野口修造","納品済み。請求対象。"),
            ("MTD-202605-004","2026/05/13","リベルタ","18Kパーツ","18K",6,"パーツ加工・仕上げ","2026/06/30",220000,"加工中","野口修造","加工中。"),
            ("MTD-202605-005","2026/05/14","リベルタ","SV925パーツ","SV925",10,"研磨・検品","2026/06/30",30000,"加工中","野口修造","加工中。"),
            ("MTD-202605-006","2026/05/16","リベルタ","PT900パーツ","PT900",4,"成形・仕上げ","2026/06/30",110000,"納品準備","野口修造","納品準備中。"),
        ]
        cur.executemany("""INSERT INTO items
            (code,date,client,item,material,qty,work,due,amount,status,checker,memo)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", seed_items)
    if cur.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 0:
        cur.executemany("""INSERT INTO clients(name, person, email, phone, closing_day, payment_site, memo) VALUES (?,?,?,?,?,?,?)""", [
            ("ソラボルジュエリー","担当者","","","月末","翌月末","22Kネックレス・チャーム加工"),
            ("リベルタ","担当者","","","月末","翌月末","18K/SV925/PT900パーツ加工"),
        ])
    if cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0:
        cur.executemany("""INSERT INTO messages(date,client,kind,subject,person,body,attachment_name,related_code) VALUES (?,?,?,?,?,?,?,?)""", [
            ("2026/05/08 10:15","ソラボルジュエリー","見積依頼","K18製作用パーツ・Pt900/SV925製品の見積依頼","金様",
             "株式会社M.T DICE\n野口様\n\nお世話になっております。\nソラボルジュエリーの金です。\n\nK18ブレスレット用の製作用パーツにつきまして、下記内容でお見積りをお願いいたします。\n\n・K18クリップ\n・K18プレート\n・K18丸カン\n・K18ブレスレット用クラスプ\n\n数量は前回と同程度で考えておりますが、在庫状況に応じて調整いただいて構いません。\n\nまた、連休前にお願いしておりましたPt900リングおよびSV925ネックレスクロストップの納品予定日についても、あわせて確認させてください。\n\n可能であれば、今回追加でお願いするK18製作用パーツと一緒に納品いただけますと助かります。\n\nお手数ですが、金額と納品予定日をご確認のうえ、ご連絡いただけますでしょうか。\n\nよろしくお願いいたします。\n\nソラボルジュエリー株式会社\n金\nMAIL：taku@soraboljewelry.com",
             "見積依頼メール","MTD-202605-001"),
            ("2026/05/08 18:02","ソラボルジュエリー","見積回答","K18製作用パーツほか見積回答","金様",
             "ソラボルジュエリー株式会社\n金様\n\nお世話になっております。\n株式会社M.T DICEの野口です。\n\nご連絡ありがとうございます。\n\nK18ブレスレット用の製作用パーツにつきまして、下記内容でご用意可能です。\n\n・K18クリップ\n・K18プレート\n・K18丸カン\n・K18ブレスレット用クラスプ\n\n上記一式で、620,000円にてお見積りいたします。\n\nまた、連休前にご依頼いただいておりましたPt900リングおよびSV925ネックレスクロストップにつきましても、あわせて納品可能です。\n\n今回追加分のK18製作用パーツとあわせて、2026年5月15日にまとめて納品予定です。\n\nお見積り内容は下記の通りです。\n\n・K18ブレスレット用製作用パーツ一式　620,000円\n・Pt900リング・ペンダント製品　3点　660,000円\n・SV925ネックレスクロストップ製品　5点　360,000円\n・検品・仕上げ・梱包費　90,000円\n\n小計：1,730,000円\n消費税：173,000円\n税込合計：1,903,000円\n\n上記内容でよろしければ、納品準備を進めさせていただきます。\n\nご確認のほど、よろしくお願いいたします。\n\n株式会社M.T DICE\n代表取締役　野口修造",
             "見積書PDF","MTD-202605-001"),
            ("2026/05/08 20:10","ソラボルジュエリー","発注確認","正式発注のご連絡","金様",
             "株式会社M.T DICE\n野口様\n\nお世話になっております。\nソラボルジュエリーの金です。\n\nお見積りありがとうございます。\n\nご提示いただいた内容で、正式に発注いたします。\n発注書を添付いたしますので、ご確認ください。\n\n納品日は、5月15日でお願いいたします。\n\n今回追加分のK18製作用パーツと、連休前にお願いしていたPt900リングおよびSV925ネックレスクロストップを、まとめて納品いただけますと助かります。\n\nそれでは、上記内容で進めていただけますようお願いいたします。\n\nよろしくお願いいたします。\n\nソラボルジュエリー株式会社\n金\nMAIL：taku@soraboljewelry.com",
             "発注書PDF","MTD-202605-001"),
            ("2026/05/15 15:08","ソラボルジュエリー","納品報告","加工品納品完了のご報告","金様",
             "ソラボルジュエリー株式会社\n金様\n\nお世話になっております。\n株式会社M.T DICEの野口です。\n\nご発注いただいておりました下記商品につきまして、本日納品が完了いたしました。\n\n・K18ブレスレット用製作用パーツ一式\n・Pt900リング・ペンダント製品\n・SV925ネックレスクロストップ製品\n\n納品内容をご確認いただき、問題がございましたらお知らせください。\n\n請求書につきましては、別途お送りいたします。\n\nよろしくお願いいたします。\n\n株式会社M.T DICE\n代表取締役　野口修造",
             "納品書PDF","MTD-202605-001"),
            ("2026/05/19 15:08","ソラボルジュエリー","請求送付","請求書送付のご連絡","金様",
             "ソラボルジュエリー株式会社\n金様\n\nお世話になっております。\n株式会社M.T DICEの野口です。\n\n2026年5月15日に納品いたしました下記商品につきまして、請求書を添付にてお送りいたします。\n\n・K18ブレスレット用製作用パーツ一式\n・Pt900リング・ペンダント製品\n・SV925ネックレスクロストップ製品\n\n請求金額：1,903,000円（税込）\n支払期日：2026年6月30日\n\nご確認のほど、よろしくお願いいたします。\n\n株式会社M.T DICE\n代表取締役　野口修造",
             "請求書PDF","MTD-202605-001"),
            ("2026/05/19 15:11","ソラボルジュエリー","請求確認","請求書確認完了のご連絡","金様",
             "株式会社M.T DICE\n野口様\n\nお世話になっております。\nソラボルジュエリーの金です。\n\n請求書を確認いたしました。\n\n請求内容に相違ございません。\n\n今後ともよろしくお願いいたします。\n\nソラボルジュエリー株式会社\n金\nMAIL：taku@soraboljewelry.com",
             "請求確認メール","MTD-202605-001"),
            ("2026/05/24 15:45","リベルタ","納期確認","18K/SV925/PT900パーツ加工進捗","担当者","一部加工中。6月上旬納品予定として進行。","加工進捗表","MTD-202605-004"),
        ])

    if cur.execute("SELECT COUNT(*) FROM mail_threads").fetchone()[0] == 0:
        cur.execute("""INSERT INTO mail_threads(client,contact_name,contact_email,subject,related_code,status,updated_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    ("ソラボルジュエリー","金様","taku@soraboljewelry.com","K18製作用パーツ・Pt900/SV925製品の件","MTD-202605-001","返信済","2026/05/19 15:11"))
        thread_id = cur.lastrowid
        cur.executemany("""INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name)
                           VALUES (?,?,?,?,?,?,?,?,?)""", [
            (thread_id,"received","2026/05/08 10:15","金","taku@soraboljewelry.com","野口","volca7000@gmail.com",
             "株式会社M.T DICE\\n野口様\\n\\nお世話になっております。\\nソラボルジュエリーの金です。\\n\\nK18ブレスレット用の製作用パーツにつきまして、下記内容でお見積りをお願いいたします。\\n\\n・K18クリップ\\n・K18プレート\\n・K18丸カン\\n・K18ブレスレット用クラスプ\\n\\nまた、Pt900リングおよびSV925ネックレスクロストップの納品予定日についても、あわせて確認させてください。\\n\\nよろしくお願いいたします。",""),
            (thread_id,"sent","2026/05/08 18:02","野口","volca7000@gmail.com","金","taku@soraboljewelry.com",
             "ソラボルジュエリー株式会社\\n金様\\n\\nお世話になっております。\\n株式会社M.T DICEの野口です。\\n\\nK18ブレスレット用の製作用パーツにつきまして、下記内容でご用意可能です。\\n\\n・K18クリップ\\n・K18プレート\\n・K18丸カン\\n・K18ブレスレット用クラスプ\\n\\n税込合計：1,903,000円\\n納品予定日：2026年5月15日\\n\\nご確認のほど、よろしくお願いいたします。","見積書PDF"),
            (thread_id,"received","2026/05/08 20:10","金","taku@soraboljewelry.com","野口","volca7000@gmail.com",
             "株式会社M.T DICE\\n野口様\\n\\nお見積りありがとうございます。\\n\\nご提示いただいた内容で、正式に発注いたします。\\n発注書を添付いたしますので、ご確認ください。\\n\\n納品日は、5月15日でお願いいたします。","発注書PDF"),
            (thread_id,"sent","2026/05/15 15:08","野口","volca7000@gmail.com","金","taku@soraboljewelry.com",
             "ソラボルジュエリー株式会社\\n金様\\n\\nご発注いただいておりました商品につきまして、本日納品が完了いたしました。\\n\\n・K18ブレスレット用製作用パーツ一式\\n・Pt900リング・ペンダント製品\\n・SV925ネックレスクロストップ製品\\n\\n納品内容をご確認ください。","納品書PDF"),
            (thread_id,"sent","2026/05/19 15:08","野口","volca7000@gmail.com","金","taku@soraboljewelry.com",
             "ソラボルジュエリー株式会社\\n金様\\n\\n請求書を添付にてお送りいたします。\\n\\n請求金額：1,903,000円（税込）\\n支払期日：2026年6月30日\\n\\nご確認のほど、よろしくお願いいたします。","請求書PDF"),
            (thread_id,"received","2026/05/19 15:11","金","taku@soraboljewelry.com","野口","volca7000@gmail.com",
             "株式会社M.T DICE\\n野口様\\n\\n請求書を確認いたしました。\\n請求内容に相違ございません。\\n\\n今後ともよろしくお願いいたします。",""),
        ])

    con.commit()
    con.close()

init_db()

def mail_upload_dir():
    path = os.path.join(UPLOAD_DIR, "mail")
    os.makedirs(path, exist_ok=True)
    return path


def save_mail_attachment(file):
    if not file or not getattr(file, "filename", ""):
        return ""
    original = secure_filename(file.filename)
    if not original:
        return ""
    stored = datetime.now().strftime("%Y%m%d_%H%M%S_") + original
    file.save(os.path.join(mail_upload_dir(), stored))
    return stored


def attachment_display_name(filename):
    if not filename:
        return ""
    name = str(filename)
    parts = name.split("_", 2)
    if len(parts) == 3 and len(parts[0]) == 8 and len(parts[1]) == 6 and parts[0].isdigit() and parts[1].isdigit():
        return parts[2]
    return name


@app.context_processor
def inject_mail_helpers():
    return dict(attachment_display_name=attachment_display_name)


@app.route("/health")
def health():
    return {"ok": True, "app": "mt-dice-jewelry-mail-web"}


@app.route("/mail/attachment/<path:filename>")
def mail_attachment(filename):
    if not logged_in():
        return redirect(url_for("login"))
    return send_from_directory(mail_upload_dir(), filename, as_attachment=False)


def logged_in():
    return session.get("logged_in") is True

@app.template_filter("yen")
def yen(v):
    try:
        return "¥{:,.0f}".format(int(v or 0))
    except Exception:
        return "¥0"

@app.template_filter("nl2br")
def nl2br(v):
    return str(v or "").replace("\n", "<br>")

def get_dashboard_data():
    con = db()
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    client_filter = request.args.get("client", "").strip()
    sql = "SELECT * FROM items WHERE 1=1"
    params = []
    if q:
        sql += " AND (code LIKE ? OR client LIKE ? OR item LIKE ? OR material LIKE ? OR work LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like, like, like]
    if status:
        sql += " AND status=?"
        params.append(status)
    if client_filter:
        sql += " AND client=?"
        params.append(client_filter)
    sql += " ORDER BY id DESC"
    items = con.execute(sql, params).fetchall()
    clients = con.execute("SELECT * FROM clients ORDER BY name").fetchall()
    messages = con.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    files = con.execute("SELECT * FROM files ORDER BY id DESC").fetchall()
    total = con.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    progress = con.execute("SELECT COUNT(*) FROM items WHERE status='加工中'").fetchone()[0]
    done = con.execute("SELECT COUNT(*) FROM items WHERE status IN ('納品済','請求済')").fetchone()[0]
    amount = con.execute("SELECT COALESCE(SUM(amount),0) FROM items").fetchone()[0]
    due_amount = con.execute("SELECT COALESCE(SUM(amount),0) FROM items WHERE status IN ('納品済','請求済')").fetchone()[0]
    con.close()
    return dict(items=items, clients=clients, messages=messages, files=files, total=total,
                progress=progress, done=done, amount=amount, due_amount=due_amount,
                statuses=STATUSES, q=q, status_filter=status, client_filter=client_filter,
                updated=datetime.now().strftime("%Y/%m/%d %H:%M"))

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == DEMO_USER and request.form.get("password") == DEMO_PASS:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="ユーザー名またはパスワードが違います")
    if logged_in():
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not logged_in(): return redirect(url_for("login"))
    return render_template("dashboard.html", **get_dashboard_data())

@app.route("/add_item", methods=["POST"])
def add_item():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    count = con.execute("SELECT COUNT(*) FROM items").fetchone()[0] + 1
    code = request.form.get("code") or f"MTD-202606-{count:03d}"
    con.execute("""INSERT OR REPLACE INTO items(code,date,client,item,material,qty,work,due,amount,status,checker,memo)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (code, request.form.get("date"), request.form.get("client"), request.form.get("item"),
                 request.form.get("material"), int(request.form.get("qty") or 0), request.form.get("work"),
                 request.form.get("due"), int(request.form.get("amount") or 0), request.form.get("status") or "預り", "野口修造", request.form.get("memo","")))
    con.commit(); con.close()
    return redirect(url_for("dashboard"))

@app.route("/status/<code>/<status>")
def status(code, status):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    con.execute("UPDATE items SET status=? WHERE code=?", (status, code))
    con.commit(); con.close()
    return redirect(url_for("dashboard"))

@app.route("/delete_item/<code>")
def delete_item(code):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    con.execute("DELETE FROM items WHERE code=?", (code,))
    con.commit(); con.close()
    return redirect(url_for("dashboard"))

@app.route("/add_client", methods=["POST"])
def add_client():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    con.execute("INSERT INTO clients(name,person,email,phone,closing_day,payment_site,memo) VALUES (?,?,?,?,?,?,?)",
                (request.form.get("name"), request.form.get("person"), request.form.get("email"), request.form.get("phone"),
                 request.form.get("closing_day"), request.form.get("payment_site"), request.form.get("memo")))
    con.commit(); con.close()
    return redirect(url_for("dashboard"))

@app.route("/add_message", methods=["POST"])
def add_message():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    con.execute("INSERT INTO messages(date,client,kind,subject,person,body,attachment_name,related_code) VALUES (?,?,?,?,?,?,?,?)",
                (request.form.get("date") or datetime.now().strftime("%Y/%m/%d %H:%M"), request.form.get("client"), request.form.get("kind"),
                 request.form.get("subject"), request.form.get("person"), request.form.get("body"), request.form.get("attachment_name"), request.form.get("related_code")))
    con.commit(); con.close()
    return redirect(url_for("dashboard"))

@app.route("/upload_file", methods=["POST"])
def upload_file():
    if not logged_in(): return redirect(url_for("login"))
    f = request.files.get("file")
    if not f or f.filename == "":
        flash("ファイルが選択されていません")
        return redirect(url_for("dashboard"))
    original = f.filename
    safe = secure_filename(original)
    stored = datetime.now().strftime("%Y%m%d%H%M%S_") + safe
    f.save(os.path.join(UPLOAD_DIR, stored))
    con = db()
    con.execute("""INSERT INTO files(item_code,client,category,original_name,stored_name,uploaded_at)
                   VALUES (?,?,?,?,?,?)""",
                (request.form.get("item_code"), request.form.get("client"), request.form.get("category"),
                 original, stored, datetime.now().strftime("%Y/%m/%d %H:%M")))
    con.commit(); con.close()
    return redirect(url_for("dashboard"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    if not logged_in(): return redirect(url_for("login"))
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/report")
def report():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    items = con.execute("SELECT * FROM items ORDER BY id").fetchall()
    messages = con.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    files = con.execute("SELECT * FROM files ORDER BY id DESC").fetchall()
    clients = con.execute("SELECT * FROM clients ORDER BY name").fetchall()
    con.close()
    return render_template("report.html", items=items, messages=messages, files=files, clients=clients, updated=datetime.now().strftime("%Y/%m/%d %H:%M"))

@app.route("/csv/items")
def csv_items():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    rows = con.execute("SELECT code,date,client,item,material,qty,work,due,amount,status,checker,memo FROM items ORDER BY id").fetchall()
    con.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["管理番号","預り日","取引先","品目","素材","数量","加工内容","予定納品日","請求予定額","状態","確認者","メモ"])
    for r in rows:
        writer.writerow(list(r))
    csv_data = "\ufeff" + output.getvalue()
    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=jewelry_items.csv"})

@app.route("/csv/messages")
def csv_messages():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    rows = con.execute("SELECT date,client,kind,subject,person,body,attachment_name,related_code FROM messages ORDER BY id").fetchall()
    con.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日時","取引先","分類","件名","担当者","内容","添付資料","関連管理番号"])
    for r in rows:
        writer.writerow(list(r))
    csv_data = "\ufeff" + output.getvalue()
    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=message_history.csv"})


@app.route("/edit_item/<code>", methods=["GET","POST"])
def edit_item(code):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    if request.method == "POST":
        con.execute("""UPDATE items SET date=?, client=?, item=?, material=?, qty=?, work=?, due=?, amount=?, status=?, checker=?, memo=? WHERE code=?""",
                    (request.form.get("date"), request.form.get("client"), request.form.get("item"), request.form.get("material"),
                     int(request.form.get("qty") or 0), request.form.get("work"), request.form.get("due"), int(request.form.get("amount") or 0),
                     request.form.get("status"), request.form.get("checker") or "野口修造", request.form.get("memo"), code))
        con.commit(); con.close()
        return redirect(url_for("dashboard"))
    item = con.execute("SELECT * FROM items WHERE code=?", (code,)).fetchone()
    clients = con.execute("SELECT * FROM clients ORDER BY name").fetchall()
    con.close()
    return render_template("edit_item.html", item=item, clients=clients, statuses=STATUSES)

@app.route("/payment_schedule")
def payment_schedule():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    rows = con.execute("""SELECT due, client, code, item, amount, status FROM items
                          WHERE due IS NOT NULL AND due != ''
                          ORDER BY due, client""").fetchall()
    total = con.execute("SELECT COALESCE(SUM(amount),0) FROM items WHERE due IS NOT NULL AND due != ''").fetchone()[0]
    con.close()
    return render_template("payment_schedule.html", rows=rows, total=total, updated=datetime.now().strftime("%Y/%m/%d %H:%M"))

@app.route("/document/<doc_type>/<code>")
def document(doc_type, code):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    item = con.execute("SELECT * FROM items WHERE code=?", (code,)).fetchone()
    con.close()
    title = "納品書" if doc_type == "delivery" else "請求書"
    return render_template("document.html", item=item, title=title, doc_type=doc_type, updated=datetime.now().strftime("%Y/%m/%d"))

@app.route("/backup")
def backup():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["TYPE","管理番号","預り日/日時","取引先","品目/分類","素材/件名","数量/担当者","内容","予定日","金額","状態","確認者/添付"])
    for x in con.execute("SELECT * FROM items ORDER BY id").fetchall():
        writer.writerow(["ITEM", x["code"], x["date"], x["client"], x["item"], x["material"], x["qty"], x["work"], x["due"], x["amount"], x["status"], x["checker"]])
    for m in con.execute("SELECT * FROM messages ORDER BY id").fetchall():
        writer.writerow(["MESSAGE", m["related_code"], m["date"], m["client"], m["kind"], m["subject"], m["person"], m["body"], "", "", "", m["attachment_name"]])
    con.close()
    csv_data = "\ufeff" + output.getvalue()
    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=mtdice_backup.csv"})


@app.route("/message/<int:message_id>")
def message_detail(message_id):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    message = con.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
    related_item = None
    if message and message["related_code"]:
        related_item = con.execute("SELECT * FROM items WHERE code=?", (message["related_code"],)).fetchone()
    related_files = []
    if message:
        related_files = con.execute("""SELECT * FROM files
                                       WHERE item_code=? OR client=?
                                       ORDER BY id DESC""",
                                    (message["related_code"], message["client"])).fetchall()
    con.close()
    return render_template("message_detail.html", message=message, related_item=related_item, related_files=related_files)

@app.route("/edit_message/<int:message_id>", methods=["GET","POST"])
def edit_message(message_id):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    if request.method == "POST":
        con.execute("""UPDATE messages SET date=?, client=?, kind=?, subject=?, person=?, body=?, attachment_name=?, related_code=?
                       WHERE id=?""",
                    (request.form.get("date"), request.form.get("client"), request.form.get("kind"),
                     request.form.get("subject"), request.form.get("person"), request.form.get("body"),
                     request.form.get("attachment_name"), request.form.get("related_code"), message_id))
        con.commit(); con.close()
        return redirect(url_for("message_detail", message_id=message_id))
    message = con.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
    con.close()
    return render_template("edit_message.html", message=message)

@app.route("/delete_message/<int:message_id>")
def delete_message(message_id):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    con.execute("DELETE FROM messages WHERE id=?", (message_id,))
    con.commit(); con.close()
    return redirect(url_for("dashboard"))


@app.route("/reset_demo")
def reset_demo():
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    con.execute("DELETE FROM items")
    con.execute("DELETE FROM clients")
    con.execute("DELETE FROM messages")
    con.execute("DELETE FROM files")
    con.execute("DELETE FROM mail_messages")
    con.execute("DELETE FROM mail_threads")
    con.commit()
    con.close()
    init_db()
    return redirect(url_for("dashboard"))



@app.route("/mail")
@app.route("/inbox")
def mail_inbox():
    if not logged_in(): return redirect(url_for("login"))
    box = request.args.get("box", "inbox")
    page = request.args.get("page", 1, type=int)
    per_page = 10
    if page < 1:
        page = 1
    offset = (page - 1) * per_page

    con = db()
    where_sql = ""
    title = "すべてのメール"
    if box == "inbox":
        where_sql = """WHERE EXISTS (SELECT 1 FROM mail_messages m WHERE m.thread_id=t.id AND m.direction='received')"""
        title = "受信箱"
    elif box == "sent":
        where_sql = """WHERE EXISTS (SELECT 1 FROM mail_messages m WHERE m.thread_id=t.id AND m.direction='sent')"""
        title = "送信済み"
    elif box == "open":
        where_sql = """WHERE t.status IS NULL OR t.status='' OR t.status IN ('未対応','確認中')"""
        title = "未対応"
    elif box == "replied":
        where_sql = """WHERE t.status IN ('返信済','返信済み','送信済')"""
        title = "返信済み"
    elif box == "all":
        title = "すべてのメール"
    else:
        box = "all"
        title = "すべてのメール"

    count_sql = "SELECT COUNT(*) AS cnt FROM mail_threads t " + where_sql
    total = con.execute(count_sql).fetchone()["cnt"]
    total_pages = max(1, (total + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages
        offset = (page - 1) * per_page

    rows = con.execute("""
        SELECT t.*,
          lm.body AS last_body,
          lm.direction AS latest_direction,
          lm.sent_at AS last_at,
          lm.sender_name AS latest_sender_name
        FROM mail_threads t
        LEFT JOIN mail_messages lm ON lm.id = (
          SELECT m2.id FROM mail_messages m2
          WHERE m2.thread_id=t.id
          ORDER BY m2.id DESC LIMIT 1
        )
    """ + where_sql + """
        ORDER BY t.updated_at DESC, t.id DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset)).fetchall()
    con.close()
    return render_template("mailbox.html", threads=rows, box=box, title=title, page=page, total_pages=total_pages, total=total)


@app.route("/mail/thread/<int:thread_id>/status", methods=["POST"])
def update_mail_thread_status(thread_id):
    if not logged_in(): return redirect(url_for("login"))
    status = request.form.get("status", "未対応")
    if status not in ["未対応", "確認中", "返信済み"]:
        status = "未対応"
    con = db()
    con.execute("UPDATE mail_threads SET status=?, updated_at=? WHERE id=?", (status, datetime.now().strftime("%Y/%m/%d %H:%M"), thread_id))
    con.commit(); con.close()
    return redirect(url_for("mail_thread", thread_id=thread_id))


@app.route("/mail/message/<int:message_id>/delete", methods=["POST"])
def delete_mail_message(message_id):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    row = con.execute("SELECT thread_id FROM mail_messages WHERE id=?", (message_id,)).fetchone()
    if row:
        tid = row["thread_id"]
        con.execute("DELETE FROM mail_messages WHERE id=?", (message_id,))
        con.execute("UPDATE mail_threads SET updated_at=? WHERE id=?", (datetime.now().strftime("%Y/%m/%d %H:%M"), tid))
        con.commit(); con.close()
        return redirect(url_for("mail_thread", thread_id=tid))
    con.close()
    return redirect(url_for("mail_inbox"))


@app.route("/mail/thread/<int:thread_id>", methods=["GET","POST"])
def mail_thread(thread_id):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        attachment_name = request.form.get("attachment_name", "").strip()
        saved = save_mail_attachment(request.files.get("attachment_file"))
        if saved:
            attachment_name = saved
        if body or attachment_name:
            thread = con.execute("SELECT * FROM mail_threads WHERE id=?", (thread_id,)).fetchone()
            now = datetime.now().strftime("%Y/%m/%d %H:%M")
            con.execute("""INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (thread_id,"sent",now,"野口","volca7000@gmail.com",thread["contact_name"],thread["contact_email"],body,attachment_name))
            con.execute("UPDATE mail_threads SET status=?, updated_at=? WHERE id=?", ("返信済み", now, thread_id))
            con.commit()
        con.close()
        return redirect(url_for("mail_thread", thread_id=thread_id))
    thread = con.execute("SELECT * FROM mail_threads WHERE id=?", (thread_id,)).fetchone()
    mail_messages = con.execute("SELECT * FROM mail_messages WHERE thread_id=? ORDER BY id ASC", (thread_id,)).fetchall()
    con.close()
    if not thread:
        return redirect(url_for("mail_inbox"))
    return render_template("mail_thread.html", thread=thread, mail_messages=mail_messages)


@app.route("/mail/compose", methods=["GET","POST"])
def mail_compose():
    if not logged_in(): return redirect(url_for("login"))
    if request.method == "POST":
        attachment_name = request.form.get("attachment_name", "").strip()
        saved = save_mail_attachment(request.files.get("attachment_file"))
        if saved:
            attachment_name = saved
        con = db()
        now = datetime.now().strftime("%Y/%m/%d %H:%M")
        con.execute("""INSERT INTO mail_threads(client,contact_name,contact_email,subject,related_code,status,updated_at)
                       VALUES (?,?,?,?,?,?,?)""",
                    (request.form.get("client"), request.form.get("contact_name"), request.form.get("contact_email"),
                     request.form.get("subject"), request.form.get("related_code"), "送信済", now))
        thread_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        con.execute("""INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (thread_id,"sent",now,"野口","volca7000@gmail.com",request.form.get("contact_name"),
                     request.form.get("contact_email"),request.form.get("body"),attachment_name))
        con.commit(); con.close()
        return redirect(url_for("mail_thread", thread_id=thread_id))
    return render_template("mail_compose.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8300)), debug=os.environ.get("FLASK_DEBUG") == "1")
