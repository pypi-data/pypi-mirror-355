"""
module: Data Parser Module For Local WebSocket Client.
support: help@jvQuant.com
"""


def get_map(obj: object):
    if hasattr(obj, '__dict__'):
        return {k: obj_to_dict(obj, v) for k, v in vars(obj).items()}
    elif hasattr(obj, '__slots__'):
        return {attr: obj_to_dict(obj, getattr(obj, attr)) for attr in obj.__slots__}
    else:
        return {}


def obj_to_dict(obj: object, value):
    if isinstance(value, list):
        return [obj_to_dict(obj, item) for item in value]
    elif hasattr(value, '__dict__'):
        return {k: obj_to_dict(obj, v) for k, v in vars(value).items()}
    elif hasattr(value, '__slots__'):
        return {attr: obj_to_dict(obj, getattr(value, attr)) for attr in value.__slots__}
    return value


class AbLv1:
    code: str
    time: str
    name: str
    price: float
    ratio: float
    amount: float
    volume: float

    b1: float
    b2: float
    b3: float
    b4: float
    b5: float

    b1p: float
    b2p: float
    b3p: float
    b4p: float
    b5p: float

    s1: float
    s2: float
    s3: float
    s4: float
    s5: float

    s1p: float
    s2p: float
    s3p: float
    s4p: float
    s5p: float
    field_order = ["time", "name", "price", "ratio", "amount", "volume", "b1", "b1p", "b2", "b2p", "b3", "b3p", "b4",
                   "b4p", "b5", "b5p", "s1", "s1p", "s2", "s2p", "s3", "s3p", "s4", "s4p", "s5", "s5p"]

    __slots__ = field_order + ["code"]
    float_skip_field = ["time", "name"]
    field_len = len(field_order)

    def __init__(self, row: str):
        spl = row.split("=")
        if len(spl) != 2:
            raise ValueError("symbol异常")
        symbol = spl[0]
        self.code = symbol.replace("lv1_", "")
        mspl = spl[1].split('|')
        latest = mspl[-1] if mspl else None
        fspl = latest.split(',')
        if len(fspl) != self.field_len:
            raise ValueError("数据异常")
        for index, field in enumerate(self.field_order):
            value = fspl[index]
            if field not in self.float_skip_field:
                setattr(self, field, float(value))
            else:
                setattr(self, field, value)

    def get_map(self):
        return get_map(self)


class AbLv10:
    code: str
    time: str
    name: str
    price: float
    ratio: float
    last_close: float
    volume: float
    amount: float

    b1: float
    b2: float
    b3: float
    b4: float
    b5: float
    b6: float
    b7: float
    b8: float
    b9: float
    b10: float

    b1p: float
    b2p: float
    b3p: float
    b4p: float
    b5p: float
    b6p: float
    b7p: float
    b8p: float
    b9p: float
    b10p: float

    s1: float
    s2: float
    s3: float
    s4: float
    s5: float
    s6: float
    s7: float
    s8: float
    s9: float
    s10: float

    s1p: float
    s2p: float
    s3p: float
    s4p: float
    s5p: float
    s6p: float
    s7p: float
    s8p: float
    s9p: float
    s10p: float
    field_order = [
        "time", "name", "price", "last_close", "amount", "volume",
        "b1p", "b2p", "b3p", "b4p", "b5p", "b6p", "b7p", "b8p", "b9p", "b10p", "b1", "b2", "b3", "b4", "b5", "b6", "b7",
        "b8", "b9", "b10",
        "s1p", "s2p", "s3p", "s4p", "s5p", "s6p", "s7p", "s8p", "s9p", "s10p", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
        "s8", "s9", "s10",
    ]

    __slots__ = field_order + ["code", "ratio"]
    float_skip_field = ["time", "name"]
    field_len = len(field_order)

    def __init__(self, row: str):
        spl = row.split("=")
        if len(spl) != 2:
            raise ValueError("symbol异常")
        symbol = spl[0]
        self.code = symbol.replace("lv10_", "")
        mspl = spl[1].split('|')
        latest = mspl[-1] if mspl else None
        fspl = latest.split(',')
        if len(fspl) != self.field_len:
            raise ValueError("数据异常")
        for index, field in enumerate(self.field_order):
            value = fspl[index]
            if field not in self.float_skip_field:
                setattr(self, field, float(value))
            else:
                setattr(self, field, value)
        self.ratio = round(100 * (self.price / self.last_close - 1), 2)

    def get_map(self):
        return get_map(self)


class AbLv2DealList:
    time: str
    deal_id: str
    price: float
    volume: float
    field_order = ["time", "deal_id", "price", "volume"]

    __slots__ = field_order
    float_skip_field = ["time", "deal_id"]
    field_len = len(field_order)

    def __init__(self, deal: str):
        fspl = deal.split(',')
        if len(fspl) != self.field_len:
            raise ValueError("数据异常")
        for index, field in enumerate(self.field_order):
            value = fspl[index]
            if field not in self.float_skip_field:
                setattr(self, field, float(value))
            else:
                setattr(self, field, value)
        self.volume = int(self.volume)

    def get_map(self):
        return get_map(self)


class AbLv2:
    code: str
    average_price: float
    amount: float
    volume: float
    deal_list: list[AbLv2DealList]

    __slots__ = ["code", "average_price", "amount", "volume", "deal_list"]

    def __init__(self, row: str):
        spl = row.split("=")
        if len(spl) != 2:
            raise ValueError("symbol异常")
        symbol = spl[0]
        self.code = symbol.replace("lv2_", "")
        self.deal_list = []
        ospl = spl[1].split('|')
        volume_sum = 0
        amount_sum = 0
        for deal in ospl:
            piece = AbLv2DealList(deal)
            self.deal_list.append(piece)
            volume_sum = piece.volume + volume_sum
            amount_sum = amount_sum + piece.volume * piece.price

        self.amount = round(amount_sum, 2)
        self.volume = volume_sum
        self.average_price = 0
        if volume_sum != 0:
            self.average_price = round(amount_sum / volume_sum, 3)

    def get_map(self):
        return get_map(self)


class HkLv1:
    code: str
    time: str
    name: str
    price: float
    ratio: float
    last_close: float
    volume: float
    amount: float

    b1: float
    b2: float
    b3: float
    b4: float
    b5: float
    b6: float
    b7: float
    b8: float
    b9: float
    b10: float

    b1p: float
    b2p: float
    b3p: float
    b4p: float
    b5p: float
    b6p: float
    b7p: float
    b8p: float
    b9p: float
    b10p: float

    s1: float
    s2: float
    s3: float
    s4: float
    s5: float
    s6: float
    s7: float
    s8: float
    s9: float
    s10: float

    s1p: float
    s2p: float
    s3p: float
    s4p: float
    s5p: float
    s6p: float
    s7p: float
    s8p: float
    s9p: float
    s10p: float

    field_order = [
        "time", "name_en", "name_zh", "price", "ratio", "amount", "volume",
        "b1", "b1p", "b2", "b2p", "b3", "b3p", "b4", "b4p", "b5", "b5p", "b6", "b6p", "b7", "b7p", "b8", "b8p", "b9",
        "b9p", "b10", "b10p",
        "s1", "s1p", "s2", "s2p", "s3", "s3p", "s4", "s4p", "s5", "s5p", "s6", "s6p", "s7", "s7p", "s8", "s8p", "s9",
        "s9p", "s10", "s10p",
    ]

    __slots__ = field_order + ["code"]
    float_skip_field = ["time", "name_en", "name_zh"]
    field_len = len(field_order)

    def __init__(self, row: str):
        spl = row.split("=")
        if len(spl) != 2:
            raise ValueError("symbol异常")
        symbol = spl[0]
        self.code = symbol.replace("lv1_", "")
        mspl = spl[1].split('|')
        latest = mspl[-1] if mspl else None
        fspl = latest.split(',')
        if len(fspl) != self.field_len:
            raise ValueError("数据异常")
        for index, field in enumerate(self.field_order):
            value = fspl[index]
            if field not in self.float_skip_field:
                setattr(self, field, float(value))
            else:
                setattr(self, field, value)

    def get_map(self):
        return get_map(self)


class HkLv2DealList:
    time: str
    deal_id: str
    price: float
    volume: float
    field_order = ["time", "deal_id", "price", "volume"]

    __slots__ = field_order

    def __init__(self, time: str, deal_id: str, price: float, volume: float):
        self.time = time
        self.deal_id = deal_id
        self.price = price
        self.volume = int(volume)
        if self.volume == 0 or self.price == 0:
            raise ValueError("price or vol zero")

    def get_map(self):
        return get_map(self)


class HkLv2:
    code: str
    average_price: float
    amount: float
    volume: float
    deal_list: list[HkLv2DealList]

    __slots__ = ["code", "average_price", "amount", "volume", "deal_list"]

    def __init__(self, row: str):
        spl = row.split("=")
        if len(spl) != 2:
            raise ValueError("symbol异常")
        symbol = spl[0]
        self.code = symbol.replace("lv2_", "")
        self.deal_list = []
        ospl = spl[1].split('|')
        volume_sum = 0
        amount_sum = 0
        for deal in ospl:
            dspl = deal.split(",")
            if len(dspl) < 4:
                continue
            time = dspl[0]
            deal_id = dspl[1]
            deal_list = dspl[2:]
            deal_num = len(deal_list)
            if deal_num % 2 != 0:
                continue
            for i in range(int(deal_num / 2)):
                price_index = i * 2
                vol_index = price_index + 1
                price = float(deal_list[price_index])
                vol = float(deal_list[vol_index])
                piece = HkLv2DealList(time, deal_id, price, vol)
                self.deal_list.append(piece)
                volume_sum = piece.volume + volume_sum
                amount_sum = amount_sum + piece.volume * piece.price

        self.amount = round(amount_sum, 2)
        self.volume = volume_sum
        self.average_price = 0
        if volume_sum != 0:
            self.average_price = round(amount_sum / volume_sum, 4)

    def get_map(self):
        return get_map(self)


class UsLv1:
    code: str
    time: str
    update_time: str
    name: str
    price: float
    ratio: float
    last_close: float
    volume: float
    amount: float

    field_order = ["code", "price", "ratio", "amount", "volume", "time", "update_time"]

    __slots__ = field_order
    float_skip_field = ["code", "time", "update_time"]
    field_len = len(field_order)

    def __init__(self, row: str):
        spl = row.split("=")
        if len(spl) != 2:
            raise ValueError("symbol异常")
        mspl = spl[1].split('|')
        latest = mspl[-1] if mspl else None
        fspl = latest.split(',')
        if len(fspl) != self.field_len:
            raise ValueError("数据异常")
        for index, field in enumerate(self.field_order):
            value = fspl[index]
            if field not in self.float_skip_field:
                setattr(self, field, float(value))
            else:
                setattr(self, field, value)
        self.code = self.code.lower()

    def get_map(self):
        return get_map(self)


class UsLv2DealList:
    time: str
    category: str
    deal_id: str
    price: float
    volume: float
    field_order = ["time", "category", "deal_id", "price", "volume"]

    __slots__ = field_order

    def __init__(self, time: str, category: str, deal_id: str, price: float, volume: float):
        self.time = time
        self.category = category
        self.deal_id = deal_id
        self.price = price
        self.volume = int(volume)

    def get_map(self):
        return get_map(self)


class UsLv2:
    code: str
    time: str
    category: str
    average_price: float
    amount: float
    volume: float
    deal_list: list[UsLv2DealList]

    __slots__ = ["code", "time", "category", "average_price", "amount", "volume", "deal_list"]

    def __init__(self, row: str):
        spl = row.split("=")
        if len(spl) != 2:
            raise ValueError("symbol异常")
        symbol = spl[0]
        self.code = symbol.replace("lv2_", "").lower()
        self.deal_list = []
        ospl = spl[1].split('|')
        volume_sum = 0
        amount_sum = 0
        for deal in ospl:
            dspl = deal.split(",")
            if len(dspl) < 5:
                continue
            self.time = dspl[0]
            self.category = dspl[1]
            deal_id = dspl[2]
            deal_list = dspl[3:]
            deal_num = len(deal_list)
            if deal_num % 2 != 0:
                continue
            for i in range(int(deal_num / 2)):
                price_index = i * 2
                vol_index = price_index + 1
                price = float(deal_list[price_index])
                vol = float(deal_list[vol_index])
                piece = UsLv2DealList(self.time, self.category, deal_id, price, vol)
                self.deal_list.append(piece)
                volume_sum = piece.volume + volume_sum
                amount_sum = amount_sum + piece.volume * piece.price

        self.amount = round(amount_sum, 2)
        self.volume = volume_sum
        self.average_price = 0
        if volume_sum != 0:
            self.average_price = round(amount_sum / volume_sum, 4)

    def get_map(self):
        return get_map(self)
