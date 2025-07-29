from datetime import datetime
from enum import IntEnum
from typing import Literal

from pydantic import BaseModel


class OrderRequest(BaseModel):
    class Side(IntEnum):
        BUY = 0
        SALE = 1

    itemId: str
    tokenId: str
    currencyId: str
    side: Literal["0", "1"]  # 0 покупка, # 1 продажа
    curPrice: str
    quantity: str
    amount: str
    flag: Literal["amount", "quantity"]
    version: str = "1.0"
    securityRiskToken: str = ""


class PreOrderResp(BaseModel):
    price: str  # float
    curPrice: str
    totalAmount: float
    minAmount: float
    maxAmount: float
    minQuantity: float
    maxQuantity: float
    payments: list[str]  # list[int]
    status: Literal[10]
    paymentTerms: list
    paymentPeriod: Literal[15]
    lastQuantity: float
    lastPrice: float
    isOnline: bool
    lastLogoutTime: datetime
    itemPriceAvailableTime: datetime
    itemPriceValidTime: int  # 45000
    itemType: Literal["ORIGIN"]


class OrderResp(BaseModel):
    orderId: str
    isNeedConfirm: bool
    success: bool
    isBulkOrder: bool
    confirmed: str = None
    delayTime: str


class CancelOrderReq(BaseModel):
    orderId: str
    cancelCode: Literal["cancelReason_transferFailed"] = "cancelReason_transferFailed"
    cancelRemark: str = ""
    voucherPictures: str = ""


class JudgeInfo(BaseModel):
    autoJudgeUnlockTime: str
    dissentResult: str
    preDissent: str
    postDissent: str


class Extension(BaseModel):
    isDelayWithdraw: bool
    delayTime: str
    startTime: str


class OrderItem(BaseModel):
    id: str
    side: Literal[0, 1]  # int: 0 покупка, 1 продажа
    tokenId: str
    orderType: Literal[
        "ORIGIN", "SMALL_COIN", "WEB3"
    ]  # str: ORIGIN: normal p2p order, SMALL_COIN: HotSwap p2p order, WEB3: web3 p2p order
    amount: str
    currencyId: str
    price: str
    notifyTokenQuantity: str
    notifyTokenId: str
    fee: str
    targetNickName: str
    targetUserId: str
    status: int
    selfUnreadMsgCount: str
    createDate: str
    transferLastSeconds: str
    appealLastSeconds: str
    userId: str
    sellerRealName: str
    buyerRealName: str
    judgeInfo: JudgeInfo
    unreadMsgCount: str
    extension: Extension
    bulkOrderFlag: bool


class PayTerm(BaseModel):
    id: str
    realName: str
    paymentType: int
    bankName: str
    branchName: str
    accountNo: str


class OrderFull(BaseModel):
    itemId: str
    paymentTermResult: PayTerm
    confirmedPayTerm: PayTerm


class Message(BaseModel):
    id: str
    accountId: str
    message: str
    msgType: Literal[
        0, 1, 2, 5, 6, 7, 8
    ]  # int: 0: system message, 1: text (user), 2: image (user), 5: text (admin), 6: image (admin), 7: pdf (user), 8: video (user)
    msgCode: int
    createDate: str
    isRead: Literal[0, 1]  # int: 1: read, 0: unread
    contentType: Literal["text", "pic", "pdf", "video"]
    roleType: str
    userId: str
    orderId: str
    msgUuid: str
    nickName: str
    read: str
    fileName: str
    onlyForCustomer: int
