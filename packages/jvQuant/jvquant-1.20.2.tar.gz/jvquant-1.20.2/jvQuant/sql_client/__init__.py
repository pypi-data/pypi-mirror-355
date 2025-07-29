#!python3
# -*- coding:utf-8 -*-
import os
import time
import logging
import requests

"""
module: Local SQL Client For Community User.
support:help@jvQuant.com
"""


class Construct:
    def __init__(self, token: str, log_level=logging.INFO):
        """
            在线数据库服务sql_client实例化方法入口。参考 http://jvquant.com/wiki

            Args:
                token: 平台授权Token,前往 https://jvQuant.com 查看账户Token
            Returns:


            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                sql = jvQuant.sql_client
                sqlclient=sql.Construct(token=TOKEN,log_level=LOG_LEVEL)
            """

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger("sql_client")
        self.logger.setLevel(log_level)
        msg = ""
        if msg == "" and token == "":
            msg = "请输入正确的授权Token。Token获取地址: https://jvQuant.com/register.html"

        if msg != "":
            raise ValueError(msg)

        self.__last_req_ser_stamp = 0
        self.__token = token
        self.__ask_for_server()

    __sql_ser_addr = ""

    def __ask_for_server(self):
        if time.time() - self.__last_req_ser_stamp < 3:
            return
        self.__last_req_ser_stamp = time.time()
        url = "http://jvquant.com/query/server?market=ab&type=sql&token=" + self.__token
        try:
            res = requests.get(url=url)
            rsp = res.json()
            if "code" in rsp and rsp["code"] == "0" and "server" in rsp:
                self.__sql_ser_addr = rsp["server"]
                self.logger.info("获取数据库服务器地址成功")
            else:
                self.logger.error("分配数据库服务器地址失败,服务器响应:" + res.text)
        except Exception as e:
            self.logger.error("请求数据库服务器地址失败" + str(e))

    def __check_server(self):
        if self.__sql_ser_addr == "":
            self.__ask_for_server()
        if self.__sql_ser_addr == "":
            self.logger.warning("未获取到服务器，请检查后再试")
            return False
        return True

    def query(self, query, page=1, sort_type=1, sort_key=""):
        """
            智能语义查询 参考 http://jvquant.com/wiki

            Args:
                query: 查询语句,多个条件逗号分隔。
                page: 查询页表。
                sort_type: 按指定排序方式,0为升序,1为降序。默认升序
                sort_key: 指定排序字段，详见查询结果内sorts列表
            Returns:
                语义分析和查询结果

            Raises:
                ValueError: 获取服务器或连接服务器失败。

            Examples:
                >>>
                    sql = jvQuant.sql_client
                    sqlclient = sql.Construct(token=TOKEN,log_level=LOG_LEVEL)
                    sqlclient.query("主板,非ST,价格,近5日涨幅,市盈率，市值大于20亿小于100亿，量比，营业额，利润率，利润，行业，股东人数，IPO时间",1,0,"INDUSTRY")
                    sqlclient.query("集合竞价抢筹,30日均线向上,量比",1,1,"QRR")
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/sql?&mode=sql&&token=%s&query=%s&page=%s&sort_type=%s&sort_key=%s&src=pip" % (
            self.__sql_ser_addr, self.__token, query, page, sort_type, sort_key)
        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("语义查询 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning(e)
        return rsp

    def kline(self, code, cate="stock", fq="前复权", type="day", limit=240):
        """
            获取K线公共方法 参考 http://jvquant.com/wiki

            Args:
                code: 证券代码，支持股票，可转债，ETF，指数。
                cate: 指定品种,stock/bond/etf/index,缺省默认为stock。
                fq: 复权类型,支持前复权/后复权/不复权,缺省默认为前复权。
                type: K线类型,支持日线(day),周线(week),月线(month),缺省默认为day。
                limit: 限定查询K线长度,最长支持30年倒查,按需查询可加快查询速度。
            Returns:
                K线数据体

            Raises:
                ValueError: 获取服务器或连接服务器失败。

            Examples:
                >>>
                    sql = jvQuant.sql_client
                    sqlclient = sql.Construct(token=TOKEN,log_level=LOG_LEVEL)
                    sqlclient.kline("600519", "stock", "前复权", "week", 2)
                    sqlclient.kline("000001", "index", "后复权", "day", 2)
                    sqlclient.kline("000001", "stock", "不复权", "day", 2)
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/sql?&mode=kline&token=%s&code=%s&cate=%s&type=%s&fq=%s&limit=%s&src=pip" % (
            self.__sql_ser_addr, self.__token, code, cate, type, fq, limit)
        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("K线查询 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning(e)
        return rsp

    def bond(self):
        """
        查询所有可转债基本信息 参考 http://jvquant.com/wiki

        Returns:
            ["转债代码","转债简称","正股代码","正股简称","发行规模(亿)","发行价格","发行日期","币种","到期日","票面利率","付息日","计息方式","付息方式","转股日期","强赎触发价","正股价(昨收)","转股价","转股价值","纯债价值","转股溢价(昨收)"]
        """
        rsp = {}
        if not self.__check_server():
            return rsp

        url = "%s/sql?&mode=bond&token=%s&src=pip" % (
            self.__sql_ser_addr, self.__token)
        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("可转债基本信息 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning(e)
        return rsp

    def industry(self):
        """
        获取所有证券的申万行业分类 参考 http://jvquant.com/wiki

        Returns:
                ["股票代码","股票简称","所属行业","流通股数"]
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/sql?&mode=industry&token=%s&src=pip" % (
            self.__sql_ser_addr, self.__token)
        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("申万行业信息 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning(e)
        return rsp

    def minute(self, code: str, end_day: str, limit: int):
        """
            查询历史分时数据 参考 http://jvquant.com/wiki

            Args:
                code: 证券代码，可以是股票代码、指数代码等
                end_day: 查询的结束日期。
                limit: 指定时间长度。
            Returns:
                指定时间段内分时数据

            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                    sql = jvQuant.sql_client
                    sqlclient = sql.Construct(token=TOKEN,log_level=LOG_LEVEL)
                    sqlclient.minute("600519",'2016-06-21',2)
                    sqlclient.minute("i000001",'2009-06-21',2)#指数分时
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/sql?&mode=minute&token=%s&code=%s&end_day=%s&limit=%s&src=pip" % (
            self.__sql_ser_addr, self.__token, code, end_day, limit)
        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("历史分时查询 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning(e)
        return rsp

    def order_book(self, code: str, offset=0):
        """
            查询逐笔委托队列 参考 http://jvquant.com/wiki

            Args:
                code: 股票代码。
                offset: 支持按队列偏移量查询，未指定则查询最新数据。
            Returns:
                逐笔委托队列

            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                sql = jvQuant.sql_client
                sqlclient = sql.Construct(token=TOKEN,log_level=LOG_LEVEL)
                sqlclient.order_book("000001",0) #最新队列
                sqlclient.order_book("600519",40676443) #倒推查询
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/sql?&mode=order_book&token=%s&code=%s&offset=%s&src=pip" % (
            self.__sql_ser_addr, self.__token, code, offset)
        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("逐笔委托查询 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning(e)
        return rsp

    def level_queue(self, code):
        """
            查询千档盘口 参考 http://jvquant.com/wiki

            Args:
                code: 股票代码。
            Returns:
                千档盘口

            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                sql = jvQuant.sql_client
                sqlclient = sql.Construct(token, logging.INFO)
                sqlclient.level_queue("000001")
                sqlclient.level_queue("600519")
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/sql?&mode=level_queue&token=%s&code=%s&src=pip" % (
            self.__sql_ser_addr, self.__token, code)
        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("千档盘口查询 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning(e)
        return rsp

    def download_history(self, year: str, save_path=''):
        """
            下载历史分时数据 参考 http://jvquant.com/wiki

            Args:
                year: 指定数据年份。
                save_path: 指定下载文件存储路径。
            Returns:
                历史数据打包文件

            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                sql = jvQuant.sql_client
                sqlclient = sql.Construct(token=TOKEN,log_level=LOG_LEVEL)
                # 全量下载2008~2016年历史分时
                for i in range(2008,2016):
                    sqlclient.download_history(str(i))
                # 指定年份下载
                sqlclient.download_history("2024")
                sqlclient.download_history("2025")
        """
        if not self.__check_server():
            return
        url = "%s/sql?&mode=history&token=%s&year=%s.zip&stamp=%s&src=pip" % (
            self.__sql_ser_addr, self.__token, year, time.time())
        if save_path == '':
            script_dir = os.getcwd()
            save_path = os.path.join(script_dir, year + ".zip")
        self.logger.info("开始下载历史数据文件:{},保存路径:{}".format(year + ".zip", save_path))
        response = requests.get(url, stream=True)

        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/zip' not in content_type:
            self.logger.warning("{} 文件下载异常:{}".format(year + ".zip", response.text))
            return

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        block_size = 1024
        start_time = time.time()
        last_updated = 0

        with open(save_path, 'wb') as file:
            for data in response.iter_content(block_size):
                downloaded_size += len(data)
                file.write(data)

                current_time = time.time()
                if current_time - last_updated < 0.5 and downloaded_size < total_size:
                    continue
                last_updated = current_time

                elapsed_time = current_time - start_time
                speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0

                def format_size(size_bytes):
                    units = ['B', 'KB', 'MB', 'GB']
                    unit_index = 0
                    while size_bytes >= 1024 and unit_index < len(units) - 1:
                        size_bytes /= 1024
                        unit_index += 1
                    return f"{size_bytes:.2f} {units[unit_index]}"

                remaining_size = total_size - downloaded_size
                if speed > 0:
                    eta_seconds = remaining_size / speed
                    if eta_seconds < 60:
                        eta = f"{eta_seconds:.1f}s"
                    elif eta_seconds < 3600:
                        eta = time.strftime('%M:%S', time.gmtime(eta_seconds))
                    else:
                        eta = time.strftime('%H:%M:%S', time.gmtime(eta_seconds))
                else:
                    eta = "--:--"
                progress = f"\r下载中: {year}.zip，已下载[{format_size(downloaded_size)}/{format_size(total_size)}] ，下载速度[{format_size(speed)}/s] [剩余时间: {eta}]"
                print(progress, end="")
        msg = f"{year}年历史分时数据下载完成，耗时: {time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))}"
        self.logger.info(msg)
