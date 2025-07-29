from .transaction_batch import TransactionBatch
from ..tg_environment.t_user import TUser
from datetime import datetime


class TaalcTransaction():
    transaction_batch: TransactionBatch
    sent_from: TUser
    sent_to: TUser
    transaction_time: datetime