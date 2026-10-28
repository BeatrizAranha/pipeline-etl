"""Power BI REST API helper.

This module provides a small helper to trigger a dataset refresh via the
Power BI REST API using an Azure AD app registration (client credentials).
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import requests

try:
    import msal
except ImportError:  # pragma: no cover
    msal = None


# 🔹 Configuração básica de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _acquire_powerbi_token(
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> str:
    """Acquire an AAD token for the Power BI service scope."""

    logger.info("Iniciando aquisição de token do Power BI...")

    if msal is None:
        logger.error("Biblioteca msal não instalada")
        raise ImportError(
            "msal is required for Power BI authentication. Install with `pip install msal`."
        )

    authority = f"https://login.microsoftonline.com/{tenant_id}"

    try:
        app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret,
        )

        token = app.acquire_token_for_client(
            scopes=["https://analysis.windows.net/powerbi/api/.default"]
        )

    except Exception:
        logger.exception("Erro ao tentar adquirir token")
        raise

    access_token = token.get("access_token")

    if not access_token:
        logger.error(f"Falha ao obter token: {token}")
        raise RuntimeError(f"Failed to acquire Power BI token: {token}")

    logger.info("Token adquirido com sucesso!")
    return access_token


def refresh_powerbi_dataset(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    workspace_id: str,
    dataset_id: str,
    notify_option: str = "NoNotification",
) -> dict:
    """Trigger a refresh for a Power BI dataset."""

    logger.info("Iniciando processo de refresh do dataset...")

    access_token = _acquire_powerbi_token(tenant_id, client_id, client_secret)

    url = (
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
        f"/datasets/{dataset_id}/refreshes"
    )

    logger.info(f"Chamando endpoint: {url}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {"notifyOption": notify_option}

    try:
        resp = requests.post(url, headers=headers, json=payload)
    except Exception:
        logger.exception("Erro na chamada HTTP para Power BI")
        raise

    logger.info(f"Status HTTP: {resp.status_code}")

    try:
        resp.raise_for_status()
    except Exception:
        logger.error(f"Erro na resposta: {resp.text}")
        raise

    logger.info("Refresh solicitado com sucesso no Power BI!")

    try:
        return resp.json()
    except Exception:
        logger.warning("Resposta não contém JSON")
        return {}


def refresh_powerbi_dataset_from_env() -> Optional[dict]:
    """Trigger refresh using credentials from environment variables."""

    logger.info("Executando refresh a partir das variáveis de ambiente...")

    env = os.environ
    required = [
        "POWERBI_TENANT_ID",
        "POWERBI_CLIENT_ID",
        "POWERBI_CLIENT_SECRET",
        "POWERBI_WORKSPACE_ID",
        "POWERBI_DATASET_ID",
    ]

    missing = [k for k in required if not env.get(k)]

    if missing:
        logger.warning(f"Variáveis de ambiente faltando: {missing}")
        return None

    try:
        result = refresh_powerbi_dataset(
            tenant_id=env["POWERBI_TENANT_ID"],
            client_id=env["POWERBI_CLIENT_ID"],
            client_secret=env["POWERBI_CLIENT_SECRET"],
            workspace_id=env["POWERBI_WORKSPACE_ID"],
            dataset_id=env["POWERBI_DATASET_ID"],
        )

        logger.info("Processo finalizado com sucesso!")
        return result

    except Exception:
        logger.exception("Erro geral ao executar refresh via ENV")
        raise


# 🔥 opcional: executa direto (ótimo pra teste local / pipeline)
# if __name__ == "__main__":
#     refresh_powerbi_dataset_from_env()
