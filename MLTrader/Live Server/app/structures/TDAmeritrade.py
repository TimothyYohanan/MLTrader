import atexit
import joblib
from pathlib import Path
from tda.client import Client
from tda.auth import easy_client
from tda.streaming import StreamClient
from app import resources_folder, tickers, tdaAPI_filepath, quotesHandler

class TDAmeritradeAPI:
    def __init__(self, consumer_key: str, redirect_uri: str, QOSLevel='SLOW'):
        self.consumer_key = consumer_key
        self.client_id = f'{self.consumer_key}@AMER.OAUTHAP'
        self.redirect_uri = redirect_uri
        self.trading_accountId = None
        self.token_filepath = resources_folder/'api_state'/'tdaAPI_token.json'
        self.QOSLevel = QOSLevel
        self.QOSLevels = {
            'EXPRESS': 500,
            'REAL_TIME': 750,
            'FAST': 1000,
            'MODERATE': 1500,
            'SLOW': 3000,
            'DELAYED': 5000,
        }
        self.apiUpdates_perMin = 60/(self.QOSLevels[self.QOSLevel]/1000)

        self.client()
        
    def client(self) -> object:
        client = easy_client(self.client_id, self.redirect_uri, self.token_filepath, self.__make_webdriver, asyncio=False)
        self.__get_trading_accountId(client)
        self.__save()
        return client 

    def __stream_client(self) -> object:
        client = self.client()
        stream_client = StreamClient(client, account_id=self.trading_accountId)
        return stream_client 

    async def stream_quotes(self) -> None:
        stream_client = self.__stream_client()
        await stream_client.login()
        if self.QOSLevel in self.QOSLevels:
            if self.QOSLevel == 'EXPRESS':
                await stream_client.quality_of_service(StreamClient.QOSLevel.EXPRESS)
            elif self.QOSLevel == 'REAL_TIME':
                await stream_client.quality_of_service(StreamClient.QOSLevel.REAL_TIME)
            elif self.QOSLevel == 'FAST':
                await stream_client.quality_of_service(StreamClient.QOSLevel.FAST)
            elif self.QOSLevel == 'MODERATE':
                await stream_client.quality_of_service(StreamClient.QOSLevel.MODERATE)
            elif self.QOSLevel == 'SLOW':
                await stream_client.quality_of_service(StreamClient.QOSLevel.SLOW)
            elif self.QOSLevel == 'DELAYED':
                await stream_client.quality_of_service(StreamClient.QOSLevel.DELAYED)
        else:
            raise Exception("TDAmeritradeAPI.stream_quotes: QOSLevel not in QOSLevels")

        quotesHandler.new_stream()

        stream_client.add_level_one_equity_handler(lambda msg: self.__stream_msg_pool(msg))
        await stream_client.level_one_equity_subs(tickers)
        while True:
            await stream_client.handle_message()
        return None
 
    def __stream_msg_pool(self, msg) -> None:
        streamFields = quotesHandler.level_one_quotes_fields.copy()
        streamFields.remove('timestamp')
        timestamp = msg['timestamp']
        content = msg['content']

        for frame in content:
            ticker = frame['key']
            streamedData = [frame[key] if key in frame else None for key in streamFields]
            streamedData.insert(0,timestamp)
            quotesHandler.append(ticker, timestamp, streamedData)
        self.__save()
        return None
         
    def __get_trading_accountId(self, client) -> None:
            accounts_resp = Client.get_accounts(client)
            accounts = accounts_resp.json()
            account_types = list(accounts[0].keys())
            if 'securitiesAccount' not in account_types:
                print('error: no securitiesAccount found in accounts!')
            else:
                self.trading_accountId = str(accounts[0]['securitiesAccount']['accountId'])
            return None

    def __make_webdriver(self) -> object:
        # Import selenium here because it's slow to import
        from selenium import webdriver
        chromedriverPath = Path.cwd()/'app'/'resources'/'chromedriver'
        driver = webdriver.Chrome(executable_path=chromedriverPath)
        atexit.register(lambda: driver.quit())
        return driver

    def __save(self) -> None:
        joblib.dump(self, tdaAPI_filepath)   
        return None