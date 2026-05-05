"""Tests del módulo de evaluación (quality gate)."""

from src.models.evaluacion import supera_umbrales


def test_supera_umbrales_modelo_bueno():
    assert supera_umbrales(f1_macro=0.95, auc_roc=0.98, recall_ataque=0.92) is True


def test_falla_f1_bajo():
    assert supera_umbrales(f1_macro=0.80, auc_roc=0.95, recall_ataque=0.90) is False


def test_falla_auc_bajo():
    assert supera_umbrales(f1_macro=0.90, auc_roc=0.85, recall_ataque=0.90) is False


def test_falla_recall_bajo():
    assert supera_umbrales(f1_macro=0.90, auc_roc=0.95, recall_ataque=0.70) is False


def test_exacto_en_limite():
    assert supera_umbrales(f1_macro=0.85, auc_roc=0.90, recall_ataque=0.80) is True


def test_modelo_malo():
    assert supera_umbrales(f1_macro=0.50, auc_roc=0.60, recall_ataque=0.40) is False


def test_un_umbral_falla_es_suficiente():
    # F1 y AUC buenos, pero recall bajo → no desplegamos
    assert supera_umbrales(f1_macro=0.95, auc_roc=0.99, recall_ataque=0.75) is False
