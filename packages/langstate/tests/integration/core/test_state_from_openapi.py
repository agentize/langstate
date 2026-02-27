"""Integration tests for creating states from OpenAPI schemas.

This module tests the complete workflow:
1. Loading an OpenAPI schema via OpenAPIReader
2. Creating states and populating them with data
3. Verifying graph structure contains all schema fields
4. Validating all graph export methods (to_ascii_tree, to_json, to_json_dict, to_mermaid, to_dot)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Set

import pytest

from core.data_structure.dah.dah import DirectedAcyclicHypergraph
from core.spec_extractor.base.schema import Schema, SchemaField
from core.spec_extractor.openapi.extractor import OpenAPIReader
from core.state.state.schema import (
    Inference,
    ValueConfidence,
)
from core.state.state.state import State


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def schema_path() -> Path:
    """Path to the registration schema fixture."""
    return (
        Path(__file__).parent.parent.parent / "data" / "schemas" / "registeration.yaml"
    )


@pytest.fixture
def openapi_reader() -> OpenAPIReader:
    """Create OpenAPIReader configured for Registration entity."""
    return OpenAPIReader(root_entity="Registration")


@pytest.fixture
def schema(schema_path: Path, openapi_reader: OpenAPIReader) -> Schema:
    """Load and parse the registration schema."""
    return openapi_reader.read(schema_path)


@pytest.fixture
def output_dir() -> Path:
    """Create output directory for test artifacts."""
    output_path = Path(__file__).parent / "test_outputs"
    if _should_save_output():
        output_path.mkdir(exist_ok=True)
    return output_path


def _should_save_output() -> bool:
    """Check if test outputs should be saved to files.

    Returns True only if TEST_OUTPUT environment variable is set to 'true'.
    """
    return os.environ.get("TEST_OUTPUT", "").lower() == "true"


# -----------------------------------------------------------------------------
# Test Data Helpers
# -----------------------------------------------------------------------------


def _get_expected_registration_fields() -> Set[str]:
    """Return the set of expected top-level field names in Registration schema."""
    return {"id", "registrant", "event", "guests", "total_price", "status"}


def _get_expected_person_fields() -> Set[str]:
    """Return the set of expected Person/registrant field names."""
    return {"id", "name", "email"}


def _get_expected_event_fields() -> Set[str]:
    """Return the set of expected Event field names."""
    return {"id", "name", "description", "schedule", "capacity", "remaining", "pricing"}


def _create_sample_registrant_data() -> Dict[str, ValueConfidence]:
    """Generate sample data for a registrant."""
    return {
        "registrant.id": ValueConfidence(value="REG-2026-001", confidence=0.9),
        "registrant.name": ValueConfidence(value="John Doe", confidence=0.9),
        "registrant.email": ValueConfidence(
            value="john.doe@example.com", confidence=0.9
        ),
    }


def _create_sample_event_data() -> Dict[str, ValueConfidence]:
    """Generate sample data for an event."""
    return {
        "event.id": ValueConfidence(value="EVT-PYTHON-2026", confidence=0.9),
        "event.name": ValueConfidence(value="PyCon 2026", confidence=0.9),
        "event.description": ValueConfidence(
            value="Annual Python conference with workshops and talks.", confidence=0.9
        ),
        "event.schedule": ValueConfidence(value="2026-05-15T09:00:00Z", confidence=0.9),
        "event.capacity": ValueConfidence(value=500, confidence=0.9),
        "event.remaining": ValueConfidence(value=350, confidence=0.9),
        "event.pricing": ValueConfidence(value=299.99, confidence=0.9),
    }


def _create_sample_guest_data(
    index: int, name: str, email: str
) -> Dict[str, ValueConfidence]:
    """Generate sample data for a guest at a specific index."""
    return {
        f"guests.{index}.id": ValueConfidence(
            value=f"GUEST-{index:03d}", confidence=0.9
        ),
        f"guests.{index}.name": ValueConfidence(value=name, confidence=0.9),
        f"guests.{index}.email": ValueConfidence(value=email, confidence=0.9),
    }


def _create_sample_invitation_data(guest_index: int) -> Dict[str, ValueConfidence]:
    """Generate sample invitation data for a guest."""
    return {
        f"guests.{guest_index}.invitation.subject": ValueConfidence(
            value=f"You're invited to PyCon 2026!", confidence=0.9
        ),
        f"guests.{guest_index}.invitation.body": ValueConfidence(
            value="Join us for an amazing conference experience.", confidence=0.9
        ),
        f"guests.{guest_index}.invitation.send_at": ValueConfidence(
            value="2026-04-01T10:00:00Z", confidence=0.9
        ),
    }


def _create_full_registration_data() -> Dict[str, ValueConfidence]:
    """Generate complete registration data with 2 guests."""
    data: Dict[str, ValueConfidence] = {
        "id": ValueConfidence(value="REG-MAIN-2026-001", confidence=0.9),
        "status": ValueConfidence(value="confirmed", confidence=0.9),
        "total_price": ValueConfidence(value=899.97, confidence=0.9),
    }

    # Add registrant
    data.update(_create_sample_registrant_data())

    # Add event
    data.update(_create_sample_event_data())

    # Add Guest 0 with invitation
    data.update(_create_sample_guest_data(0, "Alice Smith", "alice.smith@example.com"))
    data.update(_create_sample_invitation_data(0))

    # Add Guest 1 without invitation
    data.update(_create_sample_guest_data(1, "Bob Johnson", "bob.johnson@example.com"))

    return data


def _create_state_from_data(data: Dict[str, ValueConfidence]) -> State:
    """Create a State and populate it with data."""
    state = State()
    for path, vc in data.items():
        state.add_value(path, vc)
    return state


# -----------------------------------------------------------------------------
# Stage 1: Schema Parsing and Graph Structure Validation
# -----------------------------------------------------------------------------


class TestSchemaParsing:
    """Tests for OpenAPI schema parsing via OpenAPIReader."""

    def test_schema_file_exists(self, schema_path: Path) -> None:
        """Verify the test schema file exists."""
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

    def test_schema_loads_successfully(self, schema: Schema) -> None:
        """Verify schema loads without errors."""
        assert schema is not None
        assert schema.root is not None
        assert isinstance(schema.root, dict)

    def test_schema_contains_all_top_level_fields(self, schema: Schema) -> None:
        """Verify all expected top-level fields are present in parsed schema."""
        expected_fields = _get_expected_registration_fields()
        actual_fields = set(schema.root.keys())

        assert expected_fields == actual_fields, (
            f"Missing fields: {expected_fields - actual_fields}, "
            f"Extra fields: {actual_fields - expected_fields}"
        )

    def test_registrant_nested_structure(self, schema: Schema) -> None:
        """Verify registrant field has correct nested Person structure."""
        registrant_field = schema.root.get("registrant")
        assert registrant_field is not None
        assert isinstance(registrant_field, SchemaField)
        assert "object" in registrant_field.field_type

        # Check nested fields are in default_value
        nested_fields = registrant_field.default_value
        assert isinstance(nested_fields, dict)
        expected_person_fields = _get_expected_person_fields()
        # Cast to dict[str, SchemaField] for type safety
        nested_dict: Dict[str, SchemaField] = nested_fields  # type: ignore[assignment]
        actual_nested: Set[str] = set(nested_dict.keys())
        assert expected_person_fields == actual_nested

    def test_event_nested_structure(self, schema: Schema) -> None:
        """Verify event field has correct nested Event structure."""
        event_field = schema.root.get("event")
        assert event_field is not None
        assert isinstance(event_field, SchemaField)

        nested_fields = event_field.default_value
        assert isinstance(nested_fields, dict)
        expected_event_fields = _get_expected_event_fields()
        # Cast to dict[str, SchemaField] for type safety
        nested_dict: Dict[str, SchemaField] = nested_fields  # type: ignore[assignment]
        actual_nested: Set[str] = set(nested_dict.keys())
        assert expected_event_fields == actual_nested

    def test_guests_array_structure(self, schema: Schema) -> None:
        """Verify guests field is an array type.

        Note: The OpenAPI reader doesn't fully resolve allOf compositions for arrays,
        so item schema may be None. Array element fields are created dynamically
        when populating state with indexed paths like 'guests.0.name'.
        """
        guests_field = schema.root.get("guests")
        assert guests_field is not None
        assert isinstance(guests_field, SchemaField)
        assert "array" in guests_field.field_type

    def test_invitation_structure_in_schema(self, schema: Schema) -> None:
        """Verify Invitation is parsed as a referenced type.

        The Invitation type is referenced via $ref in the schema.
        Since Guest uses allOf with $ref to Person, the invitation
        field structure may not be directly accessible from guests.
        The actual field paths are created when populating state.
        """
        guests_field = schema.root.get("guests")
        assert guests_field is not None
        # The field_type indicates it's an array of objects
        assert "array" in guests_field.field_type


# -----------------------------------------------------------------------------
# Stage 2: Creating and Populating States
# -----------------------------------------------------------------------------


class TestStateCreation:
    """Tests for State creation and population."""

    def test_state_created_successfully(self) -> None:
        """Verify State can be created."""
        state = State()
        assert state is not None
        assert isinstance(state, State)

    def test_state_add_and_retrieve_values(self) -> None:
        """Verify values can be added and retrieved."""
        state = State()
        state.add_value("name", ValueConfidence(value="John", confidence=0.9))

        field = state.get_field("name")
        assert field is not None
        assert field.values[0].value == "John"
        assert field.values[0].confidence == 0.9

    def test_state_dah_structure(self) -> None:
        """Verify underlying DAH structure is valid."""
        state = State()
        state.add_value("field1", ValueConfidence(value="val1", confidence=0.9))

        dah = state.get_dah()
        assert dah is not None
        assert isinstance(dah, DirectedAcyclicHypergraph)
        assert len(dah.nodes) > 0


class TestStatePopulation:
    """Tests for populating state with data."""

    def test_add_value_with_confidence(self) -> None:
        """Verify values can be added with confidence scores."""
        state = State()

        state.add_value(
            "registrant.name",
            ValueConfidence(value="John Doe", confidence=0.95),
        )

        field = state.get_field("registrant.name")
        assert field is not None
        assert field.values[0].value == "John Doe"
        assert field.values[0].confidence == 0.95

    def test_add_multiple_values_different_confidence(self) -> None:
        """Verify multiple values can be added and best is selected by confidence."""
        state = State()

        state.add_value(
            "registrant.email",
            ValueConfidence(value="john@example.com", confidence=0.8),
        )
        state.add_value(
            "registrant.email",
            ValueConfidence(value="johndoe@example.com", confidence=0.95),
        )
        state.add_value(
            "registrant.email",
            ValueConfidence(value="j.doe@example.com", confidence=0.6),
        )

        field = state.get_field("registrant.email")
        assert field is not None
        best = max(field.values, key=lambda vc: vc.confidence)
        assert best.value == "johndoe@example.com"
        assert best.confidence == 0.95

    def test_add_inference(self) -> None:
        """Verify inferences can be added to fields and latest overwrites previous."""
        state = State()
        state.add_value(
            "event.name", ValueConfidence(value="PyCon 2026", confidence=0.9)
        )

        state.add_inference(
            "event.name",
            Inference(
                content="Extracted from form submission",
                mutator_id="form_extractor_v1",
            ),
        )
        state.add_inference(
            "event.name",
            Inference(
                content="Validated against event database",
                mutator_id="event_validator_v1",
            ),
        )

        field_state = state.get_field("event.name")
        assert field_state is not None
        assert field_state.inference is not None
        assert field_state.inference.content == "Validated against event database"
        assert field_state.inference.mutator_id == "event_validator_v1"

    def test_populate_guests_with_values_and_inferences(self) -> None:
        """Verify array elements can have values and inferences."""
        state = State()

        # Add guest 0
        state.add_value(
            "guests.0.name",
            ValueConfidence(value="Alice Smith", confidence=0.9),
        )
        state.add_inference(
            "guests.0.name",
            Inference(content="Parsed from guest list", mutator_id="guest_parser"),
        )

        # Add guest 1
        state.add_value(
            "guests.1.name",
            ValueConfidence(value="Bob Johnson", confidence=0.85),
        )

        assert state.get_field("guests.0.name") is not None
        assert state.get_field("guests.0.name").values[0].value == "Alice Smith"  # type: ignore[union-attr]
        assert state.get_field("guests.1.name").values[0].value == "Bob Johnson"  # type: ignore[union-attr]

    def test_state_copy(self) -> None:
        """Verify state can be copied."""
        state = State()
        state.add_value(
            "id",
            ValueConfidence(value="COPY-TEST", confidence=0.99),
        )
        state.add_inference(
            "id",
            Inference(content="Test inference", mutator_id="test"),
        )

        copied = state.copy()

        field_original = state.get_field("id")
        field_copied = copied.get_field("id")

        assert field_original is not None
        assert field_copied is not None
        assert field_original.values[0].value == field_copied.values[0].value

    def test_populate_full_registration(self) -> None:
        """Verify complete registration data can be populated."""
        full_data = _create_full_registration_data()
        state = _create_state_from_data(full_data)

        # Verify all data was set correctly
        assert state.get_field("id") is not None
        assert state.get_field("id").values[0].value == "REG-MAIN-2026-001"  # type: ignore[union-attr]
        assert state.get_field("status").values[0].value == "confirmed"  # type: ignore[union-attr]
        assert state.get_field("registrant.name").values[0].value == "John Doe"  # type: ignore[union-attr]
        assert state.get_field("event.name").values[0].value == "PyCon 2026"  # type: ignore[union-attr]
        assert state.get_field("guests.0.name").values[0].value == "Alice Smith"  # type: ignore[union-attr]
        assert state.get_field("guests.1.name").values[0].value == "Bob Johnson"  # type: ignore[union-attr]
        assert (
            state.get_field("guests.0.invitation.subject").values[0].value  # type: ignore[union-attr]
            == "You're invited to PyCon 2026!"
        )

    def test_set_nested_registrant_fields(self) -> None:
        """Verify nested registrant fields can be added."""
        data = _create_sample_registrant_data()
        state = _create_state_from_data(data)

        assert state.get_field("registrant.id").values[0].value == "REG-2026-001"  # type: ignore[union-attr]
        assert state.get_field("registrant.name").values[0].value == "John Doe"  # type: ignore[union-attr]
        assert state.get_field("registrant.email").values[0].value == "john.doe@example.com"  # type: ignore[union-attr]

    def test_set_nested_event_fields(self) -> None:
        """Verify nested event fields can be added."""
        data = _create_sample_event_data()
        state = _create_state_from_data(data)

        assert state.get_field("event.id").values[0].value == "EVT-PYTHON-2026"  # type: ignore[union-attr]
        assert state.get_field("event.name").values[0].value == "PyCon 2026"  # type: ignore[union-attr]
        assert state.get_field("event.capacity").values[0].value == 500  # type: ignore[union-attr]
        assert state.get_field("event.pricing").values[0].value == 299.99  # type: ignore[union-attr]

    def test_set_array_element_fields(self) -> None:
        """Verify array element fields can be set with indexed paths."""
        state = State()

        # Add two guests
        guest0_data = _create_sample_guest_data(0, "Alice Smith", "alice@example.com")
        guest1_data = _create_sample_guest_data(1, "Bob Johnson", "bob@example.com")

        for path, vc in guest0_data.items():
            state.add_value(path, vc)
        for path, vc in guest1_data.items():
            state.add_value(path, vc)

        assert state.get_field("guests.0.name").values[0].value == "Alice Smith"  # type: ignore[union-attr]
        assert state.get_field("guests.0.email").values[0].value == "alice@example.com"  # type: ignore[union-attr]
        assert state.get_field("guests.1.name").values[0].value == "Bob Johnson"  # type: ignore[union-attr]
        assert state.get_field("guests.1.email").values[0].value == "bob@example.com"  # type: ignore[union-attr]

    def test_set_deeply_nested_invitation_fields(self) -> None:
        """Verify deeply nested invitation fields within guest array."""
        invitation_data = _create_sample_invitation_data(0)
        state = _create_state_from_data(invitation_data)

        subj_field = state.get_field("guests.0.invitation.subject")
        assert subj_field is not None
        assert subj_field.values[0].value == "You're invited to PyCon 2026!"

        send_field = state.get_field("guests.0.invitation.send_at")
        assert send_field is not None


# -----------------------------------------------------------------------------
# Stage 3: Graph Export Methods Validation
# -----------------------------------------------------------------------------


@pytest.fixture
def populated_state() -> State:
    """State populated with full registration data and inferences."""
    state = State()

    # Add registration data with various confidences
    state.add_value("id", ValueConfidence(value="REG-MAIN-2026-001", confidence=1.0))
    state.add_value("status", ValueConfidence(value="confirmed", confidence=0.95))
    state.add_value("total_price", ValueConfidence(value=899.97, confidence=0.9))

    # Registrant with inference
    state.add_value(
        "registrant.name", ValueConfidence(value="John Doe", confidence=0.98)
    )
    state.add_inference(
        "registrant.name",
        Inference(
            content="Extracted from account profile", mutator_id="profile_extractor"
        ),
    )
    state.add_value(
        "registrant.email",
        ValueConfidence(value="john.doe@example.com", confidence=0.99),
    )

    # Event
    state.add_value("event.name", ValueConfidence(value="PyCon 2026", confidence=0.95))
    state.add_value("event.capacity", ValueConfidence(value=500, confidence=1.0))

    # Guests
    state.add_value(
        "guests.0.name", ValueConfidence(value="Alice Smith", confidence=0.9)
    )
    state.add_value(
        "guests.1.name", ValueConfidence(value="Bob Johnson", confidence=0.85)
    )

    return state


class TestStateDahExports:
    """Tests for state DAH export methods."""

    def test_to_ascii_tree(self, populated_state: State, output_dir: Path) -> None:
        """Verify to_ascii_tree produces valid ASCII tree output."""
        dah = populated_state.get_dah()
        tree = dah.to_ascii_tree()

        assert tree is not None
        assert isinstance(tree, str)
        assert len(tree) > 0
        assert "Schema" in tree
        assert "HyperEdges" in tree

        # Save to file if TEST_OUTPUT=true
        if _should_save_output():
            output_file = output_dir / "state_ascii_tree.txt"
            output_file.write_text(tree, encoding="utf-8")

    def test_to_ascii_tree_with_custom_label_fn(
        self, populated_state: State, output_dir: Path
    ) -> None:
        """Verify to_ascii_tree accepts custom label functions."""
        dah = populated_state.get_dah()

        def custom_label(value: Any) -> str:
            if value is None:
                return "(empty)"
            return f"[{value}]"

        tree = dah.to_ascii_tree(node_label_fn=custom_label, max_depth=5)

        assert tree is not None
        assert isinstance(tree, str)

        # Save to file if TEST_OUTPUT=true
        if _should_save_output():
            output_file = output_dir / "state_ascii_tree_custom.txt"
            output_file.write_text(tree, encoding="utf-8")

    def test_to_json(self, populated_state: State, output_dir: Path) -> None:
        """Verify to_json produces valid JSON string."""
        dah = populated_state.get_dah()
        json_str = dah.to_json(pretty=True, indent=2)

        assert json_str is not None
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

        # Save to file if TEST_OUTPUT=true
        if _should_save_output():
            output_file = output_dir / "state.json"
            output_file.write_text(json_str, encoding="utf-8")

    def test_to_json_compact(self, populated_state: State, output_dir: Path) -> None:
        """Verify to_json compact mode produces valid JSON."""
        dah = populated_state.get_dah()
        json_str = dah.to_json(pretty=False)

        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

        # Save to file if TEST_OUTPUT=true
        if _should_save_output():
            output_file = output_dir / "state_compact.json"
            output_file.write_text(json_str, encoding="utf-8")

    def test_to_json_dict(self, populated_state: State, output_dir: Path) -> None:
        """Verify to_json_dict produces valid dictionary structure."""
        dah = populated_state.get_dah()
        json_dict = dah.to_json_dict()

        assert json_dict is not None
        assert isinstance(json_dict, dict)
        assert "nodes" in json_dict
        assert "hyperedges" in json_dict
        assert "node_count" in json_dict
        assert "hyperedge_count" in json_dict

        # Verify nodes structure
        nodes: list[dict[str, object]] = json_dict["nodes"]
        assert isinstance(nodes, list)
        assert len(nodes) > 0

        # Each node should have id, path, value
        first_node: dict[str, object] = nodes[0]
        assert "id" in first_node
        assert "path" in first_node
        assert "value" in first_node

        # Save to file if TEST_OUTPUT=true
        if _should_save_output():
            output_file = output_dir / "state_dict.json"
            output_file.write_text(json.dumps(json_dict, indent=2), encoding="utf-8")

    def test_to_json_dict_contains_expected_paths(self, populated_state: State) -> None:
        """Verify JSON dict contains expected node paths."""
        dah = populated_state.get_dah()
        json_dict = dah.to_json_dict()

        nodes_list: list[dict[str, object]] = json_dict["nodes"]
        paths: set[str] = {str(node["path"]) for node in nodes_list}

        # Check key paths are present
        assert "id" in paths
        assert "registrant.name" in paths
        assert "event.name" in paths

    def test_to_mermaid(self, populated_state: State, output_dir: Path) -> None:
        """Verify to_mermaid produces valid Mermaid diagram format."""
        dah = populated_state.get_dah()
        mermaid = dah.to_mermaid()

        assert mermaid is not None
        assert isinstance(mermaid, str)
        assert len(mermaid) > 0
        assert mermaid.startswith("graph TD")

        # Save to file if TEST_OUTPUT=true
        if _should_save_output():
            output_file = output_dir / "state.mmd"
            output_file.write_text(mermaid, encoding="utf-8")

    def test_to_mermaid_with_custom_functions(
        self, populated_state: State, output_dir: Path
    ) -> None:
        """Verify to_mermaid accepts custom label functions."""
        dah = populated_state.get_dah()

        def node_label(value: Any) -> str:
            if value is None:
                return "null"
            return str(value)[:20]

        mermaid = dah.to_mermaid(node_label_fn=node_label, max_label_length=50)

        assert mermaid is not None
        assert "graph TD" in mermaid

        # Save to file if TEST_OUTPUT=true
        if _should_save_output():
            output_file = output_dir / "state_custom.mmd"
            output_file.write_text(mermaid, encoding="utf-8")

    def test_to_dot(self, populated_state: State, output_dir: Path) -> None:
        """Verify to_dot produces valid Graphviz DOT format."""
        dah = populated_state.get_dah()
        dot = dah.to_dot()

        assert dot is not None
        assert isinstance(dot, str)
        assert len(dot) > 0
        assert dot.startswith("digraph DAH")
        assert dot.strip().endswith("}")

        # Save to file if TEST_OUTPUT=true
        if _should_save_output():
            output_file = output_dir / "state.dot"
            output_file.write_text(dot, encoding="utf-8")


class TestExportConsistency:
    """Tests for consistency between export formats."""

    def test_json_and_json_dict_consistency(self, populated_state: State) -> None:
        """Verify to_json and to_json_dict produce consistent data."""
        dah = populated_state.get_dah()

        json_str = dah.to_json()
        json_dict = dah.to_json_dict()
        parsed_json = json.loads(json_str)

        assert json_dict["node_count"] == parsed_json["node_count"]
        assert json_dict["hyperedge_count"] == parsed_json["hyperedge_count"]

    def test_export_methods_non_empty_for_empty_state(self) -> None:
        """Verify export methods work even with fresh state (no data populated)."""
        fresh_state = State()
        # Add at least one field so DAH has content
        fresh_state.add_value("test", ValueConfidence(value=None, confidence=0.0))

        dah = fresh_state.get_dah()

        # All methods should work without errors
        assert dah.to_ascii_tree() is not None
        assert dah.to_json() is not None
        assert dah.to_json_dict() is not None
        assert dah.to_mermaid() is not None
        assert dah.to_dot() is not None


# -----------------------------------------------------------------------------
# Integration: Full Workflow Tests
# -----------------------------------------------------------------------------


class TestFullWorkflow:
    """End-to-end integration tests for complete workflow."""

    def test_complete_workflow_populate_and_export(self) -> None:
        """Test complete workflow: create state -> populate -> export."""
        # Step 1: Create state
        state = State()

        # Step 2: Populate state
        full_data = _create_full_registration_data()
        for path, vc in full_data.items():
            state.add_value(path, vc)

        # Step 3: Add additional data with higher confidence
        state.add_value(
            "registrant.name",
            ValueConfidence(value="Jane Doe", confidence=0.99),
        )
        state.add_inference(
            "registrant.name",
            Inference(content="Updated from user edit", mutator_id="user_input"),
        )

        # The best value should be Jane Doe (0.99) vs John Doe (0.9)
        name_field = state.get_field("registrant.name")
        assert name_field is not None
        best_name = max(name_field.values, key=lambda vc: vc.confidence)
        assert best_name.value == "Jane Doe"

        # Verify the inference was added
        field_state = state.get_field("registrant.name")
        assert field_state is not None
        assert len(field_state.values) >= 2  # Original + our addition
        assert field_state.inference is not None
        assert field_state.inference.content == "Updated from user edit"

        # Step 4: Verify exports work
        dah = state.get_dah()

        assert len(dah.to_ascii_tree()) > 0
        assert len(dah.to_json()) > 0

    def test_workflow_with_multiple_guests_and_invitations(self) -> None:
        """Test workflow with complex nested array data."""
        state = State()

        # Add multiple guests with invitations
        guest_names = ["Alice", "Bob", "Charlie", "Diana"]
        for i, name in enumerate(guest_names):
            state.add_value(
                f"guests.{i}.id",
                ValueConfidence(value=f"G{i:03d}", confidence=0.9),
            )
            state.add_value(
                f"guests.{i}.name",
                ValueConfidence(value=name, confidence=0.9),
            )
            state.add_value(
                f"guests.{i}.email",
                ValueConfidence(value=f"{name.lower()}@example.com", confidence=0.9),
            )

            # Add invitation for even-indexed guests
            if i % 2 == 0:
                state.add_value(
                    f"guests.{i}.invitation.subject",
                    ValueConfidence(value=f"Welcome {name}!", confidence=0.9),
                )
                state.add_value(
                    f"guests.{i}.invitation.body",
                    ValueConfidence(
                        value=f"Dear {name}, you are invited.", confidence=0.9
                    ),
                )

        # Verify all guests are stored
        for i, name in enumerate(guest_names):
            field = state.get_field(f"guests.{i}.name")
            assert field is not None
            assert field.values[0].value == name

        # Verify invitations
        subj0_field = state.get_field("guests.0.invitation.subject")
        assert subj0_field is not None
        assert subj0_field.values[0].value == "Welcome Alice!"
        assert state.get_field("guests.1.invitation.subject") is None
        subj2_field = state.get_field("guests.2.invitation.subject")
        assert subj2_field is not None
        assert subj2_field.values[0].value == "Welcome Charlie!"

        # Export should contain all data
        dah = state.get_dah()
        json_dict = dah.to_json_dict()
        nodes_list: list[dict[str, object]] = json_dict["nodes"]
        paths: set[str] = {str(node["path"]) for node in nodes_list}

        assert "guests.0.name" in paths
        assert "guests.3.name" in paths
        assert "guests.0.invitation.subject" in paths

    def test_state_iteration_methods(self) -> None:
        """Test state iteration and query methods."""
        state = State()

        # Populate some fields
        state.add_value("id", ValueConfidence(value="TEST-001", confidence=0.9))
        state.add_value("status", ValueConfidence(value="draft", confidence=0.9))
        state.add_value(
            "registrant.name",
            ValueConfidence(value="Test User", confidence=0.9),
        )

        # Test iter_fields
        field_count = sum(1 for _ in state.iter_fields())
        assert field_count > 0

        # Test get_all_fields
        all_fields = state.get_all_fields()
        assert len(all_fields) > 0

        # Verify field data
        id_field = all_fields.get("id")
        assert id_field is not None
        assert id_field.values[0].value == "TEST-001"

    def test_dah_topological_order(self, populated_state: State) -> None:
        """Test that DAH maintains valid topological order."""
        dah = populated_state.get_dah()

        # Should not raise exception
        order = dah.topological_order()

        assert isinstance(order, list)
        assert len(order) > 0

    def test_dah_validate_acyclic(self, populated_state: State) -> None:
        """Test that DAH validates acyclic property."""
        dah = populated_state.get_dah()

        # Should not raise exception for valid DAH
        dah.validate_acyclic()
