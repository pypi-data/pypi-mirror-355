from abc import abstractmethod

from asynchuobi.enums import OrderType
from xync_schema.models import Order, Agent

from xync_client.Abc.Base import BaseClient


class BaseOrderClient(BaseClient):
    order: Order
    im_maker: bool
    im_seller: bool

    @abstractmethod
    @property
    def type_map(self) -> dict[OrderType, str]: ...

    def __init__(self, agent: Agent, order: Order):
        self.order = order
        self.im_maker = order.taker_id != agent.id  # or order.ad.agent_id == agent.id
        self.im_seller = order.ad.direction.sell and self.im_maker
        super().__init__(agent.ex)

    # 2: [T] Отмена запроса на сделку
    @abstractmethod
    async def cancel_request(self) -> Order: ...

    # 3: [M] Одобрить запрос на сделку
    @abstractmethod
    async def accept_request(self) -> bool: ...

    # 4: [M] Отклонить запрос на сделку
    @abstractmethod
    async def reject_request(self) -> bool: ...

    # 5: [B] Перевод сделки в состояние "оплачено", c отправкой чека
    @abstractmethod
    async def mark_payed(self, receipt): ...

    # 6: [B] Отмена сделки
    @abstractmethod
    async def cancel_order(self) -> bool: ...

    # 7: [S] Подтвердить получение оплаты
    @abstractmethod
    async def confirm(self) -> bool: ...

    # 9, 10: [S, B] Подать аппеляцию cо скриншотом / видео / файлом
    @abstractmethod
    async def start_appeal(self, file) -> bool: ...

    # 11, 12: [S, B] Встречное оспаривание полученной аппеляции cо скриншотом / видео / файлом
    @abstractmethod
    async def dispute_appeal(self, file) -> bool: ...

    # 15: [B, S] Отмена аппеляции
    @abstractmethod
    async def cancel_appeal(self) -> bool: ...

    # 16: Отправка сообщения юзеру в чат по ордеру с приложенным файлом
    @abstractmethod
    async def send_order_msg(self, msg: str, file=None) -> bool: ...

    # 17: Отправка сообщения по апелляции
    @abstractmethod
    async def send_appeal_msg(self, file, msg: str = None) -> bool: ...
