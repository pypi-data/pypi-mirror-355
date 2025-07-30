import logging
import os
import atexit # 用于捕捉程序退出
import signal # 处理系统函数，包括Ctrl + C等
import pandas as pd

from QuantDataCollector.Utils.mysql_utils import mysqlOps
from QuantDataCollector.Global.settings import *
from QuantDataCollector.Utils.file_utils import mkdir

class DataCollectorError(Exception):  # 继承自 Exception 基类
    """自定义异常的说明文档"""
    pass  # 通常不需要额外逻辑，用 pass 占位即可

class DataCollector:

    def __init__(self):
        signal.signal(signal.SIGINT, self.signal_exit) # 捕捉SIGINT事件，并在signal_exit函数中处理
        atexit.register(self.cleanUp) # 程序退出时执行cleanUp函数
        self.db = mysqlOps(STOCK_DATABASE_NAME)
        self.__config_logging()

    def __del__(self):
        pass

    def signal_exit(self,signum,frame):
        self.__logger.info("my_exit: interrupted by ctrl+c")
        self.cleanUp()
        exit()

    def cleanUp(self):
        pass

    def __config_logging(self, level = logging.WARNING):
        if level == logging.DEBUG:
            print("================= data collector info ==================")
            print(self.get_data_collector_info())
            print("================= end of collector info ==================")
        self.__logger = logging.getLogger('data_collector')
        
        if not os.path.exists(LOGGING_FILE_DIR):
            mkdir(LOGGING_FILE_DIR)
        ch = logging.FileHandler(LOGGING_FILE_NAME)
        formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)
        self.__logger.addHandler(ch)
        self.__logger.setLevel(level)

    def get_data_collector_info(self):
        res = ""
        res += "log path:" + LOGGING_FILE_NAME + "\n"
        return res

    """
    获取股票基本信息
    """
    def get_stock_basic(self, code = None):
        filter = None
        if code != None:
            filter = "code = '" + code + "'"

        res, data = self.db.query(STOCK_BASIC_INFO_TABLE_NAME, None, filter)
        if res:
            columns = ['code', 'name', 'area', 'exchage','market', 'list_status', 'list_date', 'unlist_date','act_name', 'act_type']
            df = pd.DataFrame(data, columns=columns)
            return df
        raise DataCollectorError("获取股票基本信息失败，错误信息：" + str(data))

    def get_limit_list(self, date = None, code = None, type = None):
        filter = None
        if date:
            filter = "date = '" + date + "'"
        if code:
            if filter == None:
                filter = "code ='" + code + "'"
            else:
                filter += " and code ='" + code + "'"
        if type:
            if filter == None:
                filter = "limit_type = '" + type + "'"
            else:
                filter += " and limit_type = '" + type + "'"
        columns = ['code', 'date', 'limit_amount', 'fd_amount','first_time', 'last_time', 'open_times', 'up_stat', 'limit_times', 'limit_type']
        res, data = self.db.query(STOCK_LIMIT_LIST_DAY_TABLE_NAME, columns, filter)
        if res:
            df = pd.DataFrame(data, columns=columns)
            return df

    """
    获取股票的股东数量
    @Parameters:
    - code: 股票代码, 如果不传则查询所有股票的股东数量
    - cut_off_date: 指定数据统计的截止日期，格式为YYYY-MM-DD，返回数据统计的截止日期在该日期之前的所有数据，默认为查询所有截止日期的数据
    """
    def get_holder_number(self, code = None, cut_off_date = None):
        filter = None
        if cut_off_date:
            filter = "cut_off_date < '" + cut_off_date + "'"
        if code:
            if filter == None:
                filter = "code ='" + code + "'"
            else:
                filter += " and code ='" + code + "'"
        columns = ['code', 'ann_pub_date', 'cut_off_date', 'holder_num']
        res, data = self.db.query(STOCK_HOLDER_NUMBER_TABLE_NAME, columns, filter)
        if res:
            df = pd.DataFrame(data, columns=columns)
            # 假设 df 是原始 DataFrame，'date_column' 是日期列名
            df['cut_off_date'] = pd.to_datetime(df['cut_off_date'])  # 步骤1：转换日期格式
            df_sorted = df.sort_values(by='cut_off_date', ascending=False)          # 步骤2：按日期排序
            return df_sorted

if __name__ == '__main__':
    data_collector = DataCollector()