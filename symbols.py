# =============================================================
# DANH SACH MA GIAO DICH
# Moi ma can:
#   "yf"  : ticker Yahoo Finance (de lay du lieu)
#   "tv"  : ticker TradingView  (de mo chart)
#   "cat" : nhom
# =============================================================

SYMBOLS = {

    # FOREX
    "EURUSD": {"name":"EURUSD",  "cat":"forex",      "yf":"EURUSD=X",  "tv":"EURUSD"},
    "GBPUSD": {"name":"GBPUSD",  "cat":"forex",      "yf":"GBPUSD=X",  "tv":"GBPUSD"},
    "USDJPY": {"name":"USDJPY",  "cat":"forex",      "yf":"USDJPY=X",  "tv":"USDJPY"},
    "GBPJPY": {"name":"GBPJPY",  "cat":"forex",      "yf":"GBPJPY=X",  "tv":"GBPJPY"},
    "AUDUSD": {"name":"AUDUSD",  "cat":"forex",      "yf":"AUDUSD=X",  "tv":"AUDUSD"},
    "USDCAD": {"name":"USDCAD",  "cat":"forex",      "yf":"USDCAD=X",  "tv":"USDCAD"},
    "GBPCAD": {"name":"GBPCAD",  "cat":"forex",      "yf":"GBPCAD=X",  "tv":"GBPCAD"},
    "NZDUSD": {"name":"NZDUSD",  "cat":"forex",      "yf":"NZDUSD=X",  "tv":"NZDUSD"},
    "USDCHF": {"name":"USDCHF",  "cat":"forex",      "yf":"USDCHF=X",  "tv":"USDCHF"},
    "GBPCHF": {"name":"GBPCHF",  "cat":"forex",      "yf":"GBPCHF=X",  "tv":"GBPCHF"},
    "GBPAUD": {"name":"GBPAUD",  "cat":"forex",      "yf":"GBPAUD=X",  "tv":"GBPAUD"},
    "EURAUD": {"name":"EURAUD",  "cat":"forex",      "yf":"EURAUD=X",  "tv":"EURAUD"},
    "GBPNZD": {"name":"GBPNZD",  "cat":"forex",      "yf":"GBPNZD=X",  "tv":"GBPNZD"},

    # KIM LOAI
    "XAUUSD": {"name":"XAUUSD",  "cat":"kim loai",   "yf":"GC=F",      "tv":"XAUUSD"},
    "XAGUSD": {"name":"XAGUSD",  "cat":"kim loai",   "yf":"SI=F",      "tv":"XAGUSD"},

    # NANG LUONG
    "USOIL":  {"name":"USOIL",   "cat":"nang luong", "yf":"CL=F",      "tv":"USOIL"},
    "UKOIL":  {"name":"UKOIL",   "cat":"nang luong", "yf":"BZ=F",      "tv":"UKOIL"},

    # CHI SO
    "US500":  {"name":"US500",   "cat":"chi so",     "yf":"^GSPC",     "tv":"SP500"},
    "EU50":   {"name":"EU50",    "cat":"chi so",     "yf":"^STOXX50E", "tv":"STOXX50"},
    "JP225":  {"name":"JP225",   "cat":"chi so",     "yf":"^N225",     "tv":"NI225"},
    "US30":   {"name":"US30",    "cat":"chi so",     "yf":"^DJI",      "tv":"DJI"},
    "NAS100": {"name":"NAS100",  "cat":"chi so",     "yf":"^NDX",      "tv":"NDX"},

    # NONG SAN
    "WHEAT":  {"name":"WHEAT",   "cat":"nong san",   "yf":"ZW=F",      "tv":"WHEAT"},
    "CORN":   {"name":"CORN",    "cat":"nong san",   "yf":"ZC=F",      "tv":"CORN"},
    "SOYBEAN":{"name":"SOYBEAN", "cat":"nong san",   "yf":"ZS=F",      "tv":"SOYBN1!"},
    "COFFEE": {"name":"COFFEE",  "cat":"nong san",   "yf":"KC=F",      "tv":"KC1!"},

    # CRYPTO
    "BTCUSD": {"name":"BTCUSD",  "cat":"crypto",     "yf":"BTC-USD",   "tv":"BTCUSD"},
    "ETHUSD": {"name":"ETHUSD",  "cat":"crypto",     "yf":"ETH-USD",   "tv":"ETHUSD"},

    # THEM MA MOI O DAY:
    # "TEN": {"name":"TEN","cat":"nhom","yf":"TICKER=X","tv":"TICKER"},
}
