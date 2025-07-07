"""Test the models."""

import pytest
from datetime import datetime
from khandhas.models import BaseModel, ResponseModel, RequestModel, UserModel


def test_base_model():
    """Test BaseModel functionality."""
    model = BaseModel(name="test", value=42)

    assert model.name == "test"
    assert model.value == 42

    # Test to_dict
    data = model.to_dict()
    assert data["name"] == "test"
    assert data["value"] == 42

    # Test to_json
    json_str = model.to_json()
    assert '"name": "test"' in json_str
    assert '"value": 42' in json_str

    # Test from_dict
    new_model = BaseModel.from_dict(data)
    assert new_model.name == "test"
    assert new_model.value == 42


def test_response_model():
    """Test ResponseModel functionality."""
    response = ResponseModel(
        success=True, message="Test message", data={"key": "value"}
    )

    assert response.success is True
    assert response.message == "Test message"
    assert response.data == {"key": "value"}
    assert response.error is None
    assert isinstance(response.timestamp, datetime)

    # Test model_dump
    data = response.model_dump()
    assert data["success"] is True
    assert data["message"] == "Test message"
    assert data["data"] == {"key": "value"}


def test_response_model_error():
    """Test ResponseModel with error."""
    response = ResponseModel(
        success=False, message="Error occurred", error="Something went wrong"
    )

    assert response.success is False
    assert response.message == "Error occurred"
    assert response.error == "Something went wrong"
    assert response.data is None


def test_request_model():
    """Test RequestModel functionality."""
    request = RequestModel(param1="value1", param2="value2")

    assert request.param1 == "value1"
    assert request.param2 == "value2"

    # Test validation
    assert request.validate() is True
    assert request.get_errors() == []


def test_user_model():
    """Test UserModel functionality."""
    user = UserModel(id="123", username="testuser", email="test@example.com")

    assert user.id == "123"
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)

    # Test to_dict with datetime
    data = user.to_dict()
    assert data["id"] == "123"
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert isinstance(data["created_at"], str)  # Should be ISO format
    assert isinstance(data["updated_at"], str)  # Should be ISO format


def test_nested_models():
    """Test nested model functionality."""
    user = UserModel(id="123", username="test", email="test@example.com")
    response = ResponseModel(success=True, message="User retrieved", data=user)

    # Test nested to_dict
    data = response.to_dict()
    assert data["success"] is True
    assert data["message"] == "User retrieved"
    assert isinstance(data["data"], dict)
    assert data["data"]["id"] == "123"
    assert data["data"]["username"] == "test"


def test_model_with_list():
    """Test model with list of models."""
    users = [
        UserModel(id="1", username="user1", email="user1@example.com"),
        UserModel(id="2", username="user2", email="user2@example.com"),
    ]

    response = ResponseModel(success=True, message="Users retrieved", data=users)

    # Test to_dict with list
    data = response.to_dict()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == "1"
    assert data["data"][1]["id"] == "2"
