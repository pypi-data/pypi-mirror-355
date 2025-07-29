#!python3
# -*- coding:utf-8 -*-
import zlib
import logging
import threading
import websocket
import requests
from typing import Callable
from . import parse

"""
module: Local WebSocket Client For Community User.
support: help@jvQuant.com
"""


class Construct:
    def __init__(self, market: str, token: str, log_level=logging.INFO,
                 log_handle: Callable[[str], None] = None,
                 data_handle: Callable[[str], None] = None,
                 ab_lv1_handle: Callable[[parse.AbLv1], None] = None,
                 ab_lv2_handle: Callable[[parse.AbLv2], None] = None,
                 ab_lv10_handle: Callable[[parse.AbLv10], None] = None,
                 hk_lv1_handle: Callable[[parse.HkLv1], None] = None,
                 hk_lv2_handle: Callable[[parse.HkLv2], None] = None,
                 us_lv1_handle: Callable[[parse.UsLv1], None] = None,
                 us_lv2_handle: Callable[[parse.UsLv2], None] = None,
                 ):
        """
            websocket实时行情client实例化方法入口。参考 http://jvquant.com/wiki

            Args:
                market: 市场标志，沪深:ab；港股:hk；美股:us;
                token: 平台授权Token,前往 https://jvQuant.com 查看账户Token
                log_level: 打印日志级别，例： logging.DEBUG，logging.INFO，logging.WARNING，logging.ERROR 等。
                log_handle:自定义服务器返回日志处理函数，例：def logHandle(log):
                data_handle: 自定义服务器返回行情解析函数，例：def dataHandle(data):
                ab_lv1_handle: 解析后的沪深level1行情处理函数，例：def ab_lv1_handle(lv1: jvQuant.websocket_client.parse.AbLv1):
                ab_lv2_handle: 解析后的沪深level2行情处理函数，例：def ab_lv2_handle(lv2: jvQuant.websocket_client.parse.AbLv2):
                ab_lv10_handle: 解析后的沪深十档行情处理函数，例：def ab_lv10_handle(lv10: jvQuant.websocket_client.parse.AbLv10):
                hk_lv1_handle: 解析后的港股level1行情处理函数，例：def hk_lv1_handle(lv1: jvQuant.websocket_client.parse.HkLv1):
                hk_lv2_handle: 解析后的港股level2行情处理函数，例：def hk_lv2_handle(lv2: jvQuant.websocket_client.parse.HkLv2):
                us_lv1_handle: 解析后的美股level1行情处理函数，例：def us_lv1_handle(lv1: jvQuant.websocket_client.parse.UsLv1):
                us_lv2_handle: 解析后的美股level2行情处理函数，例：def us_lv2_handle(lv2: jvQuant.websocket_client.parse.UsLv2):
            Returns:
                websocke_client: websocke_client对象。

            Raises:
                ValueError: 获取服务器或连接服务器失败。

            Examples:
                >>>
                ws=jvQuant.websocket_client
                wsclient=ws.Construct(market="ab", token=TOKEN, log_level=LOG_LEVEL,
                             ab_lv10_handle=ab_lv10_handle, ab_lv2_handle=ab_lv2_handle,)
                wsclient.add_lv2(["600519","000001","i000001"])
                wsclient.add_lv1(["600519","000001","i000001"])
                wsclient.cmd("list")
                wsclient.thread_join()
            """

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger("websocket_client")
        self.logger.setLevel(log_level)
        msg = ""

        if msg == "" and market not in {"ab", "hk", 'us'}:
            msg = "市场标志参数(market)无效。请选择有效的市场标志映射：沪深(ab)；港股(hk)；美股(us)。"

        if msg == "" and token == "":
            msg = "请输入正确的授权Token。Token获取地址: https://jvQuant.com/register.html"

        if msg == "" and not callable(data_handle):
            if (market == "hk" and not callable(hk_lv1_handle) and not callable(hk_lv2_handle)) \
                    or (market == "us" and not callable(us_lv1_handle) and not callable(us_lv2_handle)) \
                    or (market == "ab" and not callable(ab_lv1_handle) and not callable(ab_lv2_handle) and not callable(ab_lv10_handle)):
                msg = "请至少设置一个有效的行情处理函数.详见websocket_client.Construct参数定义."

        if msg != "":
            raise ValueError(msg)

        self.__log_handle = log_handle
        self.__market = market
        self.__token = token

        self.__log_handle = log_handle
        self.__log_handle_valid = callable(log_handle)

        self.__data_handle = data_handle
        self.__data_handle_valid = callable(data_handle)

        self.__ab_lv1_handle = ab_lv1_handle
        self.__ab_lv1_handle_valid = callable(ab_lv1_handle)

        self.__ab_lv2_handle = ab_lv2_handle
        self.__ab_lv2_handle_valid = callable(ab_lv2_handle)

        self.__ab_lv10_handle = ab_lv10_handle
        self.__ab_lv10_handle_valid = callable(ab_lv10_handle)

        self.__hk_lv1_handle = hk_lv1_handle
        self.__hk_lv1_handle_valid = callable(hk_lv1_handle)

        self.__hk_lv2_handle = hk_lv2_handle
        self.__hk_lv2_handle_valid = callable(hk_lv2_handle)

        self.__us_lv1_handle = us_lv1_handle
        self.__us_lv1_handle_valid = callable(us_lv1_handle)

        self.__us_lv2_handle = us_lv2_handle
        self.__us_lv2_handle_valid = callable(us_lv2_handle)

        self.__ask_for_server()

        if self.__ws_ser_addr:
            self.__conn_event = threading.Event()
            self.__th_handle = threading.Thread(target=self.__conn, daemon=True)
            self.__th_handle.start()
            self.__conn_event.wait()

    __market = ""
    __token = ""
    __ws_ser_addr = ""
    __ws_conn = ""
    __th_handle = ""

    __ab_lv1_handle: Callable[[parse.AbLv1], None]
    __ab_lv2_handle: Callable[[parse.AbLv2], None]
    __ab_lv10_handle: Callable[[parse.AbLv10], None]

    __hk_lv1_handle: Callable[[parse.HkLv1], None]
    __hk_lv2_handle: Callable[[parse.HkLv2], None]

    __us_lv1_handle: Callable[[parse.UsLv1], None]
    __us_lv2_handle: Callable[[parse.UsLv2], None]

    def cmd(self, cmd):
        """
            发送自定义指令，命令参考 http://jvquant.com/wiki

            Args:
                cmd: 命令代码
                        例：add=lv10_600519,lv2_600519;
                        all=lv1_600519
        """
        if self.__ws_conn:
            self.__ws_conn.send(cmd)
            self.logger.debug("发送指令:" + cmd)

    def add_lv1(self, code_arr: list[str]):
        """
            批量新增level1订阅。参考 http://jvquant.com/wiki

            Args:
                code_arr: 证券代码数组，
                        例：沪深["600519","000001","i000001"];
                        港股["00700","09888","09618"];
                        美股["aapl","nvda","msft"];
        """
        cmd = "add="
        op_codes = []
        for code in code_arr:
            op_codes.append("lv1_" + code)

        cmd = cmd + ",".join(op_codes)
        self.cmd(cmd)

    def del_lv1(self, code_arr: list[str]):
        """
            批量取消level1订阅。参考 http://jvquant.com/wiki

            Args:
                code_arr: 证券代码数组，
                        例：沪深["600519","000001","i000001"];
                        港股["00700","09888","09618"];
                        美股["aapl","nvda","msft"];
        """
        cmd = "del="
        op_codes = []
        for code in code_arr:
            op_codes.append("lv1_" + code)

        cmd = cmd + ",".join(op_codes)
        self.cmd(cmd)

    def add_lv10(self, code_arr: list[str]):
        """
            批量新增10档盘口(限A股)订阅。参考 http://jvquant.com/wiki

            Args:
                code_arr: 证券代码数组，
                        例：沪深["600519","000001","i000001"];
                        港股["00700","09888","09618"];
                        美股["aapl","nvda","msft"];
        """
        cmd = "add="
        op_codes = []
        for code in code_arr:
            op_codes.append("lv10_" + code)

        cmd = cmd + ",".join(op_codes)
        self.cmd(cmd)

    def del_lv10(self, code_arr: list[str]):
        """
            批量取消10档盘口(限A股)订阅。参考 http://jvquant.com/wiki

            Args:
                code_arr: 证券代码数组，
                        例：沪深["600519","000001","i000001"];
                        港股["00700","09888","09618"];
                        美股["aapl","nvda","msft"];
        """
        cmd = "del="
        op_codes = []
        for code in code_arr:
            op_codes.append("lv1_" + code)

        cmd = cmd + ",".join(op_codes)
        self.cmd(cmd)

    def add_lv2(self, code_arr: list[str]):
        """
            批量新增level2订阅。参考 http://jvquant.com/wiki

            Args:
                code_arr: 证券代码数组，
                        例：沪深["600519","000001","i000001"];
                        港股["00700","09888","09618"];
                        美股["aapl","nvda","msft"];
        """
        cmd = "add="
        op_codes = []
        for code in code_arr:
            op_codes.append("lv2_" + code)

        cmd = cmd + ",".join(op_codes)
        self.cmd(cmd)

    def del_lv2(self, code_arr: list[str]):
        """
            批量取消level2订阅。参考 http://jvquant.com/wiki

            Args:
                code_arr: 证券代码数组，
                        例：沪深["600519","000001","i000001"];
                        港股["00700","09888","09618"];
                        美股["aapl","nvda","msft"];
        """
        cmd = "del="
        op_codes = []
        for code in code_arr:
            op_codes.append("lv2_" + code)

        cmd = cmd + ",".join(op_codes)
        self.cmd(cmd)

    def thread_join(self):
        """
        等待行情子线程退出
        """
        if self.__th_handle:
            self.__th_handle.join()

    def __ask_for_server(self):
        url = "http://jvquant.com/query/server?type=websocket&token=" + self.__token + "&market=" + self.__market
        try:
            res = requests.get(url=url)
            rsp = res.json()
            if "code" in rsp and rsp["code"] == "0" and "server" in rsp:
                self.__ws_ser_addr = rsp["server"]
                self.logger.info("获取行情服务器地址成功")
            else:
                self.logger.error("分配行情服务器地址失败,服务器响应:" + res.text)
        except Exception as e:
            self.logger.error("请求行情服务器地址失败:" + str(e))

    def __conn(self):
        ws_url = self.__ws_ser_addr + "?src=pip&token=" + self.__token
        self.__ws_conn = websocket.WebSocketApp(ws_url,
                                                on_open=self.__on_open,
                                                on_data=self.__on_message,
                                                on_error=self.__on_error,
                                                on_close=self.__on_close)
        self.__ws_conn.run_forever()
        self.logger.info("websocket_client线程结束")

    def __on_open(self, ws):
        self.__conn_event.set()
        self.logger.info("行情连接已创建")

    def __on_error(self, ws, error):
        self.logger.error(error)

    def __on_close(self, ws, code, msg):
        self.logger.info("websocket_client连接已断开")

    def disconnect(self):
        self.__ws_conn.close()

    def __on_message(self, ws, message, type, flag):
        # 命令返回文本消息
        if type == websocket.ABNF.OPCODE_TEXT:
            # 发送至用户自定义日志处理
            if self.__log_handle_valid:
                self.__log_handle(message)
            self.logger.debug("Text响应:" + message)

        # 行情推送压缩二进制消息，在此解压缩
        if type == websocket.ABNF.OPCODE_BINARY:
            rb = zlib.decompress(message, -zlib.MAX_WBITS)
            text = rb.decode("utf-8")
            self.logger.debug("Binary响应:" + text)

            if self.__data_handle_valid:
                self.__data_handle(text)

            if self.__market == "ab":
                self.__parse_ab(text)
            elif self.__market == "hk":
                self.__parse_hk(text)
            elif self.__market == "us":
                self.__parse_us(text)

    '''parse ws ab start'''

    def __parse_ab(self, text: str):
        rows = text.split("\n")
        for row in rows:
            if row.startswith("lv1_") and self.__ab_lv1_handle_valid:
                self.__parse_ab_lv1(row)
            elif row.startswith("lv2_") and self.__ab_lv2_handle_valid:
                self.__parse_ab_lv2(row)
            elif row.startswith("lv10") and self.__ab_lv10_handle_valid:
                self.__parse_ab_lv10(row)

    def __parse_ab_lv1(self, row: str):
        try:
            lv1 = parse.AbLv1(row)
            self.__ab_lv1_handle(lv1)
            self.logger.debug("Parse lv1: " + str(lv1.get_map()))
        except Exception as e:
            self.logger.warning("Parse lv1 Exception:{};data:{}".format(str(e), row, ""))

    def __parse_ab_lv10(self, row: str):
        try:
            lv10 = parse.AbLv10(row)
            self.__ab_lv10_handle(lv10)
            self.logger.debug("Parse lv10:" + str(lv10.get_map()))
        except Exception as e:
            self.logger.warning("Parse lv10 Exception:{};data:{}".format(str(e), row, ""))

    def __parse_ab_lv2(self, row: str):
        try:
            lv2 = parse.AbLv2(row)
            self.__ab_lv2_handle(lv2)
            self.logger.debug("Parse lv2: " + str(lv2.get_map()))
        except Exception as e:
            self.logger.warning("Parse lv2 Exception:{};data:{}".format(str(e), row, ""))

    '''parse ws ab end'''

    '''parse ws hk start'''

    def __parse_hk(self, text: str):
        rows = text.split("\n")
        for row in rows:
            if row.startswith("lv1_") and self.__hk_lv1_handle_valid:
                self.__parse_hk_lv1(row)
            elif row.startswith("lv2_") and self.__hk_lv2_handle_valid:
                self.__parse_hk_lv2(row)

    def __parse_hk_lv1(self, row: str):
        try:
            lv1 = parse.HkLv1(row)
            self.__hk_lv1_handle(lv1)
            self.logger.debug("Parse lv1: " + str(lv1.get_map()))
        except Exception as e:
            self.logger.warning("Parse lv1 Exception:{};data:{}".format(str(e), row, ""))

    def __parse_hk_lv2(self, row: str):
        try:
            lv2 = parse.HkLv2(row)
            self.__hk_lv2_handle(lv2)
            self.logger.debug("Parse lv2: " + str(lv2.get_map()))
        except Exception as e:
            self.logger.warning("Parse lv2 Exception:{};data:{}".format(str(e), row, ""))

    '''parse ws hk end'''

    '''parse ws us start'''

    def __parse_us(self, text: str):
        rows = text.split("\n")
        for row in rows:
            if row.startswith("lv1_") and self.__us_lv1_handle_valid:
                self.__parse_us_lv1(row)
            elif row.startswith("lv2_") and self.__us_lv2_handle_valid:
                self.__parse_us_lv2(row)

    def __parse_us_lv1(self, row: str):
        try:
            lv1 = parse.UsLv1(row)
            self.__us_lv1_handle(lv1)
            self.logger.debug("Parse lv1: " + str(lv1.get_map()))
        except Exception as e:
            self.logger.warning("Parse lv1 Exception:{};data:{}".format(str(e), row, ""))

    def __parse_us_lv2(self, row: str):
        try:
            lv2 = parse.UsLv2(row)
            self.__us_lv2_handle(lv2)
            self.logger.debug("Parse lv2: " + str(lv2.get_map()))
        except Exception as e:
            self.logger.warning("Parse lv2 Exception:{};data:{}".format(str(e), row, ""))

    '''parse ws us end'''
