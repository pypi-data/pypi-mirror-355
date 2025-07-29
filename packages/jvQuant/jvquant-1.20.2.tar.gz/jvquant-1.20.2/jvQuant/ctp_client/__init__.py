#!python3
# -*- coding:utf-8 -*-
import os
import time
import json
import logging
import requests
import threading

"""
module: Local CTP Client For Community User.
support:help@jvQuant.com
"""


class Construct:
    def __init__(self, token: str, ctp_acc: str, ctp_pwd: str, ticket_path="", auto_relogin=True,
                 log_level=logging.INFO):
        """
            交易CTP柜台初始化 参考 http://jvquant.com/wiki

            Args:
                token: 平台授权Token,前往 https://jvQuant.com 查看账户Token
                ctp_acc: 资金账号
                ctp_pwd: 资金密码
                ticket_path: 指定ticket信息缓存文件,留空默认保存在当前工作目录
                auto_relogin: 是否自动刷新ticket
            Returns:
                ctp_client对象

            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                ctp = jvQuant.ctp_client
                ctpclient = ctp.Construct(token=TOKEN, ctp_acc=ACCOUNT, ctp_pwd=ACCOUNT_PWD, log_level=LOG_LEVEL)
            """

        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger("ctp_client")
        self.logger.setLevel(log_level)
        msg = ""
        if msg == "" and token == "":
            msg = "请输入正确的授权Token。Token获取地址: https://jvQuant.com/register.html"

        if ticket_path == '':
            script_dir = os.getcwd()
            ticket_path = os.path.join(script_dir, "ctp_{}_ticket.json".format(ctp_acc))

        ticket_valid = False
        try:
            with open(ticket_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                old_acc = data['ctp_acc']
                if ctp_acc == old_acc:
                    expire = int(data['expire'])
                    login_stamp = int(data['login_stamp'])
                    expire_remain = login_stamp + expire - time.time()
                    expire_remain = int(expire_remain)
                    if expire_remain > 0:
                        ticket_valid = True
                        self.logger.warning("已使用指定ticket，剩余有效期:{}秒。".format(expire_remain))
                        self.__ticket_info = data
                        self.__ticket = data['ticket']
                    else:
                        self.logger.warning("指定Ticket已过期。" + str(expire_remain))
                else:
                    self.logger.warning("指定CTP账户与指定Ticket信息不符，指定的Ticket信息将失效。")
        except Exception as e:
            self.logger.warning("读取指定Ticket信息异常:" + str(e))

        if msg != "":
            raise ValueError(msg)

        self.__last_req_ser_stamp = 0
        self.__token = token
        self.__ticket_path = ticket_path
        self.auto_relogin = auto_relogin
        self.__ctp_acc = ctp_acc
        self.__ctp_pwd = ctp_pwd
        self.__ask_for_server()

        if not ticket_valid:
            self.logger.warning("需重新登录CTP。")
            self.login()

        self.__th_handle = threading.Thread(
            target=self.__ticket_expire_watch,
            daemon=True
        )
        self.__th_handle.start()

    __ctp_ser_addr = ""
    __ticket_info = {}

    def thread_join(self):
        if self.__th_handle:
            self.__th_handle.join()

    def __ask_for_server(self):
        if time.time() - self.__last_req_ser_stamp < 3:
            return
        self.__last_req_ser_stamp = time.time()
        url = "http://jvquant.com/query/server?market=ab&type=trade&token=" + self.__token
        try:
            res = requests.get(url=url)
            rsp = res.json()
            if "code" in rsp and rsp["code"] == "0" and "server" in rsp:
                self.__ctp_ser_addr = rsp["server"]
                self.logger.info("获取CTP服务器地址成功")
            else:
                self.logger.error("分配CTP服务器地址失败,服务器响应:" + res.text)
        except Exception as e:
            self.logger.error("请求CTP服务器地址失败。" + str(e))

    def __check_server(self):
        if self.__ctp_ser_addr == "":
            self.__ask_for_server()
        if self.__ctp_ser_addr == "":
            self.logger.warning("未获取到服务器，请检查后再试")
            return False
        return True

    def __ticket_expire_watch(self):
        while self.auto_relogin:
            time.sleep(60)
            data = self.__ticket_info
            if "expire" in data and "login_stamp" in data:
                expire = int(data['expire'])
                login_stamp = int(data['login_stamp'])
                expire_remain = login_stamp + expire - time.time()
                expire_remain = int(expire_remain)
                if expire_remain < 120:
                    self.logger.warning("ticket剩余有效期剩余:{}秒，将自动更新Ticket。".format(expire_remain))
                    self.login()

    def login(self):
        """
            连接登录CTP柜台，ticket自动刷新时无需手动调用 参考 http://jvquant.com/wiki

            Returns:
                授权ticket

            Examples:
                >>>
                    ctp = jvQuant.ctp_client
                    ctpclient = ctp.Construct(token=TOKEN, ctp_acc=ACCOUNT, ctp_pwd=ACCOUNT_PWD, log_level=LOG_LEVEL)
                    print("连接柜台结果",ctpclient.login())
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        self.logger.info("正在验证登录CTP柜台，请稍后...")
        url = "%s/login?&token=%s&acc=%s&pass=%s&src=pip" % (
            self.__ctp_ser_addr, self.__token, self.__ctp_acc, self.__ctp_pwd)

        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("登录柜台 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning("登录请求异常:" + str(e))

        if "code" in rsp and rsp["code"] == "0" and "ticket" in rsp:
            self.__ticket = rsp["ticket"]
            self.logger.info("获取交易凭证成功:" + self.__ticket)
            try:
                with open(self.__ticket_path, 'w', encoding='utf-8') as file:
                    file.write(json.dumps(rsp))
                    self.logger.info("已更新Ticket信息至指定文件:" + self.__ticket_path)
                    self.__ticket_info = rsp
            except Exception as e:
                self.logger.warning("写入ticket信息异常:{}".format(str(e)))
        else:
            self.logger.warning("获取交易凭证失败。url:{},response:{}".format(url, str(rsp)))
        return rsp

    def check_order(self):
        """
            查询交易委托状态 参考 http://jvquant.com/wiki

            Returns:
                交易委托结果

            Examples:
                >>>
                    ctp = jvQuant.ctp_client
                    ctpclient = ctp.Construct(token=TOKEN, ctp_acc=ACCOUNT, ctp_pwd=ACCOUNT_PWD, log_level=LOG_LEVEL)
                    print("交易委托信息",ctpclient.check_order())
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/check_order?&token=%s&ticket=%s&src=pip" % (
            self.__ctp_ser_addr, self.__token, self.__ticket)

        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("查询委托 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning("查询委托请求异常:" + str(e))
        return rsp

    def check_hold(self):
        """
            查询账户持仓信息 参考 http://jvquant.com/wiki

            Returns:
                账户持仓信息

            Examples:
                >>>
                    ctp = jvQuant.ctp_client
                    ctpclient = ctp.Construct(token=TOKEN, ctp_acc=ACCOUNT, ctp_pwd=ACCOUNT_PWD, log_level=LOG_LEVEL)
                    print("账户持仓信息",ctpclient.check_hold())
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/check_hold?&token=%s&ticket=%s&src=pip" % (
            self.__ctp_ser_addr, self.__token, self.__ticket)

        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("查询持仓 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning("查询持仓请求异常:" + str(e))
        return rsp

    def buy(self, code: str, name: str, price: str, vol: str):
        """
            买入证券 参考 http://jvquant.com/wiki

            Args:
                code: 证券代码,支持股票/可转债/ETF基金
                name: 证券名称
                price: 委托买入价格
                vol: 委托买入数量(股)
            Returns:
                委托编号

            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                    ctp = jvQuant.ctp_client
                    ctpclient = ctp.Construct(token=TOKEN, ctp_acc=ACCOUNT, ctp_pwd=ACCOUNT_PWD, log_level=LOG_LEVEL)
                    print("买入结果",ctpclient.buy("600519","贵州茅台","1572.12","1000"))
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/buy?&token=%s&ticket=%s&code=%s&name=%s&price=%s&volume=%s&src=pip" % (
            self.__ctp_ser_addr, self.__token, self.__ticket, code, name, price, vol)

        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("委托买入 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning("买入委托请求异常:" + str(e))
        return rsp

    def sale(self, code: str, name: str, price: str, vol: str):
        """
            卖出证券 参考 http://jvquant.com/wiki

            Args:
                code: 证券代码,支持股票/可转债/ETF基金
                name: 证券名称
                price: 委托卖出价格
                vol: 委托卖出数量(股)
            Returns:
                委托编号

            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                    ctp = jvQuant.ctp_client
                    ctpclient = ctp.Construct(token=TOKEN, ctp_acc=ACCOUNT, ctp_pwd=ACCOUNT_PWD, log_level=LOG_LEVEL)
                    print("卖出结果",ctpclient.sale("600519","贵州茅台","1572.12","1000"))
        """
        rsp = {}
        if not self.__check_server():
            return rsp
        url = "%s/sale?&token=%s&ticket=%s&code=%s&name=%s&price=%s&volume=%s&src=pip" % (
            self.__ctp_ser_addr, self.__token, self.__ticket, code, name, price, vol)

        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("委托卖出 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning("卖出委托请求异常:" + str(e))
        return rsp

    def cancel(self, order_id: str):
        """
            撤销委托 参考 http://jvquant.com/wiki

            Args:
                order_id: 委托编号

            Returns:
                撤单结果

            Raises:
                ValueError: 获取服务器或请求服务器失败。

            Examples:
                >>>
                    ctp = jvQuant.ctp_client
                    ctpclient = ctp.Construct(token=TOKEN, ctp_acc=ACCOUNT, ctp_pwd=ACCOUNT_PWD, log_level=LOG_LEVEL)
                    print("撤单结果",ctpclient.cancel("9702"))
        """
        rsp = {}
        if not self.__check_server():
            return
        url = "%s/cancel?&token=%s&ticket=%s&order_id=%s&src=pip" % (
            self.__ctp_ser_addr, self.__token, self.__ticket, order_id)

        try:
            res = requests.get(url=url)
            rsp = res.json()
            self.logger.debug("撤销委托 url: {};status_code: {};response: {}".format(url, res.status_code, res.text))
        except Exception as e:
            self.logger.warning("撤销委托请求异常:" + str(e))
        return rsp
