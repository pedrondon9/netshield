"""Schemas de entrada y salida de la API de detección de intrusiones."""

from pydantic import BaseModel, Field


class FlowInput(BaseModel):
    """Flujo de red a clasificar (14 features del dataset CICIDS2017)."""
    Flow_Duration: float = Field(..., ge=0, description="Duración del flujo (μs)")
    Total_Fwd_Packets: int = Field(..., ge=0, description="Paquetes forward")
    Total_Backward_Packets: int = Field(..., ge=0, description="Paquetes backward")
    Flow_Bytes_per_s: float = Field(..., ge=0, description="Bytes/segundo")
    Flow_Packets_per_s: float = Field(..., ge=0, description="Paquetes/segundo")
    Fwd_Packet_Length_Mean: float = Field(..., ge=0, description="Media longitud pkt fwd")
    Bwd_Packet_Length_Mean: float = Field(..., ge=0, description="Media longitud pkt bwd")
    Flow_IAT_Mean: float = Field(..., ge=0, description="Media inter-arrival time")
    Fwd_IAT_Mean: float = Field(..., ge=0, description="Media IAT forward")
    Bwd_IAT_Mean: float = Field(..., ge=0, description="Media IAT backward")
    SYN_Flag_Count: int = Field(..., ge=0, description="Flags SYN")
    ACK_Flag_Count: int = Field(..., ge=0, description="Flags ACK")
    Init_Win_bytes_forward: int = Field(..., ge=0, description="Ventana TCP inicial fwd")
    Init_Win_bytes_backward: int = Field(..., ge=0, description="Ventana TCP inicial bwd")

    model_config = {
        "json_schema_extra": {
            "example": {
                "Flow_Duration": 120000,
                "Total_Fwd_Packets": 12,
                "Total_Backward_Packets": 8,
                "Flow_Bytes_per_s": 45000.5,
                "Flow_Packets_per_s": 150.3,
                "Fwd_Packet_Length_Mean": 234.5,
                "Bwd_Packet_Length_Mean": 180.2,
                "Flow_IAT_Mean": 8500.0,
                "Fwd_IAT_Mean": 12000.0,
                "Bwd_IAT_Mean": 9500.0,
                "SYN_Flag_Count": 1,
                "ACK_Flag_Count": 10,
                "Init_Win_bytes_forward": 8192,
                "Init_Win_bytes_backward": 502,
            }
        }
    }


class DetectionOutput(BaseModel):
    """Resultado de la clasificación de un flujo de red."""
    es_ataque: bool = Field(..., description="True si es tráfico malicioso")
    probabilidad_ataque: float = Field(..., description="Probabilidad de ataque (0-1)")
    nivel_amenaza: str = Field(..., description="CRITICO | ALTO | MEDIO | BAJO")
    modelo_version: str = Field(..., description="Versión del modelo IDS")
    latencia_ms: float = Field(..., description="Tiempo de inferencia en ms")
