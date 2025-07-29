import asyncio
import json
import logging
import uuid
from datetime import datetime
from threading import Thread
from typing import Optional

import nats
from litewave_audit_lib.base import BaseAuditLogger

logger = logging.getLogger(__name__)


class NATSAuditLogger(BaseAuditLogger):
    def __init__(
        self,
        subject: str,
        nats_connection_url: str = "nats://localhost:4222",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.subject = subject
        # embed creds into URL if given
        if username and password and "@" not in nats_connection_url:
            scheme, addr = nats_connection_url.split("://", 1)
            self.nats_url = f"{scheme}://{username}:{password}@{addr}"
        else:
            self.nats_url = nats_connection_url

    def log(
        self,
        who: Optional[str],
        resource: str,
        action: str,
        timestamp: Optional[datetime] = None,
        location: Optional[str] = "cloud",
        request_context: Optional[dict] = None,
        context: Optional[dict] = None,
        client: Optional[dict] = None,
    ):
        """
        :param timestamp: if None, uses UTC now
        :param location: e.g. "cloud"
        :param request_context: your dict
        :param context: your dict
        :param client: your dict (won’t be pulled from request_context automatically)
        """
        entry = {
            "id": str(uuid.uuid4()),
            "who": who,
            "resource": resource,
            "action": action,
            "timestamp": (timestamp or datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S"),
            "location": location,
            "request_context": request_context or {},
            "context": context or {},
            "client": client or {},
        }

        # fire-and-forget daemon thread
        t = Thread(target=self._publish, args=(entry,), daemon=True)
        t.start()

    def _publish(self, message: dict):
        async def _once():
            try:
                nc = await nats.connect(servers=[self.nats_url])
            except Exception as e:
                logger.error(f"[NATS] connect failed: {e}")
                return

            try:
                await nc.publish(self.subject, json.dumps(message).encode())
                # guard against hung flush
                await asyncio.wait_for(nc.flush(), timeout=1)
                logger.info(f"[NATS] published: {message}")
            except Exception as e:
                logger.error(f"[NATS] publish failed: {e}")
            finally:
                try:
                    await nc.close()
                except Exception:
                    pass

        try:
            asyncio.run(_once())
        except Exception as e:
            logger.error(f"[NATS] publish runner error: {e}")