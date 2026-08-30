"""Tests for the Cronometer integration wrapper."""

from app.integrations.cronometer import CronometerService


class FakeCronometerClient:
    """Stands in for cronometer_api_mcp.client.CronometerClient."""

    def get_consumed_nutrients(self, day=None):
        return {
            "macros": {
                "energy": 2180.0,
                "protein": 160.0,
                "carbs": 210.0,
                "net_carbs": 200.0,
                "fat": 72.0,
                "fiber": 30.0,
                "alcohol": 0.0,
            }
        }


def test_get_day_summary_returns_energy_and_macros():
    service = CronometerService(client=FakeCronometerClient())

    summary = service.get_day_summary()

    assert summary == {
        "energy": 2180.0,
        "protein": 160.0,
        "carbs": 210.0,
        "fat": 72.0,
    }
