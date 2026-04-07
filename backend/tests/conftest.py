"""
Configurazione comune per tutti i test backend V2.

Imposta variabili d'ambiente a valori noti e sicuri PRIMA che qualsiasi
modulo applicativo venga importato.

Questo garantisce che:
- Settings() non dipenda dal file .env locale per i test
- Il database URL usato nei test sia prevedibile e sovrascrivibile
- get_settings() restituisca valori coerenti anche in assenza di .env

Per test che richiedono un DB reale, sovrascrivere DATABASE_URL tramite
fixture locali o variabile d'ambiente CI.
"""

import os

# Imposta PRIMA dell'import di qualsiasi modulo nssp_v2
# I valori defaults di Settings sono già sicuri, ma questo assicura
# che un .env locale non interferisca durante i test.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-not-for-production")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")

# DATABASE_URL: usa un DB test separato se presente, altrimenti il default.
# I test unit e sync usano SQLite in-memory: non dipendono da questo valore.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/nssp_v2_test",
)
