from __future__ import annotations
from typing import TYPE_CHECKING
# from ..finance.taalc_nft import TaalcNft
# from ..finance.taalc_nft_token import TaalcNftToken

from .t_user import TUser
from .t_chat import TChat
from .. import bidding
from .. import finance
if TYPE_CHECKING:
    from ..bidding.message_offer import MessageOffer
    from ..finance.message_nft_token import MessageNftToken
from epure import epure
from aiogram import types
from .telegram_entity import TelegramEntity


@epure()
class TMessage(TelegramEntity):
    # owner: TUser
    creator: TUser
    # if TYPE_CHECKING:
    taalc_offer: 'bidding.message_offer.MessageOffer'
    message_nft_token: 'finance.message_nft_token.MessageNftToken'
    taalc_chat: TChat
    tg_chat_id: int
    text: str

    @property
    def owner(self):
        if not self.message_nft_token:
           return self.creator
        from ..finance.message_transaction import MessageTransaction
        transactions = MessageTransaction.resource.read(taalc_nft_token = self.message_nft_token)
        if not transactions:
            return self.creator
        transactions = sorted(transactions, key=lambda tr: tr.transaction_time)
        last_tr = transactions[-1]
        return last_tr.sent_to
        

    def __init__(self, message: types.Message=None):
        
        if not message:
            return
        self.taalc_offer = None
        self.message_nft_token = None
        self.creator = TUser.user_by_tg_user(message.from_user)
        # self.owner = TUser.user_by_tg_user(message.from_user)
        self.tg_chat_id=message.chat.id
        self.telegram_id=message.message_id
        self.text = message.text

        taalc_chat = TChat.resource.read(telegram_id=self.tg_chat_id)
        if taalc_chat:
            taalc_chat = taalc_chat[0]
        else:
            taalc_chat = TChat()
            taalc_chat.telegram_id = message.chat.id
            taalc_chat.shifted_id = message.chat.shifted_id
        self.taalc_chat = taalc_chat

    @classmethod
    def get_t_message(cls, message: types.Message) -> TMessage:
        res = cls.resource.read(tg_chat_id=message.chat.id, \
                                telegram_id=message.message_id)
        if not res:
            res = cls(message)
            res.save()
        else:
            res = res[0]
        
        return res
    
    def get_url(self):
        res = f"https://t.me/c/{self.taalc_chat.shifted_id}/{self.telegram_id}"
        return res
    

        