# price_fetcher.py
import requests
import datetime
import logging
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, List, Tuple, Optional


class PriceFetcherThread(QThread):
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, symbols):
        super().__init__()
        self.symbols = symbols

    def run(self):
        try:
            results = self.fetch()
            self.result_ready.emit(results)
        except Exception as e:
            logging.error(f"가격 가져오기 실패: {str(e)}")
            self.error_occurred.emit(f"가격 업데이트에 실패했습니다: {str(e)}")

    def fetch(self):
        results = {}
        usd_to_krw = self.fetch_usd_krw_rate()
        with requests.Session() as sess:
            binance_map = {}
            upbit_map = {}
            upbit_symbols = {}
            morning_map = {}

            for symbol in self.symbols:
                binance_price = self.fetch_binance_price(sess, symbol)
                morning_price = self.fetch_morning_price(sess, symbol)
                up_sym = self.to_upbit_symbol(symbol)
                binance_map[symbol] = binance_price
                morning_map[symbol] = morning_price
                if up_sym:
                    upbit_symbols[symbol] = up_sym

            upbit_markets = list(upbit_symbols.values())
            upbit_price_map = {}
            if upbit_markets:
                try:
                    url = "https://api.upbit.com/v1/ticker"
                    r = sess.get(url, params={"markets": ",".join(upbit_markets)})
                    for item in r.json():
                        upbit_price_map[item["market"]] = float(item["trade_price"])
                except Exception as e:
                    logging.error(f"Upbit 조회 실패: {e}")

        for symbol in self.symbols:
            binance_price = binance_map.get(symbol)
            morning_price = morning_map.get(symbol)
            kimchi_premium = None
            morning_diff = None

            if binance_price is not None and morning_price and morning_price > 0:
                diff = binance_price - morning_price
                morning_diff = (diff / morning_price) * 100

            if binance_price is not None and usd_to_krw > 0:
                up_sym = upbit_symbols.get(symbol)
                if up_sym and up_sym in upbit_price_map:
                    up_price = upbit_price_map[up_sym]
                    kimchi_premium = ((up_price - (binance_price * usd_to_krw))
                                      / (binance_price * usd_to_krw)) * 100

            results[symbol] = (binance_price, morning_diff, kimchi_premium)

        return results

    def fetch_usd_krw_rate(self):
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
            return float(r.json()["rates"]["KRW"])
        except Exception as e:
            logging.error(f"환율 정보 가져오기 실패: {e}")
            return 0.0

    def fetch_binance_price(self, sess, symbol):
        try:
            r = sess.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": symbol})
            return float(r.json()["price"])
        except Exception as e:
            logging.error(f"{symbol} 바이낸스 가격 조회 실패: {e}")
            return None

    def fetch_morning_price(self, sess, symbol):
        try:
            today = datetime.date.today()
            now = datetime.datetime.now()
            morning_time = datetime.time(9, 0)  # 오전 9시

            # 현재 시간이 자정과 오전 9시 사이인지 확인
            if now.time() < morning_time:
                # 자정과 오전 9시 사이라면 전날 데이터 사용
                target_date = today - datetime.timedelta(days=1)
            else:
                # 그 외의 경우 당일 데이터 사용
                target_date = today

            # 타겟 날짜의 오전 9시 시간 생성
            nine_am = datetime.datetime.combine(target_date, morning_time)

            ts = int(nine_am.timestamp() * 1000)
            url = "https://api.binance.com/api/v3/klines"
            r = sess.get(url, params={
                "symbol": symbol, "interval": "1h",
                "startTime": ts, "endTime": ts + 3600000, "limit": 1
            })

            data = r.json()
            if data and len(data) > 0:
                price = float(data[0][1])
                logging.info(f"{symbol} {target_date} 오전 9시 가격: {price}")
                return price
        except Exception as e:
            logging.error(f"{symbol} 아침 가격 조회 실패: {e}")

        return None

    def to_upbit_symbol(self, binance_symbol):
        if binance_symbol.endswith("USDT"):
            return "KRW-" + binance_symbol.replace("USDT", "")
        return None