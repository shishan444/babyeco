"""Tests for point API endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from httpx import AsyncClient


@pytest.fixture
async def auth_setup(
    client: AsyncClient,
    sample_user_data: dict,
    sample_child_data: dict,
) -> dict:
    """Create authenticated user with child profile (no initial points)."""
    # Register user
    await client.post("/api/v1/auth/register", json=sample_user_data)

    # Login and get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        },
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create child profile
    child_response = await client.post(
        "/api/v1/children/",
        json=sample_child_data,
        headers=headers,
    )
    child_id = child_response.json()["id"]

    return {"headers": headers, "child_id": child_id}


@pytest.fixture
async def auth_setup_with_points(
    client: AsyncClient,
    sample_user_data: dict,
    sample_child_data: dict,
) -> dict:
    """Create authenticated user with child profile and initial points."""
    setup = await auth_setup(client, sample_user_data, sample_child_data)
    headers = setup["headers"]
    child_id = setup["child_id"]

    # Add initial points via adjust endpoint
    await client.post(
        f"/api/v1/points/child/{child_id}/points/adjust?amount=100&reason=Initial points",
        headers=headers,
    )

    return {"headers": headers, "child_id": child_id}


class TestPointBalance:
    """Tests for point balance endpoints."""

    @pytest.mark.asyncio
    async def test_get_balance_success(
        self,
        client: AsyncClient,
        auth_setup_with_points: dict,
    ) -> None:
        """Test getting balance for a child with points."""
        child_id = auth_setup_with_points["child_id"]
        headers = auth_setup_with_points["headers"]

        response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["balance"] >= 100
        assert data["available"] >= 100
        assert data["frozen"] == 0

    @pytest.mark.asyncio
    async def test_get_balance_no_points(
        self,
        client: AsyncClient,
        auth_setup: dict,
    ) -> None:
        """Test getting balance for child with no points."""
        headers = auth_setup["headers"]
        child_id = auth_setup["child_id"]

        response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["balance"] == 0
        assert data["frozen"] == 0
        assert data["available"] == 0

    @pytest.mark.asyncio
    async def test_get_balance_unauthorized(
        self,
        client: AsyncClient,
    ) -> None:
        """Test getting balance without auth fails."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/points/child/{fake_id}/balance",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPointEarn:
    """Tests for earning points."""

    @pytest.mark.asyncio
    async def test_earn_points_success(
        self,
        client: AsyncClient,
        auth_setup: dict,
    ) -> None:
        """Test successfully earning points."""
        headers = auth_setup["headers"]
        child_id = auth_setup["child_id"]

        # Initial balance
        initial_response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )
        initial_balance = initial_response.json()["balance"]

        # Earn points
        response = await client.post(
            f"/api/v1/points/child/{child_id}/points/earn",
            json={
                "child_id": child_id,
                "amount": 50,
                "source_type": "task_completion",
                "description": "Earned from completing task",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == 50
        assert data["type"] == "earn"

        # Verify balance increased
        balance_response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )
        assert balance_response.json()["balance"] == initial_balance + 50


class TestPointSpend:
    """Tests for spending points."""

    @pytest.mark.asyncio
    async def test_spend_points_success(
        self,
        client: AsyncClient,
        auth_setup_with_points: dict,
    ) -> None:
        """Test successfully spending points."""
        headers = auth_setup_with_points["headers"]
        child_id = auth_setup_with_points["child_id"]

        # Initial balance
        initial_response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )
        initial_balance = initial_response.json()["balance"]

        # Spend points
        response = await client.post(
            f"/api/v1/points/child/{child_id}/points/spend",
            json={
                "child_id": child_id,
                "amount": 30,
                "source_type": "exchange",
                "description": "Spent on reward",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == -30
        assert data["type"] == "spend"

        # Verify balance decreased
        balance_response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )
        assert balance_response.json()["balance"] == initial_balance - 30

    @pytest.mark.asyncio
    async def test_spend_insufficient_points(
        self,
        client: AsyncClient,
        auth_setup: dict,
    ) -> None:
        """Test spending more than available fails."""
        headers = auth_setup["headers"]
        child_id = auth_setup["child_id"]

        # Add some points first
        await client.post(
            f"/api/v1/points/child/{child_id}/points/earn",
            json={
                "child_id": child_id,
                "amount": 10,
                "source_type": "test",
            },
            headers=headers,
        )

        # Try to spend more than available
        response = await client.post(
            f"/api/v1/points/child/{child_id}/points/spend",
            json={
                "child_id": child_id,
                "amount": 100,
                "source_type": "test",
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPointAdjust:
    """Tests for manual point adjustments."""

    @pytest.mark.asyncio
    async def test_adjust_increase(
        self,
        client: AsyncClient,
        auth_setup: dict,
    ) -> None:
        """Test adjusting points upward."""
        headers = auth_setup["headers"]
        child_id = auth_setup["child_id"]

        # Initial balance
        initial_response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )
        initial_balance = initial_response.json()["balance"]

        # Adjust points
        response = await client.post(
            f"/api/v1/points/child/{child_id}/points/adjust?amount=25&reason=Bonus reward",
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == 25
        assert data["type"] == "adjust"

        # Verify balance
        balance_response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )
        assert balance_response.json()["balance"] == initial_balance + 25

    @pytest.mark.asyncio
    async def test_adjust_decrease(
        self,
        client: AsyncClient,
        auth_setup_with_points: dict,
    ) -> None:
        """Test adjusting points downward."""
        headers = auth_setup_with_points["headers"]
        child_id = auth_setup_with_points["child_id"]

        # Initial balance
        initial_response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )
        initial_balance = initial_response.json()["balance"]

        # Adjust points down
        response = await client.post(
            f"/api/v1/points/child/{child_id}/points/adjust?amount=-20&reason=Correction",
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == -20

        # Verify balance
        balance_response = await client.get(
            f"/api/v1/points/child/{child_id}/balance",
            headers=headers,
        )
        assert balance_response.json()["balance"] == initial_balance - 20


class TestTransactionHistory:
    """Tests for transaction history."""

    @pytest.mark.asyncio
    async def test_get_transaction_history(
        self,
        client: AsyncClient,
        auth_setup_with_points: dict,
    ) -> None:
        """Test getting transaction history."""
        headers = auth_setup_with_points["headers"]
        child_id = auth_setup_with_points["child_id"]

        # Create some transactions
        for i in range(3):
            await client.post(
                f"/api/v1/points/child/{child_id}/points/earn",
                json={
                    "child_id": child_id,
                    "amount": 10,
                    "source_type": "test",
                    "description": f"Transaction {i}",
                },
                headers=headers,
            )

        # Get history
        response = await client.get(
            f"/api/v1/points/child/{child_id}/transactions",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 4  # Initial + 3 new transactions
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_transaction_history_pagination(
        self,
        client: AsyncClient,
        auth_setup_with_points: dict,
    ) -> None:
        """Test transaction history pagination."""
        headers = auth_setup_with_points["headers"]
        child_id = auth_setup_with_points["child_id"]

        # Create multiple transactions
        for i in range(25):
            await client.post(
                f"/api/v1/points/child/{child_id}/points/earn",
                json={
                    "child_id": child_id,
                    "amount": 1,
                    "source_type": "test",
                },
                headers=headers,
            )

        # Get first page
        response = await client.get(
            f"/api/v1/points/child/{child_id}/transactions?page=1&page_size=10",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 10
        assert data["has_more"] is True

        # Get second page
        response2 = await client.get(
            f"/api/v1/points/child/{child_id}/transactions?page=2&page_size=10",
            headers=headers,
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert len(data2["items"]) == 10
