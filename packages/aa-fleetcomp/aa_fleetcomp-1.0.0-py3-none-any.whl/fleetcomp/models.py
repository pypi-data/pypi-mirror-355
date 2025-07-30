"""Models."""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import ClassVar

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, QuerySet
from django.db.models.aggregates import Count
from django.utils.translation import gettext_lazy as _
from esi.models import Token
from eveuniverse.models import EveGroup, EveType

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter

from . import ESI_SCOPES
from .managers import FleetSnapshotManager


class Constants(IntEnum):
    """Constant values used in queries"""

    LOGISTICS_GROUP = 832
    FORCE_RECON_GROUP = 833
    COMMAND_SHIPS_GROUP = 540
    HEAVY_INTERDICTION_GROUP = 894
    DREADNOUGHT_GROUP = 485
    FORCE_AUXILIARY_GROUP = 1538


class General(models.Model):
    """A metamodel for app permissions."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can create snapshots and see own snapshots"),
            (
                "view_all",
                "Can view all recorded fleets and snapshot other people fleets",
            ),
        )


class CustomGrouping(models.Model):
    """Custom ship grouping"""

    display_name = models.CharField(
        max_length=50, help_text="Name of the grouping in the UI"
    )

    associated_types = models.ManyToManyField(
        EveType, help_text="Ship types associated to this grouping", blank=True
    )
    associated_groups = models.ManyToManyField(
        EveGroup, help_text="Eve ship groups associated to this grouping", blank=True
    )

    def __str__(self):
        return f"Custom group {self.display_name}"

    def get_snapshot_matches(
        self, snapshot: "FleetSnapshot"
    ) -> QuerySet["FleetMember"]:
        """Return all members matching the grouping"""
        return snapshot.members.filter(
            Q(ship_type__in=self.associated_types.all())
            | Q(ship_type__eve_group__in=self.associated_groups.all())
        )


class FleetCommander(models.Model):
    """
    Member of a fleet with ESI stored
    """

    character_ownership = models.ForeignKey(
        CharacterOwnership,
        on_delete=models.CASCADE,
        related_name="+",
    )

    @property
    def character_id(self) -> int:
        """Return character id"""
        return self.character_ownership.character.character_id

    @property
    def character_name(self) -> str:
        """Return character name"""
        return self.character_ownership.character.character_name

    @property
    def user(self) -> User:
        """Return the associated user"""
        return self.character_ownership.user

    def fetch_token(self) -> Token:
        """Return a valid token if there is one"""
        token = (
            Token.objects.filter(
                character_id=self.character_id,
            )
            .require_scopes(ESI_SCOPES)
            .require_valid()
            .first()
        )

        if not token:
            raise Token.DoesNotExist(f"{self}: No valid token found")
        return token

    def __str__(self):
        return self.character_name


class FleetSnapshot(models.Model):
    """Takes a snapshot of a fleet at a given time"""

    objects: ClassVar[FleetSnapshotManager] = FleetSnapshotManager()

    fleet_id = models.BigIntegerField(help_text=_("EVE online fleet id"))
    timestamp = models.DateTimeField(
        auto_now_add=True, help_text=_("Time of the snapshot")
    )

    commander = models.ForeignKey(
        FleetCommander,
        on_delete=models.SET_NULL,
        null=True,
        help_text=_("Fleet commander at the time of the snapshot"),
    )

    @property
    def timestamp_str(self) -> str:
        """Timestamp displayed with leading zeroes"""
        return self.timestamp.strftime("%Y/%m/%d %H-%M")

    class Meta:
        ordering = ["-timestamp"]

    # pylint: disable=too-many-instance-attributes
    @dataclass
    class MemberReport:
        """Report to be displayed in templates"""

        main_character: EveCharacter | None
        user: User
        character_count: int
        main_line: int = 0
        logistics: int = 0
        hics: int = 0
        command_ships: int = 0
        cynoes: int = 0
        dreads: int = 0
        faxes: int = 0
        customs: dict[int, int] = field(default_factory=dict)

        @property
        def others(self):
            """Count characters that don't fit in any category"""
            return self.character_count - (
                self.main_line
                + self.logistics
                + self.hics
                + self.command_ships
                + self.cynoes
                + self.dreads
                + self.faxes
                + sum(self.customs.values())
            )

    def __str__(self):
        return f"Fleet {self.fleet_id} at {self.timestamp}"

    def count_mains(self) -> int:
        """Counts how many main characters are in the fleet"""
        return (
            self.members.exclude(character__character_ownership=None)
            .values("character__character_ownership__user")
            .distinct()
            .count()
        )

    def count_orphans(self) -> int:
        """Count how many characters in the fleet don't have a main associated"""
        return self.members.filter(character__character_ownership=None).count()

    def count_members(self) -> int:
        """Counts how many characters are in the fleet"""
        return self.members.count()

    def get_user_members(self, user: User | None) -> QuerySet["FleetMember"]:
        """
        Returns characters in fleets linked to this user.
        If None is passed returns all orphans
        """
        if user:
            user_members = self.members.filter(
                character__character_ownership__user=user
            )
        else:
            user_members = self.members.filter(character__character_ownership=None)
        return user_members

    def get_main_ship_type(self) -> EveType:
        """Return the most popular ship type of this fleet"""
        type_id = (
            self.members.values("ship_type")
            .annotate(Count("id"))
            .order_by("-id__count")
            .first()["ship_type"]
        )
        return EveType.objects.get(id=type_id)

    def count_ship_type(self, ship_type: EveType) -> int:
        """Returns how many of a certain ship there is in the fleet"""
        return self.members.filter(ship_type=ship_type).count()

    def count_ship_group_id(self, group_id: int) -> int:
        """Returns how many ships of this specific group are in the fleet"""
        return self.members.filter(ship_type__eve_group__id=group_id).count()

    def count_logistics(self) -> int:
        """Return the number of logistic cruisers in the fleet"""
        return self.count_ship_group_id(Constants.LOGISTICS_GROUP)

    def count_hics(self) -> int:
        """Count HICS in the fleet"""
        return self.count_ship_group_id(Constants.HEAVY_INTERDICTION_GROUP)

    def count_command_ships(self) -> int:
        """Count CSs in the fleet"""
        return self.count_ship_group_id(Constants.COMMAND_SHIPS_GROUP)

    def count_cynoes(self) -> int:
        """Count force recons in the fleet"""
        return self.count_ship_group_id(Constants.FORCE_RECON_GROUP)

    def count_dreads(self) -> int:
        """Count dreadnoughts in the fleet"""
        return self.count_ship_group_id(Constants.DREADNOUGHT_GROUP)

    def count_faxes(self) -> int:
        """Count FAXes in the fleet"""
        return self.count_ship_group_id(Constants.FORCE_AUXILIARY_GROUP)

    def generate_report(self) -> list[MemberReport]:
        """Generates a snapshot report to be displayed"""

        reports = []
        users = []
        for user_id in self.members.values_list(
            "character__character_ownership__user", flat=True
        ).distinct():
            if user_id:
                users.append(User.objects.get(id=user_id))
            else:
                users.append(None)

        main_ship_type = self.get_main_ship_type()

        for user in users:
            user_members = self.get_user_members(user)
            report = self.MemberReport(
                main_character=user.profile.main_character if user else None,
                user=user,
                character_count=user_members.count(),
            )
            report.main_line = user_members.filter(ship_type=main_ship_type).count()
            report.logistics = user_members.filter(
                ship_type__eve_group__id=Constants.LOGISTICS_GROUP
            ).count()
            report.hics = user_members.filter(
                ship_type__eve_group__id=Constants.HEAVY_INTERDICTION_GROUP
            ).count()
            report.command_ships = user_members.filter(
                ship_type__eve_group__id=Constants.COMMAND_SHIPS_GROUP
            ).count()
            report.cynoes = user_members.filter(
                ship_type__eve_group__id=Constants.FORCE_RECON_GROUP
            ).count()
            report.dreads = user_members.filter(
                ship_type__eve_group__id=Constants.DREADNOUGHT_GROUP
            ).count()
            report.faxes = user_members.filter(
                ship_type__eve_group__id=Constants.FORCE_AUXILIARY_GROUP
            ).count()

            for custom_grouping in CustomGrouping.objects.all():
                report.customs[custom_grouping.id] = (
                    custom_grouping.get_snapshot_matches(self) & user_members
                ).count()

            reports.append(report)

        return reports


class FleetMember(models.Model):
    """Member of a fleet and its associated ships"""

    fleet = models.ForeignKey(
        FleetSnapshot, on_delete=models.CASCADE, related_name="members"
    )
    character = models.ForeignKey(EveCharacter, on_delete=models.CASCADE)
    ship_type = models.ForeignKey(EveType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.character} - {self.ship_type}"
