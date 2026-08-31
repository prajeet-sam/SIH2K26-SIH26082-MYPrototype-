from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    AlertContext,
    AlertItemResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    DataQualityIncidentResponse,
)
from ml.config.settings import get_settings
from ml.storage.models import Alert, AlertRule, DataQualityLog, Station

router = APIRouter(prefix="/api", tags=["alerts"])

STATION_NAME_MAP: dict[str, str] | None = None


def require_admin(authorization: str | None = Header(default=None)) -> None:
    token = get_settings().admin_token
    if not token:
        raise HTTPException(
            status_code=501,
            detail="Admin token not configured (set AIRACAST_ADMIN_TOKEN). Alert rules API disabled.",
        )
    expected = f"Bearer {token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")


def _station_names(db: Session) -> dict[str, str]:
    global STATION_NAME_MAP
    if STATION_NAME_MAP is None:
        STATION_NAME_MAP = {s.canonical_slug: s.name for s in db.query(Station).all()}
    return STATION_NAME_MAP


@router.get("/alerts", response_model=list[AlertItemResponse])
def get_alerts(db: Session = Depends(get_db)):
    names = _station_names(db)
    rows = db.query(Alert).order_by(desc(Alert.triggered_at)).limit(200).all()
    result: list[AlertItemResponse] = []
    for r in rows:
        result.append(
            AlertItemResponse(
                id=str(r.id),
                alert_type=r.alert_type,
                severity=r.severity,
                station_slug=r.station_slug,
                station_name=names.get(r.station_slug) if r.station_slug else None,
                triggered_at=r.triggered_at.isoformat() if r.triggered_at else "",
                observed_or_forecast=r.observed_or_forecast,
                message=r.message,
                context=AlertContext(),
                resolved_at=r.resolved_at.isoformat() if r.resolved_at else None,
            )
        )
    return result


@router.get("/data-quality/status", response_model=list[DataQualityIncidentResponse])
def data_quality_incidents(db: Session = Depends(get_db)):
    rows = db.query(DataQualityLog).order_by(desc(DataQualityLog.detected_at)).limit(200).all()
    return [
        DataQualityIncidentResponse(
            id=str(r.id),
            station_slug=r.station_slug,
            check_type=r.check_type,
            severity=r.severity,
            detected_at=r.detected_at.isoformat(),
            resolved_at=r.resolved_at.isoformat() if r.resolved_at else None,
            detail=r.detail or "",
        )
        for r in rows
    ]


def _rule_response(r: AlertRule) -> AlertRuleResponse:
    return AlertRuleResponse(
        id=str(r.id),
        name=r.name,
        metric=r.metric,
        comparator=r.comparator,
        threshold=r.threshold,
        window_hours=r.window_hours,
        horizon_filter=r.horizon_filter,
        enabled=r.enabled,
        cooldown_minutes=r.cooldown_minutes,
    )


@router.get("/alerts/rules", response_model=list[AlertRuleResponse])
def list_rules(db: Session = Depends(get_db)):
    return [_rule_response(r) for r in db.query(AlertRule).order_by(AlertRule.name).all()]


@router.post("/alerts/rules", response_model=AlertRuleResponse, status_code=201)
def create_rule(
    payload: AlertRuleCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    rule = AlertRule(
        name=payload.name,
        metric=payload.metric,
        comparator=payload.comparator,
        threshold=payload.threshold,
        window_hours=payload.window_hours,
        horizon_filter=payload.horizon_filter,
        enabled=payload.enabled,
        cooldown_minutes=payload.cooldown_minutes,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _rule_response(rule)


@router.put("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
def update_rule(
    rule_id: int,
    payload: AlertRuleUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field in (
        "name",
        "metric",
        "comparator",
        "threshold",
        "window_hours",
        "horizon_filter",
        "enabled",
        "cooldown_minutes",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return _rule_response(rule)
