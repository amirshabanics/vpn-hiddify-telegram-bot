import requests
import logging
from users.models import User
from payment.models import Payment
from vpn.models import Subscription, VPN
import uuid

from django.conf import settings

logger = logging.getLogger(__name__)


