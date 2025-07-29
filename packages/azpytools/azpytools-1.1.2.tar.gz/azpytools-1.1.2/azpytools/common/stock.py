import tushare as ts
import pandas as pd
class stockAPITuShare:
    def __init__(self,apitoken):
        self.API = ts.pro_api(apitoken)
    
    def get_daily_by_code(self,ts_code,start_date='', end_date=''):
        """_summary_

        Args:
            ts_code (_type_): 股票代码如：300033.SZ '688362.SH,600203.SH,300223.SZ,300346.SZ'
            start_date (str, optional): 开始日期：'20200102'.
            end_date (str, optional):  开始日期：'20200202'.

        Returns:
            _type_  : _description_dataframe:
            ts_code ：代码
            trade_date  ：交易日期 
            open   ：开盘价
            high   ：最高价 
            low    ：最低价 
            close  ：收盘价 
            pre_close ：昨收价 
            previous_close ：前收价
            change  ：涨跌额 
            pct_chg ：涨跌幅 
            vol     ：成交量  
            amount ：成交额 
        """
        df =  self.API.daily(ts_code=ts_code, start_date=start_date, end_date=end_date) 
        #self.get_daily(ts_code,start_date=start_date, end_date=end_date)
        #  for index,row in df.iterrows():
        #     amt = row.get('amount')
        #     df.loc[index:index,('amount')] = amt / 10
        rows = df.shape[0]
        if rows > 0:
            for i in range(rows):
                amt = df.iloc[i]['amount']
                df.loc[i,('amount')] = amt / 10
        #         df.iloc[i]['amount'] = amt / 10
        return df
    
    def get_basic_data(self):
        """_获取股票列表

        Returns:
            _type_: _description_dataframe
        """
        df = self.API.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
        return df
    
    def get_daily_list(self,start_date='', end_date=''):
        '''获取日期列表 
        '''
        data = pd.DataFrame()
        df = self.API.trade_cal(exchange='SSE', 
                                is_open='1', 
                                start_date=start_date,   #"'20200101'"
                                end_date=end_date, 
                                fields='cal_date')
        # print(df)
        for date in df['cal_date'].values:
            df1 = self.API.daily(trade_date=date) #  self.get_daily(date)
            # print(df1)
            data = pd.concat([data,df1],axis=0) # data .concat(df1)
            # print(data)
        return data
    

                
    
    @staticmethod
    def get_open_price_by_close(lastPrice,percent):
        '''
        lastPrice:收盘价
        percent：涨幅百分比
        '''
        return 100*lastPrice / (percent + 100)
if __name__ == '__main__':
    apitoken = 'apikey'
    stock = stockAPITuShare(apitoken)
    # df = stock.get_daily_by_code('600203.SH,300223.SZ',start_date='20250612', end_date='20250612')
    # data = stock.get_basic_data()
    # data = stock.get_daily_list(start_date='20250612', end_date='20250612')
    # print(df.head())
    