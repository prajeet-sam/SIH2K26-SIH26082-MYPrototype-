from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas import GlobalImportanceItem, ModelMetricRowResponse
from ml.config.settings import get_settings
from ml.forecasting.explain import global_importance
from ml.forecasting.train import list_model_metrics
from ml.storage.db import make_engine, make_session_factory

router = APIRouter(prefix="/api/model", tags=["models"])


@router.get("/performance", response_model=list[ModelMetricRowResponse])
def model_performance(target: str = Query("pm25", alias="target")):
    settings = get_settings()
    engine = make_engine(settings)
    factory = make_session_factory(engine)
    with factory() as db:
        rows = list_model_metrics(db, target)
    # Persistence baseline provides a reference "skill vs persistence" of 0.
    return [
        ModelMetricRowResponse(
            model_name=r["model_name"],
            target=r["target"],
            horizon_hours=r["horizon_hours"],
            mae=r["mae"],
            rmse=r["rmse"],
            mape=r["mape"],
            r2=r["r2"],
            skill_vs_persistence=0.0,
            model_run_id=r["model_run_id"],
        )
        for r in rows
    ]


@router.get("/explanations/global-importance", response_model=list[GlobalImportanceItem])
def global_importances(target: str = Query("pm25", alias="target")):
    settings = get_settings()
    engine = make_engine(settings)
    factory = make_session_factory(engine)
    with factory() as db:
        rows = global_importance(db, target)
    return [
        GlobalImportanceItem(
            feature_label=r["feature_label"],
            importance_pct=r["importance_pct"],
            family=r["family"],
        )
        for r in rows
    ]
