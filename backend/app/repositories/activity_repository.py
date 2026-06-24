"""
activity_repository.py — CarbonTracker Activity Repository (Phase I.1)
=======================================================================
CRUD operations for Activity and ActivityEntity models.

All methods accept a SQLAlchemy Session and return model instances or None.
No business logic — pure data access layer.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import Activity
from app.models.activity_entity import ActivityEntity


class ActivityRepository:
    """
    Data access layer for the `activities` and `activity_entities` tables.

    Usage:
        repo = ActivityRepository(db)
        activity = repo.create_activity(
            user_id=1,
            input_text="I travelled 25 km by train",
            category="transport",
            item="train",
            quantity=25.0,
            unit="km",
            calculated_value=0.50,
        )
    """

    def __init__(self, db: Session):
        self.db = db

    # ─── ACTIVITY: CREATE ────────────────────────────────────────────────────

    def create_activity(
        self,
        user_id: int,
        input_text: str,
        category: str,
        item: str,
        quantity: float,
        unit: str,
        calculated_value: float,
        region: str = "Global",
        metadata_json: Optional[dict] = None,
    ) -> Activity:
        """
        Create a new Activity row.

        Args:
            user_id:         FK to users.id
            input_text:      Original user text (e.g. "I travelled 25 km by train")
            category:        Emission category (e.g. "transport")
            item:            Specific item key (e.g. "train")
            quantity:        Numeric amount (e.g. 25.0)
            unit:            Unit of measure (e.g. "km")
            calculated_value: Total carbon in kgCO2e
            region:          Geographic region (default "Global")
            metadata_json:   Optional extra data dict

        Returns:
            The newly created Activity instance (with id populated).
        """
        activity = Activity(
            user_id=user_id,
            input_text=input_text,
            category=category,
            item=item,
            quantity=quantity,
            unit=unit,
            calculated_value=calculated_value,
            region=region,
            metadata_json=metadata_json,
        )
        try:
            self.db.add(activity)
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except Exception as e:
            self.db.rollback()
            raise e

    # ─── ACTIVITY ENTITY: CREATE ─────────────────────────────────────────────

    def create_entity(
        self,
        activity_id: int,
        entity_name: str,
        entity_category: Optional[str] = None,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        factor: Optional[float] = None,
        carbon_emission: Optional[float] = None,
    ) -> ActivityEntity:
        """
        Create an ActivityEntity row linked to an Activity.

        Args:
            activity_id:     FK to activities.id
            entity_name:     Display name (e.g. "Train")
            entity_category: Category (e.g. "transport")
            quantity:        Amount (e.g. 25.0)
            unit:            Unit (e.g. "km")
            factor:          Emission factor applied (e.g. 0.02)
            carbon_emission: Calculated emission in kgCO2e (e.g. 0.50)

        Returns:
            The newly created ActivityEntity instance.
        """
        entity = ActivityEntity(
            activity_id=activity_id,
            entity_name=entity_name,
            entity_category=entity_category,
            quantity=quantity,
            unit=unit,
            factor=factor,
            carbon_emission=carbon_emission,
        )
        try:
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except Exception as e:
            self.db.rollback()
            raise e

    # ─── ACTIVITY: READ ──────────────────────────────────────────────────────

    def get_by_id(self, activity_id: int) -> Optional[Activity]:
        """Return Activity by primary key, or None if not found."""
        return self.db.query(Activity).filter(Activity.id == activity_id).first()

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Activity]:
        """
        Return a paginated list of activities for a given user,
        ordered by most recent first.
        """
        return (
            self.db.query(Activity)
            .filter(Activity.user_id == user_id)
            .order_by(Activity.logged_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_entities_for_activity(self, activity_id: int) -> List[ActivityEntity]:
        """Return all ActivityEntity rows for a given activity."""
        return (
            self.db.query(ActivityEntity)
            .filter(ActivityEntity.activity_id == activity_id)
            .all()
        )

    # ─── ACTIVITY: UPDATE ────────────────────────────────────────────────────

    def update_activity(
        self,
        activity_id: int,
        category: Optional[str] = None,
        calculated_value: Optional[float] = None,
        metadata_json: Optional[dict] = None,
    ) -> Optional[Activity]:
        """
        Update mutable fields of an Activity. Only non-None args are applied.

        Returns:
            Updated Activity, or None if activity_id not found.
        """
        activity = self.get_by_id(activity_id)
        if not activity:
            return None
        if category is not None:
            activity.category = category
        if calculated_value is not None:
            activity.calculated_value = calculated_value
        if metadata_json is not None:
            activity.metadata_json = metadata_json
        try:
            self.db.commit()
            self.db.refresh(activity)
            return activity
        except Exception as e:
            self.db.rollback()
            raise e

    # ─── ACTIVITY: DELETE ────────────────────────────────────────────────────

    def delete_activity(self, activity_id: int) -> bool:
        """
        Delete an Activity by primary key.
        Cascades to ActivityEntity rows (via DB cascade).

        Returns:
            True if deleted, False if not found.
        """
        activity = self.get_by_id(activity_id)
        if not activity:
            return False
        try:
            self.db.delete(activity)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_entity(self, entity_id: int) -> bool:
        """Delete a single ActivityEntity by primary key."""
        entity = self.db.query(ActivityEntity).filter(ActivityEntity.id == entity_id).first()
        if not entity:
            return False
        try:
            self.db.delete(entity)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
