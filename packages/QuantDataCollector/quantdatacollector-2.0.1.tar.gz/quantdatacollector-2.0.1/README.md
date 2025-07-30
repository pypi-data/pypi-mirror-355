# 数据收集

## 简介

> QuantDataCollector的目的是提供统一、稳定的数据接口，用户可以不用考虑数据获取问题，专注策略开发。



## 使用

> 使用Cache前需要先完成环境变量配置，比如使用MYSQL作为缓存，则需要设置MYSQL环境变量，具体参考下文

通过DataCollector类向外提供统一接口，以获取所有股票sz.399995的基本信息为例：

```python
import QuantDataCollector as qdc
data_collector = qdc()
data = data_collector.get_stock_basic('000001.SZ')
print(data)
```

> code  name are exchage market list_status   list_date unlist_date act_name act_type
> 
> 0  000001.SZ  平安银行  深圳    SZSE     主板           L  1991-04-03        None   无实际控制人        无


### 日志查看

通过`get_data_collector_info`接口查看日志路径，进而查看日志

```python
import QuantDataCollector as qdc

data_collector = qdc()
print(data_collector.get_data_collector_info())
```


## 如何设置MySQL

目前仅支持MySQL作为缓存，为了使用缓存，需要设置环境变量：

* MYSQL_HOST: MySQL服务器地址
* MYSQL_PORT: MySQL服务器端口
* MYSQL_USER: MySQL用户名
* MYSQL_PASSWORD: MySQL密码

环境变量设置方法

* Windows
    `set MYSQL_HOST=192.168.71.17`
    
* Linux / MacOS
    相比Windows要简单一些，只需要`export MYSQL_HOST=192.168.6.19`即可


## 数据源及其特点


### [baostock](http://baostock.com/baostock/index.php/%E9%A6%96%E9%A1%B5)

已经包装好的**股票数据拉取**Python库，数据覆盖

- 股票
- 公司业绩
- 货币
- 存款利率

优点：

- 使用简单

缺点：

- 服务由他人提供，已有收费趋势，可用性不高



### [tushare](https://tushare.pro/)

tushare的数据比较全面，使用也很方便，但很多功能是需要付费使用的


## API接口

### get_stock_basic

获取股票基本信息

* 输入参数
    * code: 指定需要的股票代码，格式为000001.SZ，可选参数，如果不指定，则返回所有股票的基本信息
* 输出参数

    输入为pandas的DataFrame
    * code: 股票代码
    * name: 股票名称
    * area: 上市公司所在省份
    * exchage: 交易所代码
    * market: 市场类型（主板/创业板/科创板/CDR）
    * list_status： 上市状态 L上市 D退市 P暂停上市，默认是L
    * list_date：上市日期
    * unlist_date：退市日期
    * act_name：实控人名称
    * act_type：实控人性质

### get_limit_list

获取股票涨停、跌停、炸板信息

* 输入参数
    * date: 出现涨停、跌停、炸板信息的日期，格式为'yyyy-mm-dd'。可选参数，不指定表示不限制日期
    * code: 指定需要的股票代码，格式为000001.SZ，可选参数，如果不指定，则不限制代码
    * type: 涨跌停、炸板类型：U涨停D跌停Z炸板，可选参数，不指定表示不限制类型
* 输出参数

    输出为pandas的DataFrame
    * code: 股票代码
    * date: 发生涨跌停的日期
    * limit_amount: 板上成交金额(成交价格为该股票跌停价的所有成交额的总和，涨停无此数据)
    * fd_amount： 封单金额（以涨停价买入挂单的资金总量）
    * first_time： 首次封板时间（跌停无此数据）
    * last_time：最后封板时间
    * open_times：炸板次数(跌停为开板次数)
    * up_stat：涨停统计（N/T T天有N次涨停）
    * limit_times：连板数（个股连续封板数量）
    * limit_type：D跌停U涨停Z炸板

### get_holder_number
    获取股票的股东数量

* 输入参数
    * code: 股票代码, 如果不传则查询所有股票的股东数量
    * cut_off_date: 指定数据统计的截止日期，格式为YYYY-MM-DD，返回数据统计的截止日期在该日期之前的所有数据，默认为查询所有截止日期的数据
    
* 输出参数
    输出为pandas的DataFrame
    * code: 股票代码
    * ann_pub_date: 公告发布的日期
    * cut_off_date: 股东人数数据统计的截止日期
    * holder_num: 股东人数