from django.conf import settings
from django.core.checks import Error as CheckError, register


@register(deploy=True)
def smart_proxy_rhsm_url_check(app_configs, **kwargs):
    messages = []
    if getattr(settings, "SMART_PROXY_RHSM_URL", "UNREACHABLE") == "UNREACHABLE":
        messages.append(
            CheckError(
                "SMART_PROXY_RHSM_URL is a required setting but it was not configured.",
                id="pulp_smart_proxy.E001",
            )
        )
    return messages
