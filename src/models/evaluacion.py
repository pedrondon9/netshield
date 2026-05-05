"""Umbrales de calidad del modelo (Quality Gate).

En un IDS, el recall es crítico: un falso negativo (ataque no detectado)
es más peligroso que un falso positivo (alerta innecesaria). Por eso
se exigen umbrales altos en F1-macro y AUC-ROC, más un mínimo de recall
para la clase ataque.
"""

F1_MACRO_MINIMO = 0.85
AUC_ROC_MINIMO = 0.90
RECALL_ATAQUE_MINIMO = 0.80


def supera_umbrales(f1_macro: float, auc_roc: float, recall_ataque: float) -> bool:
    """Devuelve True si el modelo supera todos los umbrales para despliegue."""
    return (
        f1_macro >= F1_MACRO_MINIMO
        and auc_roc >= AUC_ROC_MINIMO
        and recall_ataque >= RECALL_ATAQUE_MINIMO
    )
