#!/usr/bin/env python3
"""
MA50/MA200 + MACD H4 Dashboard Generator
==========================================
Dung yfinance de lay du lieu - don gian, on dinh, mien phi.
D1: MA50, MA200 chinh xac 100%
H4: lay interval 4h truc tiep tu yfinance (khong resample)
MACD H4: tinh tren nen H4 da dong

Cai dat: pip install yfinance pandas
Chay:    python ma_dashboard_fetcher.py
"""

import yfinance as yf
import pandas as pd
import json, os, time
from datetime import datetime, timezone

try:
    from symbols import SYMBOLS
    print(f"  Da tai {len(SYMBOLS)} ma tu symbols.py")
except ImportError:
    print("  [LOI] Khong tim thay file symbols.py!")
    exit(1)

# ============================================================
# HAM LAY DU LIEU
# ============================================================

def get_d1(yf_ticker, n=250):
    """Lay D1: price, MA50, MA200."""
    try:
        df = yf.download(yf_ticker, period=f"{n}d", interval="1d",
                         progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 52:
            return None
        close = df["Close"].squeeze().dropna()
        price = float(close.iloc[-1])
        ma50  = float(close.rolling(50).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        return {
            "price":    round(price, 5),
            "above50":  price > ma50,
            "above200": (price > ma200) if ma200 else None,
        }
    except:
        return None

def get_h4(yf_ticker):
    """
    Lay H4 truc tiep tu yfinance (interval=4h, khong resample).
    Tinh MA50 va MACD(12,26,9) tren cac nen da dong.
    """
    try:
        df = yf.download(yf_ticker, period="60d", interval="1h",
                         progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 60:
            return None, None

        close_h1 = df["Close"].squeeze().dropna()

        # Resample H1->H4 bo nen chua dong
        # yfinance tra index UTC, TV dung UTC+7
        # => offset 7h de nen H4 khop voi TV
        utc7 = pd.Timedelta(hours=7)
        close_h4 = (
            close_h1
            .shift(freq=utc7)
            .resample("4h").last()
            .shift(freq=-utc7)
            .dropna()
        )

        # Bo nen H4 chua dong: nen H4 cuoi phai co it nhat 3h H1 sau no
        last_h1 = close_h1.index[-1]
        last_h4 = close_h4.index[-1]
        if (last_h1 - last_h4).total_seconds() / 3600 < 3:
            close_h4 = close_h4.iloc[:-1]

        if len(close_h4) < 52:
            return None, None

        price = float(close_h4.iloc[-1])

        # MA50 H4
        ma50 = float(close_h4.rolling(50).mean().iloc[-1])
        h4_result = {"above50": price > ma50}

        # MACD(12,26,9)
        ema12 = close_h4.ewm(span=12, adjust=False).mean()
        ema26 = close_h4.ewm(span=26, adjust=False).mean()
        macd  = ema12 - ema26
        sig   = macd.ewm(span=9,  adjust=False).mean()
        hist  = macd - sig

        h  = hist.iloc[-4:].values
        hc, hp, hp2 = float(h[-1]), float(h[-2]), float(h[-3])

        cross_up   = hp < 0 <= hc
        cross_dn   = hp > 0 >= hc
        about_up   = hc < 0 and hp < 0 and hp2 < 0 and abs(hc) < abs(hp) < abs(hp2)
        about_down = hc > 0 and hp > 0 and hp2 > 0 and abs(hc) < abs(hp) < abs(hp2)

        if   cross_up:   status = "crossed_up"
        elif cross_dn:   status = "crossed_down"
        elif about_up:   status = "about_up"
        elif about_down: status = "about_down"
        else:            status = "normal"

        macd_result = {"status": status, "histogram": round(hc, 6)}
        return h4_result, macd_result

    except Exception as e:
        return None, None

# ============================================================
# THU THAP TAT CA
# ============================================================

def fetch_all():
    results = []
    total   = len(SYMBOLS)

    for i, (key, meta) in enumerate(SYMBOLS.items(), 1):
        sym     = meta["name"]
        yf_tick = meta.get("yf", key)   # ticker yfinance

        print(f"[{i:2d}/{total}] {sym:10s} ...", end=" ", flush=True)

        d1          = get_d1(yf_tick)
        h4, macd    = get_h4(yf_tick)

        d1_a50 = d1["above50"]  if d1   else None
        h4_a50 = h4["above50"]  if h4   else None

        if d1_a50 is not None and h4_a50 is not None:
            signal = ("bull" if d1_a50 else "bear") if d1_a50 == h4_a50 else "mixed"
        else:
            signal = "nodata"

        row = {
            "sym":         sym,
            "cat":         meta["cat"],
            "tv":          meta["tv"],
            "d1_above50":  d1_a50,
            "d1_above200": d1["above200"] if d1 else None,
            "d1_price":    d1["price"]    if d1 else None,
            "h4_above50":  h4_a50,
            "signal":      signal,
            "macd_status": macd["status"]    if macd else "nodata",
            "macd_hist":   macd["histogram"] if macd else None,
        }

        ma  = ("D1+" if d1_a50 else "D1-") if d1_a50 is not None else "D1?"
        h   = ("H4+" if h4_a50 else "H4-") if h4_a50 is not None else "H4?"
        mc  = macd["status"] if macd else "?"
        print(f"{ma} {h} | MACD={mc}")
        results.append(row)

    return results

# ============================================================
# HTML
# ============================================================
HTML = """<!DOCTYPE html>
<html lang="vi"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Phan tich Xu Huong & Tin Hieu</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--up:#1D9E75;--dn:#D85A30;--al:#BA7517;--pu:#534AB7;--bg:#f7f6f2;--sf:#fff;--bd:rgba(0,0,0,.1);--tx:#1a1a18;--mu:#888780;--bb:#EAF3DE;--bf:#3B6D11;--rb:#FAECE7;--rf:#993C1D;--mb:#F1EFE8;--mf:#5F5E5A}
@media(prefers-color-scheme:dark){:root{--bg:#1a1a18;--sf:#252522;--bd:rgba(255,255,255,.1);--tx:#e8e6e0;--bb:#27500A;--bf:#C0DD97;--rb:#4A1B0C;--rf:#F0997B;--mb:#2C2C2A;--mf:#B4B2A9}}
body{background:var(--bg);color:var(--tx);font-family:-apple-system,'Segoe UI',sans-serif;font-size:14px}
.wrap{max-width:1300px;margin:0 auto;padding:20px 16px}
header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px}
h1{font-size:17px;font-weight:700}.upd{font-size:11px;color:var(--mu)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:16px}
.card{background:var(--sf);border-radius:8px;border:.5px solid var(--bd);padding:10px 14px}
.card .lbl{font-size:11px;color:var(--mu);margin-bottom:2px}.card .val{font-size:21px;font-weight:700}
.val.up{color:var(--up)}.val.dn{color:var(--dn)}.val.al{color:var(--al)}.val.pu{color:var(--pu)}
.pills{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.pill{font-size:11px;padding:4px 12px;border-radius:20px;border:.5px solid var(--bd);background:var(--sf);color:var(--mu);cursor:pointer;transition:all .15s;user-select:none}
.pill.on{background:var(--tx);color:var(--bg);border-color:transparent}
.tbl-wrap{overflow-x:auto;border-radius:10px;border:.5px solid var(--bd)}
table{width:100%;border-collapse:collapse;background:var(--sf)}
thead th{font-size:11px;font-weight:600;color:var(--mu);text-align:left;padding:10px 11px;border-bottom:.5px solid var(--bd);white-space:nowrap;background:var(--sf);position:sticky;top:0;z-index:2}
tbody tr{border-bottom:.5px solid var(--bd);transition:background .1s}
tbody tr:last-child{border-bottom:none}tbody tr:hover{background:var(--bg)}
tbody tr.hi{background:#FAEEDA44}
tbody tr.sbull{background:#D6F5E8;border-left:4px solid var(--up)}
tbody tr.sbear{background:#FAE0D8;border-left:4px solid var(--dn)}
@media(prefers-color-scheme:dark){tbody tr.sbull{background:#0D3D28}tbody tr.sbear{background:#3D1208}}
td{padding:7px 11px;vertical-align:middle;white-space:nowrap}
.sym{font-weight:700;font-size:13px}
.slbl{font-size:10px;padding:2px 7px;border-radius:4px;font-weight:700;display:inline-block;margin-left:4px}
.slbl.buy{background:var(--up);color:#fff}.slbl.sell{background:var(--dn);color:#fff}
.badge{font-size:10px;padding:2px 6px;border-radius:4px;background:var(--bg);color:var(--mu);border:.5px solid var(--bd)}
.ma{display:flex;align-items:center;gap:4px;font-size:12px}
.chip{font-size:10px;padding:3px 8px;border-radius:4px;font-weight:600;display:inline-block;white-space:nowrap}
.chip.bull{background:var(--bb);color:var(--bf)}.chip.bear{background:var(--rb);color:var(--rf)}
.chip.mix{background:var(--mb);color:var(--mf)}
.chip.crup{background:#E1F5EE;color:#085041}.chip.crdn{background:#FAECE7;color:#712B13}
.chip.abup{background:#EAF3DE;color:#3B6D11;border:1px dashed var(--up)}
.chip.abdn{background:#FAECE7;color:#993C1D;border:1px dashed var(--dn)}
.chip.norm{background:var(--mb);color:var(--mu)}
.m200up{color:var(--up);font-weight:600;font-size:12px}.m200dn{color:var(--dn);font-weight:600;font-size:12px}
.nd{color:var(--mu);font-size:11px}
.tvl{font-size:10px;padding:3px 8px;border-radius:4px;border:.5px solid var(--bd);color:var(--mu);text-decoration:none}
.tvl:hover{background:var(--bg);color:var(--tx)}
.leg{display:flex;gap:14px;flex-wrap:wrap;margin-top:14px;font-size:11px;color:var(--mu)}
.li{display:flex;align-items:center;gap:5px}.ld{width:10px;height:10px;border-radius:2px}
.load-btn{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;border-radius:8px;border:none;background:var(--tx);color:var(--bg);font-size:12px;font-weight:600;cursor:pointer;transition:all .15s}
.load-btn:hover{opacity:.85}.load-btn:disabled{opacity:.5;cursor:not-allowed}
.load-btn .spin{display:none;width:13px;height:13px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.load-btn.loading .spin{display:inline-block}
.load-btn.loading .btn-txt{display:none}
.status-msg{font-size:11px;color:var(--mu);margin-left:8px}
.status-msg.ok{color:var(--up)}.status-msg.err{color:var(--dn)}
</style></head><body>
<div class="wrap">
<header>
  <h1>Phan tich Xu Huong &amp; Tin Hieu</h1>
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
    <button class="load-btn" id="loadBtn" onclick="loadData()">
      <div class="spin"></div>
      <span class="btn-txt">&#8635; Load du lieu moi</span>
    </button>
    <span class="status-msg" id="statusMsg"></span>
    <span class="upd">Cap nhat: __UPDATED__</span>
  </div>
</header>
<div class="cards" id="cards"></div>
<div class="pills" id="pills">
  <span class="pill on" data-f="all">Tat ca</span>
  <span class="pill" data-f="forex">Forex</span>
  <span class="pill" data-f="kim loai">Kim loai</span>
  <span class="pill" data-f="nang luong">Nang luong</span>
  <span class="pill" data-f="chi so">Chi so</span>
  <span class="pill" data-f="nong san">Nong san</span>
  <span class="pill" data-f="crypto">Crypto</span>
  <span class="pill" data-f="align">Dong pha D+H4</span>
  <span class="pill" data-f="macd">MACD tin hieu</span>
  <span class="pill" data-f="strong">&#9889; Tin hieu kep</span>
</div>
<div class="tbl-wrap"><table>
  <thead><tr>
    <th>Ma</th><th>Nhom</th><th>D1/MA50</th><th>H4/MA50</th>
    <th>Tin hieu MA</th><th>D1 vs MA200</th><th>MACD H4</th>
    <th>Histogram</th><th>Gia</th><th>Chart</th>
  </tr></thead>
  <tbody id="tbody"></tbody>
</table></div>
<div class="leg">
  <span class="li"><span class="ld" style="background:var(--up)"></span>Tren MA</span>
  <span class="li"><span class="ld" style="background:var(--dn)"></span>Duoi MA</span>
  <span class="li"><span class="ld" style="background:#FAEEDA;border:1px solid var(--al)"></span>Dong pha</span>
  <span class="li"><span class="ld" style="background:#D6F5E8;border:2px solid var(--up)"></span>Tin hieu kep MUA</span>
  <span class="li"><span class="ld" style="background:#FAE0D8;border:2px solid var(--dn)"></span>Tin hieu kep BAN</span>
</div>
</div>
<script>
const D=__DATA__;
const CATS={forex:'Forex','kim loai':'Kim loai','nang luong':'Nang luong','chi so':'Chi so','nong san':'Nong san',crypto:'Crypto'};
const MSIG=['crossed_up','crossed_down','about_up','about_down'];
const MUP=['crossed_up','about_up'],MDN=['crossed_down','about_down'];
function isSB(r){return r.signal==='bull'&&MUP.includes(r.macd_status)}
function isSBr(r){return r.signal==='bear'&&MDN.includes(r.macd_status)}
function maCell(v){
  if(v===null||v===undefined)return '<span class="nd">No data</span>';
  return '<div class="ma"><span style="color:'+(v?'var(--up)':'var(--dn)')+';">'+(v?'&#9650; Tren':'&#9660; Duoi')+'</span></div>';
}
function macdChip(s,h){
  const tip=h!=null?'Histogram: '+(h>0?'+':'')+h:'';
  const m={crossed_up:['crup','&#10003; Da cat len'],crossed_down:['crdn','&#9660; Da cat xuong'],
    about_up:['abup','Sap cat len'],about_down:['abdn','Sap cat xuong'],
    normal:['norm','Binh thuong'],nodata:['norm','No data']};
  const c=m[s]||m.normal;
  return '<span class="chip '+c[0]+'" title="'+tip+'">'+c[1]+'</span>';
}
function histBar(h){
  if(h===null||h===undefined)return '<span class="nd">No data</span>';
  return '<span style="color:'+(h>0?'var(--up)':'var(--dn)')+';font-size:11px;font-weight:600;">'+(h>0?'+':'')+h+'</span>';
}
function render(f){
  const rows=f==='align'?D.filter(r=>r.signal==='bull'||r.signal==='bear')
    :f==='macd'?D.filter(r=>MSIG.includes(r.macd_status))
    :f==='strong'?D.filter(r=>isSB(r)||isSBr(r))
    :f==='all'?D:D.filter(r=>r.cat===f);
  let u=0,d=0,bull=0,bear=0,ms=0,ss=0;
  D.forEach(r=>{
    if(r.d1_above50===true)u++;else if(r.d1_above50===false)d++;
    if(r.signal==='bull')bull++;if(r.signal==='bear')bear++;
    if(MSIG.includes(r.macd_status))ms++;
    if(isSB(r)||isSBr(r))ss++;
  });
  document.getElementById('cards').innerHTML=
    '<div class="card"><div class="lbl">Tong ma</div><div class="val">'+D.length+'</div></div>'+
    '<div class="card"><div class="lbl">D1 tren MA50</div><div class="val up">'+u+'</div></div>'+
    '<div class="card"><div class="lbl">D1 duoi MA50</div><div class="val dn">'+d+'</div></div>'+
    '<div class="card"><div class="lbl">Dong pha D+H4</div><div class="val al">'+(bull+bear)+'</div></div>'+
    '<div class="card"><div class="lbl">Tang</div><div class="val up">'+bull+'</div></div>'+
    '<div class="card"><div class="lbl">Giam</div><div class="val dn">'+bear+'</div></div>'+
    '<div class="card"><div class="lbl">MACD H4</div><div class="val pu">'+ms+'</div></div>'+
    '<div class="card" style="border:1.5px solid var(--up)"><div class="lbl">&#9889; Tin hieu kep</div><div class="val pu">'+ss+'</div></div>';
  const tbody=document.getElementById('tbody');
  tbody.innerHTML='';
  rows.forEach(r=>{
    const sb=isSB(r),sbr=isSBr(r),al=r.signal==='bull'||r.signal==='bear';
    const tr=document.createElement('tr');
    if(sb)tr.className='sbull';else if(sbr)tr.className='sbear';else if(al)tr.className='hi';
    const tag=sb?'<span class="slbl buy">MUA</span>':sbr?'<span class="slbl sell">BAN</span>':'';
    const sig=r.signal==='bull'?'<span class="chip bull">&#8593; Dong pha &#8593;</span>'
      :r.signal==='bear'?'<span class="chip bear">&#8595; Dong pha &#8595;</span>'
      :r.signal==='mixed'?'<span class="chip mix">Nguoc pha</span>'
      :'<span class="nd">No data</span>';
    const m200=!al?'<span class="nd">-</span>'
      :r.d1_above200===true?'<span class="m200up">&#9650; Tren MA200</span>'
      :r.d1_above200===false?'<span class="m200dn">&#9660; Duoi MA200</span>'
      :'<span class="nd">Not enough</span>';
    const price=r.d1_price?r.d1_price.toLocaleString('en-US',{maximumFractionDigits:5}):'—';
    const url='https://www.tradingview.com/chart/wDuFkCpN/?symbol='+r.tv;
    tr.innerHTML='<td><span class="sym">'+r.sym+'</span>'+tag+'</td>'
      +'<td><span class="badge">'+(CATS[r.cat]||r.cat)+'</span></td>'
      +'<td>'+maCell(r.d1_above50)+'</td>'
      +'<td>'+maCell(r.h4_above50)+'</td>'
      +'<td>'+sig+'</td><td>'+m200+'</td>'
      +'<td>'+macdChip(r.macd_status,r.macd_hist)+'</td>'
      +'<td>'+histBar(r.macd_hist)+'</td>'
      +'<td style="font-size:12px;color:var(--mu);">'+price+'</td>'
      +'<td><a class="tvl" href="'+url+'" target="_blank">TV</a></td>';
    tbody.appendChild(tr);
  });
}
document.getElementById('pills').addEventListener('click',e=>{
  if(!e.target.classList.contains('pill'))return;
  document.querySelectorAll('.pill').forEach(p=>p.classList.remove('on'));
  e.target.classList.add('on');render(e.target.dataset.f);
});
render('all');

async function loadData(){
  const btn = document.getElementById('loadBtn');
  const msg = document.getElementById('statusMsg');
  btn.classList.add('loading');
  btn.disabled = true;
  msg.className = 'status-msg';
  msg.textContent = 'Dang lay du lieu...';
  try {
    const res = await fetch('/api/fetch', {method:'POST'});
    if(!res.ok) throw new Error('Server error ' + res.status);
    const json = await res.json();
    if(json.status === 'ok'){
      msg.className = 'status-msg ok';
      msg.textContent = 'Xong! Dang tai lai...';
      setTimeout(()=>location.reload(), 1500);
    } else {
      throw new Error(json.message || 'Loi khong xac dinh');
    }
  } catch(err){
    if(err.message.includes('fetch') || err.message.includes('Failed')){
      msg.className = 'status-msg err';
      msg.textContent = 'Chua chay server.py! Mo CMD chay: python server.py';
    } else {
      msg.className = 'status-msg err';
      msg.textContent = 'Loi: ' + err.message;
    }
    btn.classList.remove('loading');
    btn.disabled = false;
  }
}
</script></body></html>"""

def build_html(data):
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return HTML.replace("__UPDATED__", updated).replace("__DATA__", json.dumps(data, ensure_ascii=False))

def main(open_browser=False):
    print("="*55)
    print("  Phan tich Xu Huong & Tin Hieu (yfinance)")
    print("="*55)
    print(f"  Bat dau: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n")

    data  = fetch_all()
    bull  = sum(1 for r in data if r["signal"]=="bull")
    bear  = sum(1 for r in data if r["signal"]=="bear")
    ms    = sum(1 for r in data if r["macd_status"] in ["crossed_up","crossed_down","about_up","about_down"])
    strong= sum(1 for r in data if
                (r["signal"]=="bull" and r["macd_status"] in ["crossed_up","about_up"]) or
                (r["signal"]=="bear" and r["macd_status"] in ["crossed_down","about_down"]))

    print(f"\n{'='*55}")
    print(f"  Dong pha tang:{bull} | Giam:{bear} | MACD:{ms} | Kep:{strong}")
    print(f"{'='*55}\n")

    base = os.path.dirname(os.path.abspath(__file__))

    # Luu dashboard.html
    html = build_html(data)
    out  = os.path.join(base, "dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Da luu: {out}")

    # Luu dashboard_data.json (de scheduler doc gui email)
    data_out = os.path.join(base, "dashboard_data.json")
    with open(data_out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main(open_browser=False)

