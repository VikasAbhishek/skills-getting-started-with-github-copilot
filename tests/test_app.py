"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

# Create a test client
client = TestClient(app)


class TestGetActivities:
    """Tests for getting activities"""

    def test_get_activities_success(self):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify the response structure
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
    def test_activities_have_required_fields(self):
        """Test that all activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            
    def test_activities_have_valid_participant_counts(self):
        """Test that participant counts don't exceed max participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert len(activity_data["participants"]) <= activity_data["max_participants"]


class TestSignup:
    """Tests for signing up for activities"""

    def test_signup_success(self):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant to the activity"""
        email = "participant123@mergington.edu"
        
        # Sign up
        response = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Tennis Club"]["participants"]
        
    def test_signup_duplicate_email(self):
        """Test that signing up with duplicate email returns an error"""
        email = "duplicate@mergington.edu"
        
        # First signup
        response1 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
        
    def test_signup_nonexistent_activity(self):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestUnregister:
    """Tests for unregistering from activities"""

    def test_unregister_success(self):
        """Test successfully unregistering from an activity"""
        email = "unregister_test@mergington.edu"
        
        # First, sign up
        signup_response = client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        response = client.delete(
            "/activities/Drama Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removal_test@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Debate Team/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Debate Team"]["participants"]
        
        # Unregister
        client.delete(
            "/activities/Debate Team/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email not in data["Debate Team"]["participants"]
        
    def test_unregister_not_registered(self):
        """Test that unregistering someone not registered returns an error"""
        response = client.delete(
            "/activities/Science Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
        
    def test_unregister_nonexistent_activity(self):
        """Test that unregistering from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests for multiple operations"""

    def test_signup_and_unregister_flow(self):
        """Test complete signup and unregister flow"""
        email = "integration_test@mergington.edu"
        activity = "Basketball Team"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify count increased
        after_signup = client.get("/activities")
        signup_count = len(after_signup.json()[activity]["participants"])
        assert signup_count == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify count is back to original
        after_unregister = client.get("/activities")
        final_count = len(after_unregister.json()[activity]["participants"])
        assert final_count == initial_count
