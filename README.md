# 股票資料抓取分析工具

支援台股與美股，資料來源是 yfinance（不需要申請任何 API Key）。

## 安裝

```
pip install -r requirements.txt
```

## 使用方式

### 分析單一股票（K線圖 + 均線 + RSI + MACD + 基本面）

```
python main.py analyze 2330 --period 1y
python main.py analyze AAPL --period 6mo
```

執行後會先在終端機印出基本面摘要（本益比、殖利率、營收成長率等）與近幾季營收，
接著跳出圖表視窗，包含：K 線、成交量、SMA5/20/60 均線、RSI(14)、MACD。

- `--period`：資料期間，可用 `1mo` `3mo` `6mo` `1y` `2y` `5y` `max`
- `--interval`：資料頻率，可用 `1d`（日線，預設）`1wk`（週線）

### 多檔股票報酬率比較

```
python main.py compare 2330 0050 AAPL --period 1y
```

會把多檔股票的收盤價換算成「以起點為 100」的相對報酬率，畫在同一張圖上比較走勢。

## 股票代號輸入規則

- 台股上市：直接輸入純數字即可，程式會自動補上 `.TW`，例如 `2330` → `2330.TW`
- 台股上櫃：輸入完整代號 `.TWO` 後綴，例如 `6488.TWO`
- 美股：直接輸入代號，例如 `AAPL` `TSLA`

## 檔案說明

- `data_fetcher.py` — 抓取歷史股價與基本面資料
- `indicators.py` — 計算 SMA、RSI、MACD
- `plotting.py` — 畫 K 線圖與比較圖
- `main.py` — CLI 進入點
