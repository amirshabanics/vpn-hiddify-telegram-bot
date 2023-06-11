from django.contrib import admin
from vpn.models import VPN, Subscription, HiddifyPanel


@admin.register(VPN)
class VPNAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "link", "left_days"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["id", "hiddify", "mode", "usage_limit", "package_days"]


@admin.register(HiddifyPanel)
class HiddifyPanelAdmin(admin.ModelAdmin):
    list_display = ["id", "domain", "panel_id", "admin_id"]
