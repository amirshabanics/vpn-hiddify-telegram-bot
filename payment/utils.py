from payment.models import Payment, DepositTransaction, Transaction
from users.models import User
from vpn.models import VPN, Subscription
from django.conf import settings
import logging
import requests
from payment.consts import TRONSCAN_API
from django.db.models import Sum
import uuid

logger = logging.getLogger(__name__)


class TransactionInfo:
    def __init__(self, is_success, to_address, amount, confirmed):
        self.is_success = is_success
        self.to_address = to_address
        self.amount = amount
        self.confirmed = confirmed


def create_payment_for_user(user: User) -> (Payment, VPN, float):
    Payment.objects.filter(
        user=user,
        status=Payment.PaymentStatus.IN_PROGRESS
    ).update(status=Payment.PaymentStatus.FAILURE)
    subscription = Subscription.objects.get(id=settings.DEFAULT_SUBSCRIPTION_ID)
    payment = Payment.objects.create(user=user, amount=subscription.amount, amount_after_discount=subscription.amount)
    vpn = VPN.objects.create(
        user_uuid=uuid.uuid4(),
        payment=payment,
        subscription=subscription,
        active_days=subscription.package_days,
        user=user,
    )
    amount_user_pay = payment.amount_after_discount - calculate_user_wallet(user)
    if amount_user_pay > 0:
        user.chat_state = User.ChatStateChoices.GET_TRX_HASH
        user.save()
    return payment, vpn, amount_user_pay if amount_user_pay > 0 else 0


def create_vpn_for_payment(payment: Payment) -> list[VPN]:
    vpns = []
    for v in payment.vpns.all():
        payload = {
            'uuid': v.user_uuid,
            'name': f"{payment.user.user_id}@{payment.id}",
            'usage_limit_GB': str(v.subscription.usage_limit),
            'package_days': str(v.subscription.package_days),
            'mode': Subscription.SubscriptionMode[v.subscription.mode].name,
            'comment': 'vpn-bot-created',
            'enable': 'y'
        }
        hiddify = v.subscription.hiddify

        response = requests.request(
            "POST", hiddify.get_create_vpn_link(), data=payload
        )
        try:
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Create vpn failed.\nerror={e}")
            continue
        vpn_link = hiddify.get_vpn_link(v.user_uuid)
        v.link = vpn_link
        v.active_days = v.subscription.package_days
        v.save()
        vpns.append(v)
    return vpns


def get_usdt_transaction_on_trc20_info(transaction_hash: str) -> TransactionInfo:
    try:
        response = requests.get(TRONSCAN_API.format(hash=transaction_hash))
        res_json = response.json()
        # todo check test net & time
        transfer_list = res_json["transfersAllList"]
        if len(transfer_list) <= 0:
            return None
        transfer = transfer_list[0]
        token_type = transfer["tokenType"]
        symbol = transfer["symbol"]
        if not token_type == "trc20":
            logger.warning(f"Wrong token type!\nhash={transaction_hash}\ndata={res_json}")
            return None
        if not symbol == "USDT":
            logger.warning(f"Wrong symbol!\nhash={transaction_hash}\ndata={res_json}")
            return None

        to_address = transfer["to_address"]
        decimals = transfer["decimals"]
        amount = int(transfer["amount_str"]) / (10 ** decimals)

        is_success = res_json["contractRet"] == "SUCCESS"
        confirmed = res_json["confirmed"]

        return TransactionInfo(is_success, to_address, amount, confirmed)
    except:
        return None


def calculate_user_wallet(user: User):
    deposits = user.deposits.filter(
        status=DepositTransaction.DepositTransactionStatus.PAYED_AND_CONFIRMED
    ).aggregate(
        total=Sum("amount")
    )["total"]
    if deposits is None:
        deposits = 0
    transaction = Transaction.objects.filter(payment__user=user).aggregate(total=Sum("amount"))["total"]
    if transaction is None:
        transaction = 0
    return deposits - transaction


def can_transaction_be_confirmed(trx_info: TransactionInfo):
    return trx_info is not None and trx_info.is_success and settings.WALLET == trx_info.to_address
