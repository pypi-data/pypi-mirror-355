"""Managers."""

from django.db import models
from eveuniverse.models import EveType

from allianceauth.eveonline.models import EveCharacter

from . import esi
from . import models as fleetcomp_models


class FleetSnapshotManager(models.Manager):
    """Manager for FLeetSnapshot"""

    def create_from_fleet_data(
        self, fleet_data: "esi.FleetData"
    ) -> "fleetcomp_models.FleetSnapshot":
        """Create a snapshot from the data received by the ESI"""

        snapshot: "fleetcomp_models.FleetSnapshot" = self.create(
            fleet_id=fleet_data.fleet_id,
            commander=fleet_data.fleet_commander,
        )

        for member in fleet_data.fleet_members:
            try:
                character = EveCharacter.objects.get(character_id=member.character_id)
            except EveCharacter.DoesNotExist:
                character = EveCharacter.objects.create_character(
                    character_id=member.character_id
                )
            ship_type, _ = EveType.objects.get_or_create_esi(id=member.ship_type_id)
            fleetcomp_models.FleetMember.objects.create(
                character=character, ship_type=ship_type, fleet=snapshot
            )

        return snapshot
