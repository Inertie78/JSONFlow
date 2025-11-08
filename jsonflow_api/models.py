"""
models.py

Modèle Pydantic pour la commande du robot JsonFlow.
Inclut la validation métier, les exemples pour la documentation et la gestion automatique du timestamp.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, List
from datetime import datetime
from fastapi import HTTPException
import zoneinfo
from .config.settings import DEFAULT_TZ, DEFAULT_TZINFO


class JsonCommand(BaseModel):
    """
    Modèle de commande pour JsonFlow.

    Attributs:
        command (Literal["move","sensor"]): type de commande
        direction (Optional[Literal["forward","backward","left","right"]]): direction du mouvement
        speed (Optional[float]): vitesse [0,1]
        duration (Optional[int]): durée du mouvement en secondes
        sensor_type (Optional[str]): type de capteur
        timestamp (str): timestamp ISO 8601 avec fuseau horaire
        tz (str): fuseau horaire
        mode (Optional[Literal["auto","manual"]]): mode de commande

    Méthodes importantes:
        validate_move(): Validation spécifique aux commandes "move"
        validate_sensor(): Validation spécifique aux commandes "sensor"
        validate_timestamp(): Vérifie le format ISO 8601 du timestamp
        add_default_timestamp(): Ajoute automatiquement un timestamp si absent
        validate_logic(): Validation globale après instanciation
        business_rules(): Retourne les règles métier pour documentation
        get_examples(): Retourne des exemples de payload pour documentation
    """
    # ------------------------
    # Définition des champs
    # ------------------------
    command: Literal["move", "sensor"]
    direction: Optional[Literal["forward", "backward", "left", "right"]] = None
    speed: Optional[float] = Field(None, ge=0, le=1)
    duration: Optional[int] = Field(None, ge=1)
    sensor_type: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    tz: str = Field(default_factory=lambda: DEFAULT_TZ, description="Fuseau horaire optionnel")
    mode: Optional[Literal["auto", "manual"]] = "manual"

    # ------------------------
    # Exemples pour documentation
    # ------------------------
    model_config = {
        "json_schema_extra": {}
    }

    def __init_subclass__(cls, **kwargs):
        """Injecte automatiquement les exemples dans le schéma JSON à la création de la classe."""
        super().__init_subclass__(**kwargs)
        cls.model_config["json_schema_extra"]["examples"] = cls.get_examples()

    # ======================
    # Validation métier spécifique
    # ======================
    def validate_move(self):
        """Valide les contraintes spécifiques aux commandes 'move'."""
        if self.direction is None or self.speed is None:
            raise HTTPException(status_code=400, detail="❌ 'direction' et 'speed' sont requis pour 'move'")
        if self.duration is not None and self.duration > 10:
            raise HTTPException(status_code=400, detail="❌ 'duration' dépasse la limite de 10s")
        if self.mode == "auto" and self.speed > 0.5:
            raise HTTPException(status_code=400, detail="❌ En mode 'auto', vitesse maximale = 0.5")

    def validate_sensor(self):
        """Valide les contraintes spécifiques aux commandes 'sensor'."""
        if self.sensor_type is None:
            raise HTTPException(status_code=400, detail="❌ 'sensor_type' est requis pour 'sensor'")

    def validate_timestamp(self):
        """Valide le format du timestamp ISO 8601 avec timezone."""
        if not self.timestamp:
            return
        try:
            dt = datetime.fromisoformat(self.timestamp)
            if dt.tzinfo is None:
                raise ValueError("Le timestamp doit avoir un fuseau horaire")
        except ValueError:
            raise HTTPException(status_code=400, detail="❌ 'timestamp' doit être ISO 8601 avec timezone")

    # ======================
    # Règles métier documentées
    # ======================
    @staticmethod
    def business_rules() -> List[str]:
        """Retourne la liste des règles métier applicables pour documentation."""
        return [
            "validate_move_speed_limit",
            "validate_move_duration",
            "validate_sensor_type"
        ]

    @staticmethod
    def get_examples() -> List[dict]:
        """Retourne des exemples de payload pour documentation."""
        return [
            {"command": "move", "direction": "forward", "speed": 0.5},
            {"command": "sensor", "sensor_type": "temperature"}
        ]

    # ======================
    # Validators Pydantic
    # ======================
    @model_validator(mode="before")
    @classmethod
    def add_default_timestamp(cls, values):
        """Ajoute un timestamp par défaut avec fuseau horaire si absent."""
        if not values.get("timestamp"):
            tz_name = values.get("tz", DEFAULT_TZ)
            try:
                tzinfo = zoneinfo.ZoneInfo(tz_name)
            except zoneinfo.ZoneInfoNotFoundError:
                tzinfo = DEFAULT_TZINFO
                values["tz"] = DEFAULT_TZ
            values["timestamp"] = datetime.now(tzinfo).replace(microsecond=0).isoformat()
        return values

    @model_validator(mode="after")
    def validate_logic(self):
        """Validation finale après instanciation du modèle."""
        if self.command == "move":
            self.validate_move()
        elif self.command == "sensor":
            self.validate_sensor()
        self.validate_timestamp()
        return self
