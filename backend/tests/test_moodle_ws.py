"""Tests for MoodleWSClient."""

import pytest

from app.integrations.moodle_ws import (
    MoodleWSClient,
    MoodleWSAuthError,
    MoodleWSUnavailableError,
)


class TestMoodleWSClient:
    def test_init_sets_defaults(self):
        client = MoodleWSClient(base_url="https://moodle.test", token="abc123")
        assert client.base_url == "https://moodle.test"
        assert client.token == "abc123"
        assert client.timeout == 30
        assert client.retries == 3

    def test_init_custom_timeout(self):
        client = MoodleWSClient(base_url="https://moodle.test", token="abc123", timeout=60)
        assert client.timeout == 60

    def test_init_normalizes_base_url(self):
        client = MoodleWSClient(base_url="https://moodle.test/", token="abc")
        assert not client.base_url.endswith("/")

    @pytest.mark.asyncio
    async def test_get_course_participants_raises_auth_error(self):
        client = MoodleWSClient(base_url="https://moodle.invalid", token="bad_token", timeout=1)
        with pytest.raises(MoodleWSUnavailableError):
            await client.get_course_participants(1)

    @pytest.mark.asyncio
    async def test_get_course_activities_raises_on_unreachable(self):
        client = MoodleWSClient(base_url="https://moodle.invalid", token="bad", timeout=1)
        with pytest.raises(MoodleWSUnavailableError):
            await client.get_course_activities(1)

    @pytest.mark.asyncio
    async def test_get_grades_raises_on_unreachable(self):
        client = MoodleWSClient(base_url="https://moodle.invalid", token="bad", timeout=1)
        with pytest.raises(MoodleWSUnavailableError):
            await client.get_grades(1, [1, 2])
