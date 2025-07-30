"""Fleetcomp templatetags"""

from django import template
from django.contrib.auth.models import User

from fleetcomp.models import CustomGrouping, FleetSnapshot

register = template.Library()


@register.simple_tag
def custom_grouping_counter_snapshot(
    snapshot: FleetSnapshot, custom_grouping: CustomGrouping
) -> int:
    """Returns how many ships of the given custom grouping are in the snapshot"""
    return custom_grouping.get_snapshot_matches(snapshot).count()


@register.simple_tag
def custom_grouping_counter_user(
    snapshot: FleetSnapshot, user: User, custom_grouping: CustomGrouping
) -> int:
    """Returns how many ships of the given user match the custom grouping"""
    return (
        custom_grouping.get_snapshot_matches(snapshot) & snapshot.get_user_members(user)
    ).count()
