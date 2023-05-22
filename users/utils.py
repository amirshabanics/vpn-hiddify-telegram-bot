import requests
import logging
from users.models import User, Payment, VPN
import uuid
from .consts import CREATE_VPN_URL, VPN_LINK_FORMAT
from django.conf import settings

TRONSCAN_API = "https://apilist.tronscanapi.com/api/transaction-info?hash={hash}"
logger = logging.getLogger(__name__)


class TransactionInfo:
    def __init__(self, is_success, to_address, amount, confirmed):
        self.is_success = is_success
        self.to_address = to_address
        self.amount = amount
        self.confirmed = confirmed


def get_usdt_transaction_on_trc20_info(transaction_hash: str) -> TransactionInfo:
    try:
        response = requests.get(TRONSCAN_API.format(hash=transaction_hash))
        res_json = response.json()
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
        amount = transfer["amount_str"][:-decimals]

        is_success = res_json["contractRet"] == "SUCCESS"
        confirmed = res_json["confirmed"]

        return TransactionInfo(is_success, to_address, amount, confirmed)
    except:
        return None


def create_payment_for_user(user: User) -> Payment:
    user.chat_state = User.ChatStateChoices.GET_TRX_HASH
    user.save()
    Payment.objects.filter(
        user=user,
        status=Payment.PaymentStatus.IN_PROGRESS
    ).update(status=Payment.PaymentStatus.FAILURE)
    payment = Payment.objects.create(user=user, amount=7, to_address=settings.WALLET)
    return payment


def create_vpn_for_payment(payment: Payment) -> VPN:
    vpn_id = uuid.uuid4()
    payload = {
        'uuid': vpn_id,
        'name': f"{payment.user.username}@{payment.id}",
        'usage_limit_GB': '50',
        'package_days': '90',
        'mode': 'no_reset',
        'comment': 'vpn-bot-created',
        'enable': 'y'
    }
    domain = settings.HIDDIFY_DOMAIN
    panel_id = settings.HIDDIFY_PANEL_ID
    response = requests.request(
        "POST", CREATE_VPN_URL.format(
            domain=domain,
            panel_id=panel_id,
            admin_id=settings.HIDDIFY_ADMIN_UUID
        ), data=payload
    )
    response.raise_for_status()
    vpn_link = VPN_LINK_FORMAT.format(uuid=vpn_id, domain=domain, panel_id=panel_id)
    vpn = VPN.objects.create(link=vpn_link, user=payment.user, payment=payment)
    return vpn
