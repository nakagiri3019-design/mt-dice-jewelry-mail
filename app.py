from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, Response
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3, os, csv, io

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")
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


@app.route("/")
def index():
    return redirect(url_for("dashboard"))

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




def attachment_display_name(filename):
    if not filename:
        return ""

    name = str(filename)

    # 保存用に付けた日時プレフィックスを画面表示では消す
    # 例：20260605_021230_MTDICE_20260515.pdf → MTDICE_20260515.pdf
    parts = name.split("_", 2)
    if len(parts) == 3 and len(parts[0]) == 8 and len(parts[1]) == 6 and parts[0].isdigit() and parts[1].isdigit():
        name = parts[2]

    return name


def save_mail_attachment(file):
    if not file or not file.filename:
        return ""

    upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "mail")
    os.makedirs(upload_dir, exist_ok=True)

    original = secure_filename(file.filename)
    if not original:
        return ""

    name = datetime.now().strftime("%Y%m%d_%H%M%S_") + original
    path = os.path.join(upload_dir, name)
    file.save(path)
    return name



@app.context_processor
def inject_attachment_helpers():
    return dict(attachment_display_name=attachment_display_name)


@app.route("/mail/attachment/<path:filename>")
def mail_attachment(filename):
    if not logged_in():
        return redirect(url_for("login"))

    upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "mail")
    return send_from_directory(upload_dir, filename, as_attachment=False)


@app.route("/mail")
def mail_list():
    if not logged_in(): return redirect(url_for("login"))

    box = request.args.get("box", "all")
    page = request.args.get("page", 1, type=int)
    per_page = 10
    if page < 1:
        page = 1
    offset = (page - 1) * per_page

    con = db()

    base_select = """
        SELECT
            t.*,
            lm.body AS latest_body,
            lm.direction AS latest_direction,
            lm.sent_at AS latest_sent_at,
            lm.sender_name AS latest_sender_name
        FROM mail_threads t
        LEFT JOIN mail_messages lm
          ON lm.id = (
              SELECT m2.id
              FROM mail_messages m2
              WHERE m2.thread_id = t.id
              ORDER BY m2.id DESC
              LIMIT 1
          )
    """

    where_sql = ""
    title = "すべてのメール"

    if box == "inbox":
        where_sql = """
            WHERE EXISTS (
                SELECT 1 FROM mail_messages m
                WHERE m.thread_id = t.id AND m.direction = 'received'
            )
        """
        title = "受信箱"

    elif box == "sent":
        where_sql = """
            WHERE EXISTS (
                SELECT 1 FROM mail_messages m
                WHERE m.thread_id = t.id AND m.direction = 'sent'
            )
        """
        title = "送信済み"

    elif box == "open":
        where_sql = """
            WHERE t.status IS NULL
               OR t.status = ''
               OR t.status = '未対応'
               OR t.status = '確認中'
        """
        title = "未対応"

    elif box == "replied":
        where_sql = """
            WHERE t.status = '返信済み'
        """
        title = "返信済み"

    count_sql = "SELECT COUNT(*) AS cnt FROM mail_threads t " + where_sql
    total = con.execute(count_sql).fetchone()["cnt"]
    total_pages = max(1, (total + per_page - 1) // per_page)

    if page > total_pages:
        page = total_pages
        offset = (page - 1) * per_page

    rows = con.execute(
        base_select + where_sql + """
        ORDER BY t.updated_at DESC
        LIMIT ? OFFSET ?
        """,
        (per_page, offset)
    ).fetchall()

    con.close()

    return render_template(
        "mail_list.html",
        rows=rows,
        box=box,
        title=title,
        page=page,
        total_pages=total_pages,
        total=total
    )


@app.route("/mail/thread/<int:thread_id>", methods=["GET","POST"])
def mail_thread(thread_id):
    if not logged_in(): return redirect(url_for("login"))
    con = db()
    if request.method == "POST":
        body = request.form.get("body","").strip()
        attachment_name = request.form.get("attachment_name","").strip()
        attachment_file = request.files.get("attachment_file")
        saved_attachment = save_mail_attachment(attachment_file)
        if saved_attachment:
            attachment_name = saved_attachment
        if body:
            thread = con.execute("SELECT * FROM mail_threads WHERE id=?", (thread_id,)).fetchone()
            now = datetime.now().strftime("%Y/%m/%d %H:%M")
            con.execute("""INSERT INTO mail_messages(thread_id,direction,sent_at,sender_name,sender_email,recipient_name,recipient_email,body,attachment_name)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (thread_id,"sent",now,"野口","volca7000@gmail.com","金",thread["contact_email"],body,attachment_name))
            con.execute("UPDATE mail_threads SET status=?, updated_at=? WHERE id=?", ("返信済", now, thread_id))
            con.commit()
        con.close()
        return redirect(url_for("mail_thread", thread_id=thread_id))
    thread = con.execute("SELECT * FROM mail_threads WHERE id=?", (thread_id,)).fetchone()
    mail_messages = con.execute("SELECT * FROM mail_messages WHERE thread_id=? ORDER BY id ASC", (thread_id,)).fetchall()
    con.close()
    return render_template("mail_thread.html", thread=thread, mail_messages=mail_messages)



@app.route("/mail/thread/<int:thread_id>/status", methods=["POST"])
def update_mail_thread_status(thread_id):
    if not logged_in():
        return redirect(url_for("login"))

    status = request.form.get("status", "未対応")
    allowed = ["未対応", "確認中", "返信済み"]
    if status not in allowed:
        status = "未対応"

    con = db()
    con.execute(
        "UPDATE mail_threads SET status=?, updated_at=? WHERE id=?",
        (status, datetime.now().strftime("%Y/%m/%d %H:%M"), thread_id)
    )
    con.commit()
    con.close()

    return redirect(url_for("mail_thread", thread_id=thread_id))


@app.route("/mail/message/<int:message_id>/delete", methods=["POST"])
def delete_mail_message(message_id):
    if not logged_in():
        return redirect(url_for("login"))

    con = db()
    row = con.execute("SELECT thread_id FROM mail_messages WHERE id=?", (message_id,)).fetchone()

    if row:
        thread_id = row["thread_id"]
        con.execute("DELETE FROM mail_messages WHERE id=?", (message_id,))
        con.execute("UPDATE mail_threads SET updated_at=? WHERE id=?", (datetime.now().strftime("%Y/%m/%d %H:%M"), thread_id))
        con.commit()
        con.close()
        return redirect(url_for("mail_thread", thread_id=thread_id))

    con.close()
    return redirect(request.referrer or "/mail")


@app.route("/mail/compose", methods=["GET","POST"])
def mail_compose():
    if not logged_in(): return redirect(url_for("login"))
    if request.method == "POST":
        attachment_name = request.form.get("attachment_name","").strip()
        attachment_file = request.files.get("attachment_file")
        saved_attachment = save_mail_attachment(attachment_file)
        if saved_attachment:
            attachment_name = saved_attachment

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8300)), debug=True)




