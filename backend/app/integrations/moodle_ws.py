"""Moodle Web Services client — async integration with Moodle WS API."""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class MoodleWSError(Exception):
    pass


class MoodleWSAuthError(MoodleWSError):
    pass


class MoodleWSUnavailableError(MoodleWSError):
    pass


class MoodleWSClient:
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.retries = 3

    async def _request(self, ws_function: str, params: dict | None = None) -> dict | list:
        url = f"{self.base_url}/webservice/rest/server.php"
        data = {
            "wstoken": self.token,
            "wsfunction": ws_function,
            "moodlewsrestformat": "json",
            **(params or {}),
        }

        last_exception = None
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, data=data)
                if response.status_code == 401:
                    raise MoodleWSAuthError(
                        "Token de Moodle inválido o expirado"
                    )
                response.raise_for_status()
                return response.json()
            except MoodleWSAuthError:
                raise
            except httpx.TimeoutException as e:
                last_exception = MoodleWSUnavailableError(
                    f"Timeout conectando a Moodle (intento {attempt + 1}/{self.retries})"
                )
                logger.warning(
                    "Moodle timeout (attempt %d/%d): %s",
                    attempt + 1, self.retries, ws_function,
                )
            except httpx.HTTPStatusError as e:
                last_exception = MoodleWSUnavailableError(
                    f"Error HTTP {e.response.status_code} desde Moodle"
                )
                logger.warning(
                    "Moodle HTTP error (attempt %d/%d): %s",
                    attempt + 1, self.retries, e.response.status_code,
                )
            except httpx.RequestError as e:
                last_exception = MoodleWSUnavailableError(
                    f"No se pudo conectar a Moodle: {e}"
                )
                logger.warning(
                    "Moodle connection error (attempt %d/%d): %s",
                    attempt + 1, self.retries, str(e),
                )

            if attempt < self.retries - 1:
                await asyncio.sleep(2 ** attempt)

        raise last_exception  # type: ignore[misc]

    async def get_course_participants(self, course_id: int) -> list[dict]:
        result = await self._request(
            "core_enrol_get_enrolled_users",
            {"courseid": course_id},
        )
        if isinstance(result, dict):
            return [result]
        return result

    async def get_course_activities(self, course_id: int) -> list[dict]:
        result = await self._request(
            "core_course_get_contents",
            {"courseid": course_id},
        )
        if isinstance(result, dict):
            return [result]
        return result

    async def get_grades(self, course_id: int, user_ids: list[int]) -> list[dict]:
        result = await self._request(
            "gradereport_user_get_gradebook",
            {"courseid": course_id, "userids": user_ids},
        )
        if isinstance(result, dict):
            return [result]
        return result
