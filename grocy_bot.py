import sqlite3, os, re, requests
from datetime import date, datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

def load_env():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

load_env()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROUP_ID = os.environ.get("GROUP_ID", "")
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8080/api")
API_KEY = os.environ.get("API_KEY", "")
DB = os.path.expanduser(os.environ.get("DB_PATH", "~/grocy-data/data/grocy.db"))
HEADERS = {"GROCY-API-KEY": API_KEY, "Content-Type": "application/json"}

HELP = """📋 *Grocy 命令列表*

/help       帮助
/check      未来3天到期食品
/stock      当前全部库存
/search     搜索食品（/search 牛奶）
/expired    已过期食品
/soon       未来N天到期（/soon 7）
/stats      库存统计
/add        添加物品（/add 生抽,2026-08-10,2）
           到期日可省略，/add 盐, 1 为永不过期"""

def q(sql):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(sql)
    r = c.fetchall()
    conn.close()
    return r

async def help(u, c):
    await u.message.reply_text(HELP, parse_mode="Markdown")

async def check(u, c):
    rows = q("SELECT p.name,s.best_before_date,s.amount FROM stock s JOIN products p ON p.id=s.product_id WHERE s.best_before_date BETWEEN date('now') AND date('now','+3 days') AND s.open=0 ORDER BY s.best_before_date")
    expired = q("SELECT COUNT(*) FROM stock WHERE best_before_date<date('now') AND open=0 AND amount>0")[0][0]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"📋 Grocy 食品状态 · {now}\n\n"
    if expired: msg += f"🔴 已过期: {expired} 件\n"
    if not rows: msg += "✅ 最近3天没有食品到期"
    else:
        msg += "⚠️ 未来3天到期：\n"
        for n,b,a in rows:
            d = (date.fromisoformat(b)-date.today()).days
            msg += f"{'🔴' if d<=1 else '🟡'} {n} — {b}（剩{d}天）\n"
    await u.message.reply_text(msg)

async def stock(u, c):
    rows = q("SELECT p.name,s.amount,s.open FROM stock s JOIN products p ON p.id=s.product_id WHERE s.open=0 AND s.amount>0 ORDER BY p.name")
    if not rows: await u.message.reply_text("📦 库存为空"); return
    msg = "📦 当前库存：\n\n"
    for n,a,o in rows: msg += f"• {n} × {a}{' (已开封)' if o else ''}\n"
    await u.message.reply_text(msg)

async def search(u, c):
    kw = " ".join(c.args)
    if not kw: await u.message.reply_text("🔍 用法：/search <关键词>"); return
    rows = q(f"SELECT p.name,s.amount,s.best_before_date,s.open FROM stock s JOIN products p ON p.id=s.product_id WHERE p.name LIKE '%{kw}%' AND s.open=0 ORDER BY s.best_before_date")
    if not rows:
        ps = q(f"SELECT name FROM products WHERE name LIKE '%{kw}%'")
        if ps: await u.message.reply_text("🔍 找到（无库存）：\n"+"\n".join([f"• {r[0]}" for r in ps]))
        else: await u.message.reply_text(f"❌ 没找到 \"{kw}\""); return
    msg = f"🔍 搜索 \"{kw}\" 结果：\n\n"
    for n,a,b,o in rows:
        ds = "永不过期" if (not b or b=="2999-12-31") else b
        if b and b!="2999-12-31":
            d = (date.fromisoformat(b)-date.today()).days
            ds = f"{b}{' ⚠️已过期{-d}天' if d<0 else ' ⏰剩{d}天' if d<=3 else ''}"
        msg += f"• {n} × {a}{' (已开封)' if o else ''} — 到期 {ds}\n"
    await u.message.reply_text(msg)

async def expired(u, c):
    rows = q("SELECT p.name,s.best_before_date,s.amount FROM stock s JOIN products p ON p.id=s.product_id WHERE s.best_before_date<date('now') AND s.open=0 AND s.amount>0 ORDER BY s.best_before_date")
    if not rows: await u.message.reply_text("✅ 没有过期食品"); return
    msg = f"🔴 已过期（{len(rows)} 件）：\n\n"
    for n,b,a in rows: msg += f"• {n} × {a} — 过期 {(date.today()-date.fromisoformat(b)).days}天\n"
    await u.message.reply_text(msg)

async def soon(u, c):
    try:
        d = int(c.args[0]) if c.args else 7
        if d<1 or d>365: await u.message.reply_text("天数范围 1-365"); return
    except: await u.message.reply_text("🔍 用法：/soon <天数>"); return
    rows = q(f"SELECT p.name,s.best_before_date,s.amount FROM stock s JOIN products p ON p.id=s.product_id WHERE s.best_before_date BETWEEN date('now') AND date('now','+{d} days') AND s.open=0 ORDER BY s.best_before_date")
    if not rows: await u.message.reply_text(f"✅ 未来 {d} 天没有食品到期"); return
    msg = f"⏰ 未来 {d} 天到期（{len(rows)} 件）：\n\n"
    for n,b,a in rows:
        dd = (date.fromisoformat(b)-date.today()).days
        msg += f"{'🔴' if dd<=1 else '🟡' if dd<=3 else '🟢'} {n} × {a} — {b}（剩{dd}天）\n"
    await u.message.reply_text(msg)

async def stats(u, c):
    t = q("SELECT COUNT(*) FROM stock WHERE open=0 AND amount>0")[0][0]
    e = q("SELECT COUNT(*) FROM stock WHERE best_before_date<date('now') AND open=0 AND amount>0")[0][0]
    s = q("SELECT COUNT(*) FROM stock WHERE best_before_date BETWEEN date('now') AND date('now','+3 days') AND open=0")[0][0]
    v = q("SELECT COALESCE(SUM(price*amount),0) FROM stock WHERE open=0")[0][0]
    p = q("SELECT COUNT(*) FROM products")[0][0]
    await u.message.reply_text(f"📊 Grocy 统计\n\n📦 库存: {t} 件\n🏷️ 种类: {p}\n🔴 过期: {e}\n🟡 近期待过期: {s}\n💰 总值: €{v:.2f}")

async def add(u, c):
    text = " ".join(c.args)
    if not text:
        await u.message.reply_text("📝 用法：/add <名称>,<到期日>,<数量>\n到期日可省略 /add 盐, 1\n完整：/add 牛奶,2026-08-10,2")
        return
    parts = [p.strip() for p in text.split(",")]
    name = parts[0]
    has_date = len(parts)>=2 and re.match(r"^\d{4}-\d{2}-\d{2}$", parts[1])
    due = parts[1] if has_date else None
    amt = float(parts[2]) if has_date and len(parts)>=3 else (float(parts[1]) if not has_date and len(parts)>=2 else 1.0)
    bbd = due if due else "2999-12-31"

    try:
        # 查产品是否存在
        r = requests.get(f"{API_URL}/objects/products", headers=HEADERS, timeout=10)
        r.raise_for_status()
        products = r.json()
        pid = None
        for p in products:
            if p["name"] == name:
                pid = p["id"]
                break
        newp = False
        if pid is None:
            r2 = requests.post(f"{API_URL}/objects/products", json={"name": name}, headers=HEADERS, timeout=10)
            r2.raise_for_status()
            pid = r2.json()["created_object_id"]
            newp = True

        # API 添加库存
        body = {"amount": amt, "best_before_date": bbd}
        r3 = requests.post(f"{API_URL}/stock/products/{pid}/add", json=body, headers=HEADERS, timeout=10)
        r3.raise_for_status()

        due_str = f"（到期 {due}）" if due else "（永不过期）"
        msg = f"✅ 已添加: {name} × {amt} {due_str}"
        if newp: msg = msg.replace("已添加","🆕 已添加（新建产品）")
        await u.message.reply_text(msg)
    except Exception as e:
        await u.message.reply_text(f"❌ 添加失败: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    for cmd,fn in [("help",help),("check",check),("stock",stock),("search",search),("expired",expired),("soon",soon),("stats",stats),("add",add)]:
        app.add_handler(CommandHandler(cmd, fn))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
