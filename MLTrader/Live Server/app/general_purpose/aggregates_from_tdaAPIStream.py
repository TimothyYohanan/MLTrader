import numpy as np
import pandas as pd

aggregateTypes = {'minute': 60, 'hour': 3600, 'day': 86400}
aggregateFields = [
    'LAST_PRICE',
    'LAST_SIZE',           # Number of shares traded with last trade, in 100’s
    # 'BID_SIZE',
    # 'ASK_SIZE',
    # 'HIGH_PRICE',
    # 'LOW_PRICE',
    # 'CLOSE_PRICE',
    # 'VOLATILITY',
    # 'OPEN_PRICE',
    # 'NET_CHANGE',
    # 'HIGH_52_WEEK',
    # 'LOW_52_WEEK'
    ]
custom_aggregateFields = [
    'aggregate_high',      # highest traded price during aggregate period
    'aggregate_low',       # lowest traded price during aggregate period
    'volume_increase',     # percent change in LAST_SIZE since last aggregate. LAST_SIZE = PREV_LAST_SIZE + (PREV_LAST_SIZE * volume_increase)
    'price_gradient'       # number representing LAST_PRICE proximity to aggregate_high (1) or aggregate_low (-1)
    ]

all_aggregateFields = aggregateFields + custom_aggregateFields

def round_unixTime(unixTime: int, timeDelta: int, roundUp=False):
    unixTime_floor = unixTime // timeDelta * timeDelta
    if roundUp:
        return unixTime_floor + timeDelta
    else:
        return unixTime_floor

def check_aggregateType(pastTimesteps_aggregateType: str, futureTimesteps_aggregateType: str):
    if pastTimesteps_aggregateType not in aggregateTypes or futureTimesteps_aggregateType not in aggregateTypes:
        raise Exception('function "check_aggregateType" says: "Used an invalid aggregate type."')
    else:
        return True

def minTimedelta(reads_pastTimesteps: int, pastTimesteps_aggregateType: str, predicts_futureTimesteps: int, futureTimesteps_aggregateType: str, ms=False) -> int:
    td_sec = [
        int(reads_pastTimesteps * aggregateTypes[pastTimesteps_aggregateType]), 
        int(predicts_futureTimesteps * aggregateTypes[futureTimesteps_aggregateType])
        ]
    if ms:
        return min(td_sec) * 1000
    else:
        return min(td_sec)

# should never have to use this bc of new TDAmeritrade.__level_one_quotes_handler, but leaving this here just for reference
def populateNULL_cols(df: pd.DataFrame) -> pd.DataFrame:
    _df = df.copy()
    cols = _df.columns
    firstRow_nulls = [col for col in _df.iloc[0] if col is None]
    if firstRow_nulls:
        raise Exception(f'function "populateNULL_cols" says: "First row in df has null values at columns: {firstRow_nulls}"')
    for i in range(1, _df.shape[0]):
        prev_row = _df.iloc[i-1]
        curr_row = _df.iloc[i]
        for col in cols:
            if curr_row[col] is None:
                curr_row[col] = prev_row[col]
    return _df

def aggregatePlanner(df: pd.DataFrame, firstTimestamp: int, lastTimestamp: int, timeDelta: int) -> dict:
    firstTimestamp_rounded = round_unixTime(firstTimestamp, timeDelta, roundUp=False)
    lastTimestamp_rounded = round_unixTime(lastTimestamp, timeDelta, roundUp=True) + timeDelta
    timesteps = np.arange(firstTimestamp_rounded, lastTimestamp_rounded, timeDelta).tolist()
    aggregatePlan = {timestep: [] for timestep in timesteps}
    for row in df.itertuples():
        aggregate = min([timestamp for timestamp in timesteps if int(row.timestamp) < timestamp])
        if aggregatePlan[aggregate]:
            if len(aggregatePlan[aggregate]) > 1:
                del aggregatePlan[aggregate][-1]
            aggregatePlan[aggregate].append(row.Index)
        else:
            aggregatePlan[aggregate].append(row.Index)
    return aggregatePlan

def aggregateField(df: pd.DataFrame, aggregates: list[dict], start: int, end: int, field: str):
    df_slice = df.iloc[start:end]
    if aggregates:
        prevSlice = aggregates[-1]
    else:
        prevSlice = None
    if field == 'LAST_PRICE':
        return df_slice['LAST_PRICE'].iloc[-1]
    if field == 'LAST_SIZE':
        return df_slice['LAST_SIZE'].sum()
    if field == 'OPEN_PRICE':
        return df_slice['OPEN_PRICE'].iloc[-1]
    if field == 'aggregate_high':
        return df_slice['LAST_PRICE'].max()
    if field == 'aggregate_low':
        return df_slice['LAST_PRICE'].min()
    if field == 'volume_increase':
        if prevSlice is None:
            return None
        else:
            return (df_slice['LAST_SIZE'].sum() - prevSlice['LAST_SIZE']) / (prevSlice['LAST_SIZE'])
    if field == 'price_gradient':
        low = df_slice['LAST_PRICE'].min()
        high = df_slice['LAST_PRICE'].max()
        close = df_slice['LAST_PRICE'].iloc[-1]
        lst = sorted(list((low, high, close)))
        x_min = lst[0]
        x_max = lst[-1]
        if close == x_min:
            return 0
        else:
            return 2 * ((close - x_min) / (x_max - x_min)) - 1
    else:
        return None

def createAggregates(df: pd.DataFrame, aggregatePlan: dict):
    aggregates = []
    col_order = all_aggregateFields.copy()
    col_order.insert(0,'timestamp')
    for item in aggregatePlan:
        if aggregatePlan[item]:
            start = aggregatePlan[item][0]
            end = aggregatePlan[item][-1] + 1
            aggregate = {field: aggregateField(df, aggregates, start, end, field) for field in all_aggregateFields}
            aggregate['timestamp'] = item
            aggregates.append(aggregate)
    aggregates_df = pd.DataFrame(aggregates) 
    aggregates_df = aggregates_df[col_order]
    return aggregates_df

def aggregates_from_tdaAPIStream(df: pd.DataFrame, reads_pastTimesteps: int, pastTimesteps_aggregateType: str, predicts_futureTimesteps: int, futureTimesteps_aggregateType: str) -> pd.DataFrame: 
    check_aggregateType(pastTimesteps_aggregateType, futureTimesteps_aggregateType)
    msTimedelta = minTimedelta(reads_pastTimesteps, pastTimesteps_aggregateType, predicts_futureTimesteps, futureTimesteps_aggregateType, ms=True)
    firstTimestamp = int(df['timestamp'].iloc[0])
    lastTimestamp = int(df['timestamp'].iloc[-1])
    aggregatePlan = aggregatePlanner(df, firstTimestamp, lastTimestamp, msTimedelta)
    aggregates_df = createAggregates(df, aggregatePlan)
    return aggregates_df
        

        
    







    

    