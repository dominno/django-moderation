from django.dispatch import Signal

# Arguments: "instance", "status"
pre_moderation = Signal()

# Arguments: "instance", "status"
post_moderation = Signal()

# Arguments: "queryset", "status", "by", "reason"
pre_many_moderation = Signal()

# Arguments: "queryset", "status", "by", "reason"
post_many_moderation = Signal()
