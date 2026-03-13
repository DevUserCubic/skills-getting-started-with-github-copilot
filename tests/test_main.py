"""
Unit tests for Mergington High School API using AAA (Arrange-Act-Assert) pattern.
Tests cover GET /activities, GET /, and POST /signup endpoints.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities_returns_nine_activities(self, client):
        """
        Arrange: Test client is ready
        Act: Make GET request to /activities
        Assert: Response contains all 9 activities
        """
        # Arrange & Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Soccer Team", "Basketball Club", "Art Workshop",
            "Drama Club", "Math Olympiad", "Science Club"
        ]
        assert set(activities.keys()) == set(expected_activities)

    def test_get_activities_returns_required_fields(self, client):
        """
        Arrange: Test client is ready
        Act: Make GET request to /activities
        Assert: Each activity has required fields
        """
        # Arrange & Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        required_fields = {"description", "schedule", "max_participants", "participants"}
        for activity_name, activity_data in activities.items():
            assert set(activity_data.keys()) == required_fields, \
                f"Activity '{activity_name}' missing required fields"

    def test_get_activities_initial_participants_present(self, client):
        """
        Arrange: Test client is ready
        Act: Make GET request to /activities
        Assert: Initial participants are loaded for each activity
        """
        # Arrange & Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]

        assert len(activities["Programming Class"]["participants"]) == 2
        assert "emma@mergington.edu" in activities["Programming Class"]["participants"]

    def test_get_activities_participants_is_list(self, client):
        """
        Arrange: Test client is ready
        Act: Make GET request to /activities
        Assert: Participants field is a list type
        """
        # Arrange & Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list), \
                f"Participants for '{activity_name}' should be a list"


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_endpoint_redirects_to_static_index(self, client):
        """
        Arrange: Test client is ready
        Act: Make GET request to /
        Assert: Redirects to /static/index.html with temporary redirect status (307)
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupHappyPath:
    """Tests for POST /signup endpoint - successful scenarios."""

    def test_signup_new_student_to_activity_succeeds(self, client):
        """
        Arrange: Prepare new email not in activity
        Act: Send POST request to signup endpoint
        Assert: Response status is 200 with success message
        """
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity}"

    def test_signup_adds_participant_to_activity_list(self, client):
        """
        Arrange: Prepare new email
        Act: Send POST request to signup, then GET activities
        Assert: Participant is added to the activity's participants list
        """
        # Arrange
        activity = "Chess Club"
        email = "alice@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        activities = activities_response.json()

        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]

    def test_multiple_signups_to_same_activity(self, client):
        """
        Arrange: Prepare two different emails
        Act: Sign up two students to same activity
        Assert: Both are added to participants list
        """
        # Arrange
        activity = "Soccer Team"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"

        # Act
        response1 = client.post(f"/activities/{activity}/signup", params={"email": email1})
        response2 = client.post(f"/activities/{activity}/signup", params={"email": email2})
        activities_response = client.get("/activities")
        activities = activities_response.json()

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email1 in activities[activity]["participants"]
        assert email2 in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == 4  # 2 initial + 2 new


class TestSignupErrorCases:
    """Tests for POST /signup endpoint - error scenarios."""

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Prepare request for activity that doesn't exist
        Act: Send POST request to signup
        Assert: Response is 404 with "Activity not found"
        """
        # Arrange
        activity = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student_returns_400(self, client):
        """
        Arrange: Student already signed up for activity
        Act: Send POST request to signup with same email
        Assert: Response is 400 with "already signed up" message
        """
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_missing_email_parameter_returns_error(self, client):
        """
        Arrange: Prepare request without email parameter
        Act: Send POST request without email
        Assert: Response is 422 (validation error)
        """
        # Arrange & Act
        response = client.post("/activities/Chess Club/signup")

        # Assert
        assert response.status_code == 422  # FastAPI validation error


class TestSignupEdgeCases:
    """Tests for POST /signup endpoint - edge cases."""

    def test_signup_email_with_special_characters(self, client):
        """
        Arrange: Email with special characters (+ sign)
        Act: Send POST request with special character email
        Assert: Signup succeeds and participant is added
        """
        # Arrange
        activity = "Programming Class"
        email = "user+test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        activities = activities_response.json()

        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]

    def test_signup_activity_name_with_spaces_url_encoded(self, client):
        """
        Arrange: Activity name with spaces (already in the system)
        Act: Send POST with activity name that has space
        Assert: Signup succeeds (FastAPI handles URL encoding)
        """
        # Arrange
        activity = "Programming Class"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200

    def test_signup_case_sensitive_activity_name(self, client):
        """
        Arrange: Prepare request with different case activity name
        Act: Send POST with wrong case
        Assert: Response is 404 (activity names are case-sensitive)
        """
        # Arrange
        activity = "chess club"  # Should be "Chess Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404

    def test_signup_empty_email_string(self, client):
        """
        Arrange: Prepare request with empty email string
        Act: Send POST with empty email
        Assert: Signup succeeds (backend accepts any string)
        """
        # Arrange
        activity = "Drama Club"
        email = ""

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
