import joblib
import numpy as np
from pathlib import Path

# self.quotes = {
#     'oldest data': 'unixtime',
#     'current stream': 2,
#     'current stream start': 'unixtime',
#     'latest data': 'unixtime',            
#     'tickers': {
#         'AAPL': {
#             'row count': 525,
#             'oldest data': 'unixtime',
#             'latest data': 'unixtime',
#             'streams': {
#                 1: {
#                     'start': 'unixtime', 
#                     'end': 'unixtime', 
#                     'validation': bool or None,
#                     'data': 'ndarray'
#                 },
#                 0: {
#                     'start': 'unixtime', 
#                     'end': 'unixtime', 
#                     'validation': bool or None,
#                     'data': 'ndarray'
#                 },
#             }
#         }
#     }
# }

class QuotesHandler:
    def __init__(self, resources_folder: Path, tickers: list) -> None:
        self.resources_folder = resources_folder
        self.class_filepath = f'{self.resources_folder}/api_state/quotes.save'
        self.numpy_folderpath = f'{self.resources_folder}/numpy'
        self.tickers = tickers
        self.quotes = {
            'oldest data': None,
            'current stream': 0,
            'current stream start': None,
            'latest data': None,            
            'tickers': {}
        }
        self.level_one_quotes_fields = [
            'timestamp',
            'BID_PRICE',
            'ASK_PRICE',
            'LAST_PRICE',
            'BID_SIZE',
            'ASK_SIZE',
            'LAST_SIZE',
            'TRADE_TIME',
            'QUOTE_TIME',
            'TOTAL_VOLUME',
            'HIGH_PRICE',
            'LOW_PRICE',
            'CLOSE_PRICE',
            'VOLATILITY',
            'OPEN_PRICE',
            'NET_CHANGE',
            'HIGH_52_WEEK',
            'LOW_52_WEEK',
            'PE_RATIO'
            ]
        self.newStream = False
        self.firstRun = False

        self.clear()
        return None

    def clear(self) -> None:
        self.quotes = {
            'oldest data': None,
            'current stream': 0,
            'current stream start': None,
            'latest data': None,            
            'tickers': {}
        }
        
        for ticker in self.tickers:
            self.quotes['tickers'][ticker] = {
                'row count': 0,
                'oldest data': None,
                'latest data': None,
                'streams': {}
            }
        
        self.firstRun = True
        self.__save()
        return None

    def new_stream(self) -> None:
        data = np.zeros(shape=(0,len(self.level_one_quotes_fields)))
        stream_id = self.quotes['current stream']
        for ticker in self.quotes['tickers']:
            self.quotes['tickers'][ticker]['streams'][stream_id] = {
                'start': None, 
                'end': None, 
                'validation': False,
                'data': data
                }
        self.__close_previous_stream()
        self.quotes['current stream'] += 1
        self.newStream = True
        self.__save()
        return None
                  
    def append(self, ticker: str, unix_milliseconds: int, newData: list) -> None:
        stream_id = self.quotes['current stream'] - 1
        streamData = self.quotes['tickers'][ticker]['streams'][stream_id]['data']  
        self.__append_timestamp_handler(ticker, stream_id, unix_milliseconds)
        self.quotes['tickers'][ticker]['streams'][stream_id]['data'] = np.append(streamData, [newData], axis=0) 
        self.quotes['tickers'][ticker]['row count'] += 1
        self.__save()
        return None

    def __append_timestamp_handler(self, ticker: str, stream_id: int, unix_milliseconds: int) -> None:
        stream = self.quotes['tickers'][ticker]['streams'][stream_id]

        if stream['start'] is None:
            self.quotes['tickers'][ticker]['streams'][stream_id]['start'] = unix_milliseconds

        if self.newStream is True:
            self.quotes['current stream start'] = unix_milliseconds
            self.newStream = False

        if self.quotes['tickers'][ticker]['row count'] == 0:
            self.quotes['tickers'][ticker]['oldest data'] = unix_milliseconds

        if self.firstRun is True:
            self.quotes['oldest data'] = unix_milliseconds       
            self.firstRun = False

        self.quotes['tickers'][ticker]['latest data'] = unix_milliseconds
        self.quotes['latest data'] = unix_milliseconds
        return None

    def __close_previous_stream(self):
        if not self.firstRun:
            prev_stream_id = self.quotes['current stream'] - 1
            for ticker in self.quotes['tickers']:
                data = self.quotes['tickers'][ticker]['streams'][prev_stream_id]['data']
                latest_timestamp = data[-1, 0]
                self.quotes['tickers'][ticker]['streams'][prev_stream_id]['end'] = latest_timestamp
                # opted to remove the following line because it's extra processing, and there have been no validation issues so far
                # if you think there is an issue, can uncomment this and check
                # self.quotes['tickers'][ticker]['streams'][prev_stream_id]['validation'] = True if self.__timestamps_are_ordered(data) else False
        return None

    def __timestamps_are_ordered(self, np_array: np) -> bool:
        timestamps = np_array[:,0]
        if not (all(timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps)-1))):
            return False
        else:
            return True

    def __save(self) -> None:
        joblib.dump(self, self.class_filepath)   
        return None