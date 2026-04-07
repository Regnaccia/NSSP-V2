from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/nssp_v2"
    database_url_test: str = "postgresql://postgres:postgres@localhost:5432/nssp_v2_test"
    app_env: str = "development"
    debug: bool = False
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 ore

    # Connessione a EasyJob — richiesta per sync on demand reale
    # Formato: DRIVER={SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=...
    easy_connection_string: str | None = None

    # Soglia di staleness per la freshness policy (DL-ARCH-V2-008 §5)
    sync_staleness_threshold_minutes: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Restituisce l'istanza singleton di Settings.

    L'uso di lru_cache garantisce che Settings() sia istanziato una volta sola
    e che in test sia possibile sovrascrivere i valori tramite variabili d'ambiente
    e resettare la cache con get_settings.cache_clear().
    """
    return Settings()


# Alias backward-compatible per import diretti: `from ... import settings`
settings = get_settings()
