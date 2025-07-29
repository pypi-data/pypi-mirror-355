# jvQuant Python社区功能包说明

该功能包分为 **WebSocket实时行情**、**CTP柜台**、**在线数据库** 三个模块。

请参考官方社区文档: [官方文档](http://jvquant.com/wiki)

## WebSocket实时行情推送

支持**沪深**、**港股**、**美股** 三大市场全部证券，Level1/十档/Level2逐笔成交行情实时推送。

### WebSocket行情接入示例

#### 沪深WebSocket行情接入示例
```python3
import jvQuant
import logging

'''沪深行情订阅示例'''


# 自定义日志处理函数
def logHandle(log: str):
    print("应用日志:", log)


# 自定义原始行情处理函数
def dataHandle(data: str):
    print("Binary解析结果:", data)


# 自定义level1行情处理函数
def ab_lv1_handle(lv1: jvQuant.websocket_client.parse.AbLv1):
    print("level1推送:", lv1.get_map())


# 自定义level2行情处理函数
def ab_lv2_handle(lv2: jvQuant.websocket_client.parse.AbLv2):
    print("level2推送:", lv2.get_map())


# 自定义十档行情处理函数
def ab_lv10_handle(lv10: jvQuant.websocket_client.parse.AbLv10):
    print("十档推送:", lv10.get_map())


# 沪深市场标志
market = "ab"
# 平台授权Token
token = ""
# 打印调试信息
log_level = logging.DEBUG
# log_level = logging.INFO

ws = jvQuant.websocket_client

# 注册自定义行情处理函数
wsclient = ws.Construct(market=market, token=token, log_level=log_level, log_handle=logHandle, data_handle=dataHandle,
                        ab_lv1_handle=ab_lv1_handle, ab_lv2_handle=ab_lv2_handle, ab_lv10_handle=ab_lv10_handle)

# 发送订阅代码
wsclient.add_lv1(["600519", "000001", "i000001"])
wsclient.add_lv2(["600519", "000001", "i000001"])
wsclient.add_lv10(["600519", "000001", "i000001"])

# 等待子线程结束
wsclient.thread_join()

```

#### 港股WebSocket行情接入示例

```python3
import jvQuant
import logging

'''港股行情订阅示例'''


# 自定义日志处理函数
def logHandle(log: str):
    print("应用日志:", log)


# 自定义原始行情处理函数
def dataHandle(data: str):
    print("Binary解析结果:", data)


# 自定义level1行情处理函数
def hk_lv1_handle(lv1: jvQuant.websocket_client.parse.HkLv1):
    print("level1推送:", lv1.get_map())


# 自定义level2行情处理函数
def hk_lv2_handle(lv2: jvQuant.websocket_client.parse.HkLv2):
    print("level2推送:", lv2.get_map())


# 港股市场标志
market = "hk"
# 平台授权Token
token = ""
# 打印调试信息
log_level = logging.DEBUG
# log_level = logging.INFO

ws = jvQuant.websocket_client

# 注册自定义行情处理函数
wsclient = ws.Construct(market=market, token=token, log_level=log_level, log_handle=logHandle, data_handle=dataHandle,
                        hk_lv1_handle=hk_lv1_handle, hk_lv2_handle=hk_lv2_handle)

# 发送订阅代码
wsclient.add_lv1(["00700", "09888", "09618"])
wsclient.add_lv2(["00700", "09888", "09618"])

# 等待子线程结束
wsclient.thread_join()

```


#### 美股WebSocket行情接入示例
```python3
import jvQuant
import logging

'''美股行情订阅示例'''


# 自定义日志处理函数
def logHandle(log: str):
    print("应用日志:", log)


# 自定义原始行情处理函数
def dataHandle(data: str):
    print("Binary解析结果:", data)


# 自定义level1行情处理函数
def us_lv1_handle(lv1: jvQuant.websocket_client.parse.UsLv1):
    print("level1推送:", lv1.get_map())


# 自定义level2行情处理函数
def us_lv2_handle(lv2: jvQuant.websocket_client.parse.UsLv2):
    print("level2推送:", lv2.get_map())


# 美股市场标志
market = "us"
# 平台授权Token
token = ""
# 打印调试信息
log_level = logging.DEBUG
# log_level = logging.INFO

ws = jvQuant.websocket_client

# 注册自定义行情处理函数
wsclient = ws.Construct(market=market, token=token, log_level=log_level, log_handle=logHandle, data_handle=dataHandle,
                        us_lv1_handle=us_lv1_handle, us_lv2_handle=us_lv2_handle)

# 发送订阅代码
wsclient.add_lv1(["aapl", "nvda", "msft"])
wsclient.add_lv2(["aapl", "nvda", "msft"])

# 等待子线程结束
wsclient.thread_join()

```

## CTP柜台交易

券商柜台全部功能实现:

- 证券交易
- 持仓查询
- 交易查询
- 委托撤单

### CTP接入示例:

```python3
import jvQuant
import logging

# 资金账号
ACCOUNT = ""
# 资金密码
ACCOUNT_PWD = ""
# 平台授权Token
TOKEN = ""
# 打印调试信息
LOG_LEVEL = logging.DEBUG
# LOG_LEVEL = logging.INFO

ctp = jvQuant.ctp_client
ctpclient = ctp.Construct(token=TOKEN, ctp_acc=ACCOUNT, ctp_pwd=ACCOUNT_PWD, log_level=LOG_LEVEL)

# 查询持仓信息
response = ctpclient.check_hold()

# 查询委托状态
response = ctpclient.check_order()

# 委托买入
response = ctpclient.buy("600519", "贵州茅台", "1572.12", "1000")

# 委托卖出
response = ctpclient.sale("600519", "贵州茅台", "1572.12", "1000")

# 撤销委托
response = ctpclient.cancel("9702")

# 等待子线程结束
ctpclient.thread_join()

```

## 在线数据库服务

实现功能服务如下:

- **智能语义**查询
- 获取**所有证券**的申万行业分类
- 获取所有**可转债**基本信息
- 历史分时数据查询:提供2008~至今历**史分时数据**查询及打包下载
- K线查询:支持**股票**、**可转债**、**ETF**、**指数**，提供近30年K线查询。支持**日K/周K/月K**，**前复权、后复权、不复权**等
- Level2**逐笔委托**队列查询
- Level2**千档盘口**查询

### SQL接入示例:

```python3
import jvQuant
import logging

TOKEN = ""
# 打印调试信息
LOG_LEVEL = logging.DEBUG
# LOG_LEVEL = logging.INFO

sql = jvQuant.sql_client
sqlclient = sql.Construct(TOKEN, LOG_LEVEL)

# 获取所有可转债基本信息
response = sqlclient.bond()

# 获取所有证券的申万行业分类
response = sqlclient.industry()

# Level2千档盘口查询
response = sqlclient.level_queue("600519")

# Level2逐笔委托队列查询
response = sqlclient.order_book("000001", 0)  # 最新队列
response = sqlclient.order_book("600519", 40676443)  # 倒推查询

# 历史分时数据查询
response = sqlclient.minute("600519", '2016-06-21', 2)
response = sqlclient.minute("i000001", '2009-06-21', 2)  # 指数分时

# 智能语义查询
response = sqlclient.query("主板,非ST,价格,近5日涨幅,市盈率，市值大于20亿小于100亿，量比，营业额，利润率，利润，行业，股东人数，IPO时间", 1, 0, "INDUSTRY")
response = sqlclient.query("集合竞价抢筹,30日均线向上,量比", 1, 1, "QRR")

# K线查询
response = sqlclient.kline("600519", "stock", "前复权", "week", 2)
response = sqlclient.kline("000001", "index", "后复权", "day", 2)
response = sqlclient.kline("000001", "stock", "不复权", "day", 2)

# 历史分时数据打包下载
# 遍历下载2008~2016年历史分时
for i in range(2008, 2016):
    sqlclient.download_history(str(i))

# 指定年份下载
sqlclient.download_history("2024")
sqlclient.download_history("2025")

```

- 问题反馈:`help@jvQuant.com`
- 官方社区文档: [官方文档](http://jvquant.com/wiki)
