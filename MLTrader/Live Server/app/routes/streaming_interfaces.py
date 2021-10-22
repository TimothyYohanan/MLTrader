from flask import render_template, request, url_for, Blueprint, jsonify
from app.structures.TDAmeritrade import TDAmeritradeAPI
from app.structures.Query import Query
from app.general_purpose.datetime_utils import DATETIMEfromUNIXTIMESTAMP, displayTIMEDELTA
from app.general_purpose.utils import load_object
from datetime import timedelta
import asyncio
import nest_asyncio
from app import tdaAPI_filepath, quotesHandler
from tzlocal import get_localzone_name
import pytz
from dateutil import parser

local_tz = pytz.timezone(get_localzone_name())

nest_asyncio.apply()
datastream = Blueprint('datastream', __name__)
main = Blueprint('main', __name__)
loop = asyncio.get_event_loop()

@datastream.route("/hmi/<string:action>", methods=["POST", "GET"])
def hmi(action):
    tdaAPI = load_object(tdaAPI_filepath)
    if action == "view":
        return render_template("streamingdatahmi.html", title="TDAmeritrade Streaming Data", url_for=url_for, main=main)
    elif action == "ajax_req":
        request_message = request.get_json()
        if request_message["action"] == "TDAmeritradeClient_new":
            message = request_message["message"]
            consumerkey = message["consumerkey"]
            redirecturi = message["redirecturi"] 
            qoslevel = message["qoslevel"]
            quotesHandler.clear()
            tdaAPI = TDAmeritradeAPI(consumerkey, redirecturi, QOSLevel=qoslevel)
            return jsonify(status=200, response=None)
        elif request_message["action"] == "TDAmeritradeClient_delete":
            try:
                tdaAPI_filepath.unlink()
            except:
                pass   # could set this up to flash an error message
            return jsonify(status=200, response=None)
        elif request_message["action"] == "TDAmeritradeClient_startStreaming":
            loop.create_task(tdaAPI.stream_quotes())
            loop.run_forever()
            return jsonify(status=200, response=None)
        elif request_message["action"] == "TDAmeritradeClient_stopStreaming":
            loop.stop()
            return jsonify(status=200, response=None)
        elif request_message["action"] == "info_refresh":
            general_info = {}
            ticker_info = {}
            api_info = {'apiExists': False, 'loopRunning': False}
            if tdaAPI_filepath.is_file():
                quotes = quotesHandler.quotes
                tickers = quotes['tickers']
                ticker_hasData = [ticker for ticker in tickers if tickers[ticker]['row count'] > 0]
                api_info = {'apiExists': True, 'loopRunning': loop.is_running()}
                if len(ticker_hasData) > 0:
                    stream_id = quotes['current stream'] - 1
                    lenEntries = [tickers[ticker]['row count'] for ticker in tickers]
                    general_info = {
                        'oldestItem': DATETIMEfromUNIXTIMESTAMP(quotes['oldest data'], tz=local_tz, milliseconds=True, display=True), 
                        'currStreamStart': DATETIMEfromUNIXTIMESTAMP(quotes['current stream start'], tz=local_tz, milliseconds=True, display=True),
                        'daysStreaming': None,
                        'lastUpdate': DATETIMEfromUNIXTIMESTAMP(quotes['latest data'], tz=local_tz, milliseconds=True, display=True),
                        'updateFreq': None,
                        'nTickers': len(ticker_hasData),
                        'nRowsAvg': round(sum(lenEntries) / len(lenEntries)),
                        'nRowsMin': min(lenEntries),
                        'nRowsMax': max(lenEntries)
                        }
                    for ticker in ticker_hasData:
                        ticker_info[ticker] = {
                            'lastUpdate' : DATETIMEfromUNIXTIMESTAMP(tickers[ticker]['latest data'], tz=local_tz, milliseconds=True, display=True), 
                            'oldestItem' : DATETIMEfromUNIXTIMESTAMP(tickers[ticker]['oldest data'], tz=local_tz, milliseconds=True, display=True), 
                            'nRows' : tickers[ticker]['row count']
                            }
            return jsonify(status=200, response={'api_info': api_info, 'l1quotes_info': general_info, 'ticker_info': ticker_info})
        elif request_message["action"] == "tickerDetails":
            ticker = request_message["message"]["ticker"]
            ticker_data = quotesHandler.quotes['tickers'][ticker]
            response = {
                'streams': {}
            }
            for stream_id in ticker_data['streams']:
                start_ut_ms = ticker_data['streams'][stream_id]['start']
                end_ut_ms = ticker_data['streams'][stream_id]['end']
                latest_ut_ms = ticker_data['latest data']
                streamLength = timedelta(milliseconds=(end_ut_ms - start_ut_ms)) if end_ut_ms else timedelta(milliseconds=(latest_ut_ms - start_ut_ms))
                response['streams'][stream_id] = {
                    'start': DATETIMEfromUNIXTIMESTAMP(start_ut_ms, tz=local_tz, milliseconds=True, display=True),
                    'end': DATETIMEfromUNIXTIMESTAMP(end_ut_ms, tz=local_tz, milliseconds=True, display=True) if end_ut_ms else None,
                    'validation': ticker_data['streams'][stream_id]['validation'],
                    'row count': ticker_data['streams'][stream_id]['data'].shape[0],
                    'time streaming': displayTIMEDELTA(streamLength)
                }
            
            return jsonify(status=200, response=response)

@datastream.route("/mmi", methods=["POST", "GET"])
def mmi():
    request_message = request.get_json()
    if request_message["action"] == "fetch_tickerData":
        ticker = request_message["message"]["ticker"]
        startDateTime_str = request_message["message"]["startDateTime"]
        endDateTime_str = request_message["message"]["endDateTime"]
        startDateTime = pytz.utc.localize(parser.parse(startDateTime_str))
        endDateTime = pytz.utc.localize(parser.parse(endDateTime_str))
        q = Query(startDateTime, endDateTime, [ticker])
        arr_dfs = q.run()
        print(arr_dfs)
        return jsonify(status=200, response=None)
    
