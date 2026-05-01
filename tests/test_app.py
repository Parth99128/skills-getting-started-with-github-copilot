"""
Tests for Mergington High School Activity Management API

Using the AAA (Arrange-Act-Assert) testing pattern:
- Arrange: Set up test data and fixtures
- Act: Execute the code being tested
- Assert: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Arrange: Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Arrange: Reset participants before each test to avoid cross-test contamination"""
    from src.app import activities
    
    # Store original state
    original_state = {}
    for activity_name, activity in activities.items():
        original_state[activity_name] = activity["participants"].copy()
    
    yield
    
    # Restore original state after test
    for activity_name, activity in activities.items():
        activities[activity_name]["participants"] = original_state[activity_name].copy()


class TestRootEndpoint:
    """Test suite for GET / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that root path redirects to static index.html"""
        # Arrange: No setup needed
        
        # Act: Make a GET request to root
        response = client.get("/", follow_redirects=False)
        
        # Assert: Verify redirect status and location
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivitiesEndpoint:
    """Test suite for GET /activities endpoint"""
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of activities"""
        # Arrange: No specific setup needed
        
        # Act: Fetch all activities
        response = client.get("/activities")
        
        # Assert: Verify response and data structure
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that all expected activities are returned"""
        # Arrange: No setup needed
        
        # Act: Fetch activities
        activities_data = client.get("/activities").json()
        
        # Assert: Verify expected activities exist
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Soccer Team",
            "Basketball Club", "Art Society", "Drama Club", "Science Club", "Debate Team"
        ]
        for activity in expected_activities:
            assert activity in activities_data
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has all required fields"""
        # Arrange: Get activities
        activities_data = client.get("/activities").json()
        
        # Act: Check structure of first activity
        first_activity = list(activities_data.values())[0]
        
        # Assert: Verify required fields exist
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for field in required_fields:
            assert field in first_activity
        
        assert isinstance(first_activity["participants"], list)
        assert isinstance(first_activity["max_participants"], int)


class TestSignupForActivityEndpoint:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        # Arrange: Prepare email and activity
        email = "newstudent@mergington.edu"
        activity = "Science Club"
        
        # Act: Sign up for activity
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify successful response
        assert response.status_code == 200
        assert email in response.json()["message"]
    
    def test_signup_adds_student_to_participants(self, client):
        """Test that signup actually adds student to activity"""
        # Arrange: Prepare test data
        email = "verify_signup@mergington.edu"
        activity = "Drama Club"
        
        # Act: Sign up student
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify student was added to participants list
        activities_response = client.get("/activities").json()
        assert email in activities_response[activity]["participants"]
    
    def test_signup_fails_for_nonexistent_activity(self, client):
        """Test that signup fails when activity doesn't exist"""
        # Arrange: Prepare invalid activity name
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act: Attempt to sign up for non-existent activity
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_fails_for_duplicate_student(self, client):
        """Test that student cannot sign up twice"""
        # Arrange: Use an existing participant
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act: Attempt to sign up again
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify 400 error for duplicate signup
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestUnregisterFromActivityEndpoint:
    """Test suite for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity"""
        # Arrange: Prepare existing participant
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act: Unregister from activity
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify successful response
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_student_from_participants(self, client):
        """Test that unregister actually removes student"""
        # Arrange: Get a participant to remove
        email = "daniel@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act: Unregister student
        client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify student was removed
        activities_response = client.get("/activities").json()
        assert email not in activities_response[activity]["participants"]
    
    def test_unregister_fails_for_nonexistent_activity(self, client):
        """Test that unregister fails when activity doesn't exist"""
        # Arrange: Prepare invalid activity name
        email = "student@mergington.edu"
        activity = "Fake Activity"
        
        # Act: Attempt to unregister from non-existent activity
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_fails_for_non_registered_student(self, client):
        """Test that unregister fails if student is not registered"""
        # Arrange: Prepare non-registered student
        email = "notregistered@mergington.edu"
        activity = "Science Club"
        
        # Act: Attempt to unregister non-registered student
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify 400 error
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()
