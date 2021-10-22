import os
import pytz
import numpy as np
import pandas as pd
from datetime import datetime
from multiprocessing import Pool
from app import tickers as available_tickers
from app.general_purpose.datetime_utils import UNIXTIMESTAMP, DATETIMEfromUNIXTIMESTAMP, datetime_errorCheck

# built to query QuotesHandler
# can save query objects and re-run them on a schedual if needed

class Query:
    def __init__(self, startUTC: datetime, endUTC: datetime, tickers: list):
        self.result = {}
        self.start = startUTC
        self.end = endUTC
        self.tickers = tickers

        self.__build()

    def run(self) -> dict:
        from app import quotesHandler as QH
        
        multiprocessing_useCores = os.cpu_count() - 1
        startTimestamp = UNIXTIMESTAMP(self.start, milliseconds=True)
        endTimestamp = UNIXTIMESTAMP(self.end, milliseconds=True)
        quotes_local_copy = [{'ticker': ticker, 'latest data': QH.quotes['tickers'][ticker]['latest data'], 'streams': QH.quotes['tickers'][ticker]['streams']} for ticker in self.tickers if ticker in available_tickers]

        with Pool(processes = multiprocessing_useCores) as pool:
            for each in quotes_local_copy:
                pool.apply_async(self.loop, args=(each, startTimestamp, endTimestamp, QH.level_one_quotes_fields), callback=self.parse_loop_output)
            pool.close()
            pool.join()

        return self.result

    def loop(self, input: dict, startUNIXMS: int, endUNIXMS: int, column_labels: list) -> dict:
            ticker = input['ticker']
            ret = {
                    'ticker': ticker, 
                    'info': None
                } 
            workable_streams = self.__workable_streams(input, startUNIXMS, endUNIXMS)
            if len(workable_streams) > 0:
                workable_data = [stream['data'] for stream in workable_streams]
                np_arr = np.concatenate(workable_data)
                df = pd.DataFrame(np_arr, columns=column_labels)
                timestamp_mask = (df['timestamp'] >= startUNIXMS) & (df['timestamp'] <= endUNIXMS)
                df = df.loc[timestamp_mask]
                ret['info'] = {
                    'start': DATETIMEfromUNIXTIMESTAMP(df['timestamp'].iloc[0], milliseconds=True),
                    'end': DATETIMEfromUNIXTIMESTAMP(df['timestamp'].iloc[-1], milliseconds=True),
                    'missing dates': None,
                    'data': df
                    }
            if len(workable_streams) > 1:
                missing_dates = []
                j = len(workable_streams)
                for i in range(1, j):
                    prev_stream = workable_streams[i-1]
                    curr_stream = workable_streams[i]
                    missing_dates.append({
                        'start': DATETIMEfromUNIXTIMESTAMP(prev_stream['end'], milliseconds=True),
                        'end': DATETIMEfromUNIXTIMESTAMP(curr_stream['start'], milliseconds=True)
                    })

                ret['info']['missing dates'] = missing_dates
            return ret

    def parse_loop_output(self, loop_output: dict) -> None:
            ticker = loop_output['ticker']
            self.result[ticker] = loop_output['info']
            return None

    def __build(self) -> None:
        datetime_errorCheck(self.start, pytz.utc)
        datetime_errorCheck(self.end, pytz.utc)
    
    def __workable_streams(self, input: dict, startUNIXMS: int, endUNIXMS: int) -> list:
        latest_data = input['latest data']
        streams = input['streams']
        workable_streams = []
        for stream_id in streams: 
            stream_start_milliseconds = streams[stream_id]['start']
            stream_end_milliseconds = streams[stream_id]['end'] if streams[stream_id]['end'] else latest_data
            if stream_start_milliseconds <= endUNIXMS and stream_end_milliseconds >= startUNIXMS:
                x = {
                    'start': stream_start_milliseconds, 
                    'end': stream_end_milliseconds, 
                    'data': streams[stream_id]['data']
                    }
                workable_streams.append(x)
        return workable_streams



    