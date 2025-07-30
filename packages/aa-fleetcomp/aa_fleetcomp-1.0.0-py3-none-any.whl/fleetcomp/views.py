"""Views."""

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from esi.decorators import token_required

from allianceauth.authentication.models import CharacterOwnership

from fleetcomp import ESI_SCOPES
from fleetcomp.esi import CharacterNotInFleet, NoAccessToFleet, get_fleet_data
from fleetcomp.models import CustomGrouping, FleetCommander, FleetSnapshot


@permission_required("fleetcomp.basic_access")
def index(request):
    """Render index view."""
    snapshots = FleetSnapshot.objects.all()
    if not request.user.has_perm("fleetcomp.view_all"):
        snapshots.filter(commander__character_ownership__user=request.user)
    return render(request, "fleetcomp/index.html", {"snapshots": snapshots})


@permission_required("fleetcomp.basic_access")
@token_required(scopes=ESI_SCOPES)
def capture_own_fleet_composition(request, token):
    """
    Adds a new fleet commander to the list of fleet commanders this user can pull data from.
    """

    character_ownership: CharacterOwnership = get_object_or_404(
        request.user.character_ownerships.select_related("character"),
        character__character_id=token.character_id,
    )

    fleet_commander, created = FleetCommander.objects.get_or_create(
        character_ownership=character_ownership,
    )

    if created:
        character_name = character_ownership.character.character_name
        messages.success(
            request, _(f"Successfully added new fleet commander: {character_name}")
        )

    return __capture_fleet_and_redirect(request, fleet_commander)


@permission_required("fleetcomp.view_all")
def capture_other_fleet_composition(request):
    """
    Enables to capture the fleet composition of another FC that registered
    """

    if request.method == "POST":

        commander_id = request.POST.get("commander_id")
        commander = get_object_or_404(FleetCommander, id=commander_id)

        return __capture_fleet_and_redirect(request, commander)

    commanders = FleetCommander.objects.all()
    return render(
        request, "fleetcomp/all_fleet_commanders.html", {"commanders": commanders}
    )


def __capture_fleet_and_redirect(request, fleet_commander: FleetCommander):
    """
    Captures the fleet under this commander and returns a redirect to the snapshot if successful
    """

    try:
        fleet_data = get_fleet_data(fleet_commander)
    except CharacterNotInFleet:
        messages.error(request, _("The character doesn't appear to be in a fleet"))
        return redirect("fleetcomp:index")
    except NoAccessToFleet:
        messages.error(
            request, _("The character doesn't appear to be a fleet commander")
        )
        return redirect("fleetcomp:index")

    snapshot = FleetSnapshot.objects.create_from_fleet_data(fleet_data)

    return redirect("fleetcomp:view_snapshot", snapshot.id)


@permission_required("fleetcomp.basic_access")
def view_fleet(request, snapshot_id):
    """Displays the selected snapshot"""

    snapshot = get_object_or_404(FleetSnapshot, id=snapshot_id)

    if snapshot.commander.user != request.user and not request.user.has_perm(
        "fleetcomp.view_all"
    ):
        messages.warning(
            request, _("You don't have the necessary roles to see this fleet")
        )
        return redirect("fleetcomp:index")

    main_ship_type = snapshot.get_main_ship_type()
    main_ship_type_count = snapshot.count_ship_type(main_ship_type)
    custom_groupings = CustomGrouping.objects.all()

    return render(
        request,
        "fleetcomp/snapshot.html",
        {
            "snapshot": snapshot,
            "main_ship_type": main_ship_type,
            "main_ship_type_count": main_ship_type_count,
            "custom_groupings": custom_groupings,
        },
    )


@permission_required("fleetcomp.basic_access")
def user_details(request, snapshot_id: int, user_id: int | None = None):
    """Displays the details of a user"""

    snapshot = get_object_or_404(FleetSnapshot, id=snapshot_id)
    user = get_object_or_404(User, id=user_id) if user_id else None

    members = snapshot.get_user_members(user)

    context = {
        "user": user,
        "members": members,
    }

    return render(request, "fleetcomp/modals/user_details.html", context)


@cache_page(3600)
def modal_loader_body(request):
    """Draw the loader body. Useful for showing a spinner while loading a modal."""
    return render(request, "fleetcomp/modals/loader_body.html")
