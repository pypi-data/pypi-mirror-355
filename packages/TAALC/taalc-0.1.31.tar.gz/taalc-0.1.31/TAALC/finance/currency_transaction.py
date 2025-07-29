# from __future__ import annotations
# from typing import Optional, TYPE_CHECKING
from epure import epure
from .currency import Currency
from ..tg_environment.t_member import TMember
from ..tg_environment.t_user import TUser
# if TYPE_CHECKING:
from .taalc_transaction import TaalcTransaction
from datetime import datetime
from .transaction_batch import TransactionBatch

@epure()
class CurrencyTransaction(TaalcTransaction):

    currency: Currency
    amount: float


    def __init__(self, sent_from: TUser, sent_to: TUser,\
                  currency: Currency, amount: float, batch: TransactionBatch=None):

        self.sent_from = sent_from
        self.sent_to = sent_to
        self.currency = currency
        self.amount = amount
        self.transaction_time = datetime.now()

        if batch:
            self.transaction_batch = batch