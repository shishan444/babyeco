"""Tests for task API endpoints."""

import pytest
from datetime import date, timedelta
from fastapi import status
from httpx import AsyncClient


@pytest.fixture
async def auth_headers_with_child(
    client: AsyncClient,
    sample_user_data: dict,
    sample_child_data: dict,
) -> dict:
    """Create authentication headers with a child profile."""
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


class TestTaskCreation:
    """Tests for task creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_task_success(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test successful task creation."""
        task_data = {
            "child_id": auth_headers_with_child["child_id"],
            "title": "Clean room",
            "description": "Clean and organize your room",
            "category": "daily",
            "points": 10,
            "due_date": str(date.today() + timedelta(days=1)),
        }

        response = await client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=auth_headers_with_child["headers"],
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["points"] == task_data["points"]
        assert data["status"] == "pending"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_task_unauthorized(
        self,
        client: AsyncClient,
        sample_child_data: dict,
    ) -> None:
        """Test task creation without auth fails."""
        task_data = {
            "child_id": "00000000-0000-0000-0000-000000000000",
            "title": "Test task",
            "points": 10,
        }

        response = await client.post("/api/v1/tasks/", json=task_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_task_invalid_points(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test task creation with invalid points fails."""
        task_data = {
            "child_id": auth_headers_with_child["child_id"],
            "title": "Test task",
            "points": 150,  # Max is 100
        }

        response = await client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=auth_headers_with_child["headers"],
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_recurring_task(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test creating a recurring task."""
        task_data = {
            "child_id": auth_headers_with_child["child_id"],
            "title": "Brush teeth",
            "category": "daily",
            "points": 5,
            "is_recurring": True,
            "recurrence_pattern": "0 20 * * *",  # Daily at 8 PM
        }

        response = await client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=auth_headers_with_child["headers"],
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_recurring"] is True
        assert data["recurrence_pattern"] == "0 20 * * *"


class TestTaskListing:
    """Tests for task listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_child_tasks_success(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test listing tasks for a child."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create multiple tasks
        for i in range(3):
            await client.post(
                "/api/v1/tasks/",
                json={
                    "child_id": child_id,
                    "title": f"Task {i}",
                    "points": 10,
                },
                headers=headers,
            )

        response = await client.get(
            f"/api/v1/tasks/child/{child_id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 3
        assert len(data["tasks"]) >= 3

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_status(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test filtering tasks by status."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create a task
        await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )

        response = await client.get(
            f"/api/v1/tasks/child/{child_id}?status=pending",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for task in data["tasks"]:
            assert task["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_date(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test filtering tasks by date."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]
        today = str(date.today())

        # Create task with today's date
        await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Today's task",
                "points": 10,
                "due_date": today,
            },
            headers=headers,
        )

        response = await client.get(
            f"/api/v1/tasks/child/{child_id}?date={today}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK


class TestTaskUpdate:
    """Tests for task update endpoint."""

    @pytest.mark.asyncio
    async def test_update_task_success(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test updating a task."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create task
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Original title",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]

        # Update task
        response = await client.put(
            f"/api/v1/tasks/{task_id}",
            json={
                "title": "Updated title",
                "points": 20,
            },
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated title"
        assert data["points"] == 20

    @pytest.mark.asyncio
    async def test_update_nonexistent_task(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test updating a nonexistent task fails."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.put(
            f"/api/v1/tasks/{fake_id}",
            json={"title": "Updated"},
            headers=auth_headers_with_child["headers"],
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTaskCompletion:
    """Tests for task completion workflow."""

    @pytest.mark.asyncio
    async def test_complete_task_success(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test marking a task as completed."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create task
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]

        # Complete task (no auth required for child devices)
        response = await client.post(
            f"/api/v1/tasks/{task_id}/complete",
            json={},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "awaiting_approval"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_complete_task_with_proof(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test completing task with image proof."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create task
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]

        # Complete with proof
        response = await client.post(
            f"/api/v1/tasks/{task_id}/complete",
            json={"image_proof_url": "https://example.com/proof.jpg"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["image_url"] == "https://example.com/proof.jpg"

    @pytest.mark.asyncio
    async def test_complete_already_completed_task(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test completing an already completed task fails."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create and complete task
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]
        await client.post(f"/api/v1/tasks/{task_id}/complete", json={})

        # Try to complete again
        response = await client.post(
            f"/api/v1/tasks/{task_id}/complete",
            json={},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTaskApproval:
    """Tests for task approval workflow."""

    @pytest.mark.asyncio
    async def test_approve_task_success(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test approving a completed task."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create and complete task
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]
        await client.post(f"/api/v1/tasks/{task_id}/complete", json={})

        # Approve task
        response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True},
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "approved"
        assert data["approved_at"] is not None

    @pytest.mark.asyncio
    async def test_approve_task_with_bonus(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test approving task with bonus points."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create and complete task
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]
        await client.post(f"/api/v1/tasks/{task_id}/complete", json={})

        # Approve with bonus
        response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True, "bonus_points": 5},
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_reject_task(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test rejecting a completed task."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create and complete task
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]
        await client.post(f"/api/v1/tasks/{task_id}/complete", json={})

        # Reject task
        response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": False, "feedback": "Not done properly"},
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_approve_non_awaiting_task(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test approving a task not awaiting approval fails."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create task (still pending)
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]

        # Try to approve without completion
        response = await client.post(
            f"/api/v1/tasks/{task_id}/approve",
            json={"approved": True},
            headers=headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTaskDeletion:
    """Tests for task deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_task_success(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test soft deleting a task."""
        child_id = auth_headers_with_child["child_id"]
        headers = auth_headers_with_child["headers"]

        # Create task
        create_response = await client.post(
            "/api/v1/tasks/",
            json={
                "child_id": child_id,
                "title": "Test task",
                "points": 10,
            },
            headers=headers,
        )
        task_id = create_response.json()["id"]

        # Delete task
        response = await client.delete(
            f"/api/v1/tasks/{task_id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's soft deleted (not in list)
        list_response = await client.get(
            f"/api/v1/tasks/child/{child_id}",
            headers=headers,
        )
        task_ids = [t["id"] for t in list_response.json()["tasks"]]
        assert task_id not in task_ids

    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(
        self,
        client: AsyncClient,
        auth_headers_with_child: dict,
    ) -> None:
        """Test deleting a nonexistent task fails."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/tasks/{fake_id}",
            headers=auth_headers_with_child["headers"],
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
