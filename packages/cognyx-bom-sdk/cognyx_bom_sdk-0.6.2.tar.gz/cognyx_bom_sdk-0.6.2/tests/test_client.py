import json
import uuid
from collections.abc import Callable
from pathlib import Path
from unittest import mock

import pytest

from cognyx_bom_sdk.client import BomClient
from cognyx_bom_sdk.cognyx.models import BomOntology
from cognyx_bom_sdk.models import (
    Bom,
    BomInstance,
    BomInstanceSystemAttributes,
    BomInstanceUpdate,
    BomUpdates,
    ObjectType,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# IDs from valid_bom.json
GUITAR_BODY_ID = "a1d86ee1-def4-4abc-9282-96606db4fb0c"  # "Guitar Body", Assembly, level=4
HEADSTOCK_ID = "fa296e45-5b6a-4025-8f04-1d5bdb8c0f11"  # Headstock, Part, L1, Country


def create_client_with_file_input(
    bom_file_path: Path, callback: None | Callable = None
) -> BomClient:
    content = bom_file_path.read_text()
    decoded_content = json.loads(content)

    return BomClient(
        {
            "bom": decoded_content,
            "bom_ontology": BomOntology(
                objects={},
                object_types={},
                attributes={},
                diversities={},
            ),
        },
        update_callback=callback,
    )


def test_it_parses_a_valid_bom():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    parsed_bom = bom_client.bom
    assert isinstance(parsed_bom, Bom)

    assert parsed_bom.id == "3c914fd1-55f2-4d4b-a2b4-224377c05abf"
    assert parsed_bom.name == "Les Paul Guitar"
    assert parsed_bom.reference == "GTR-001"
    assert parsed_bom.description == "Complete Les Paul type electric guitar"
    assert parsed_bom.status == "draft"
    assert len(parsed_bom.instances) == 39

    first_instance = parsed_bom.instances[0]
    assert first_instance.id == "a1d86ee1-def4-4abc-9282-96606db4fb0c"
    assert first_instance.name == "Guitar Body"
    assert first_instance.reference == "BODY-001"
    assert first_instance.description == "Mahogany body with a maple top"
    assert first_instance.status == "not_started"
    assert first_instance.bom_id == "3c914fd1-55f2-4d4b-a2b4-224377c05abf"
    assert first_instance.view_id == "e5409126-65e5-4b11-adf0-ecc8e1812684"
    assert first_instance.object_type_id == "695192ba-681b-424f-bdff-c205e1205af7"
    assert first_instance.quantity == 1
    assert first_instance.variability_configurations == []
    assert first_instance.system_attributes == BomInstanceSystemAttributes(statuses=["is_standard"])

    custom_attributes = first_instance.custom_attributes
    assert len(custom_attributes) == 1

    assert custom_attributes[0].id == "fb244a5f-3915-45ff-a07a-36ae0e09ee78"
    assert custom_attributes[0].attribute_id == "84b3fb95-14e6-4476-91a8-39cbe2c023f0"
    assert custom_attributes[0].slug == "level"
    assert custom_attributes[0].type == "NUMBER"
    assert custom_attributes[0].name == "Level"
    assert custom_attributes[0].value == 4

    object_type = first_instance.object_type
    assert object_type.id == "695192ba-681b-424f-bdff-c205e1205af7"
    assert object_type.name == "Assembly"
    assert object_type.slug == "assembly"
    assert object_type.description == "Assembly entity type."
    assert object_type.base_unit == "pc"
    assert object_type.display_name == "Assembly"

    bom_attributes = object_type.bom_attributes
    assert len(bom_attributes) == 2

    assert bom_attributes[0].id == "84b3fb95-14e6-4476-91a8-39cbe2c023f0"
    assert bom_attributes[0].name == "Level"
    assert bom_attributes[0].slug == "level"
    assert bom_attributes[0].type == "NUMBER"
    assert bom_attributes[0].options == []

    assert bom_attributes[1].id == "489db359-09d1-4915-956f-7622abf3953b"
    assert bom_attributes[1].name == "Price"
    assert bom_attributes[1].slug == "price"
    assert bom_attributes[1].type == "NUMBER"
    assert bom_attributes[1].options == []


@pytest.mark.parametrize(
    "transformer",
    [
        lambda dict_: {**dict_, "id": None},
        lambda dict_: {**dict_, "id": 10},
        lambda dict_: {**dict_, "name": None},
        lambda dict_: {**dict_, "name": 10},
        lambda dict_: {**dict_, "description": 10},
        lambda dict_: {**dict_, "status": None},
        lambda dict_: {**dict_, "status": 10},
    ],
    ids=[
        "id_none",
        "id_int",
        "name_none",
        "name_int",
        "description_int",
        "status_none",
        "status_int",
    ],
)
def test_it_throws_an_exception_if_bom_is_invalid(transformer: Callable):
    content = (FIXTURES_DIR / "valid_bom.json").read_text()
    decoded_content = json.loads(content)

    modified_content = transformer(decoded_content)

    with pytest.raises(ValueError):
        BomClient(
            {
                "bom": modified_content,
                "bom_ontology": BomOntology(
                    objects={},
                    object_types={},
                    attributes={},
                    diversities={},
                ),
            }
        )


@pytest.mark.parametrize(
    "transformer",
    [
        lambda dict_: {**dict_, "id": None},
        lambda dict_: {**dict_, "id": 10},
        lambda dict_: {**dict_, "name": None},
        lambda dict_: {**dict_, "name": 10},
        lambda dict_: {**dict_, "reference": 10},
        lambda dict_: {**dict_, "description": 10},
        lambda dict_: {**dict_, "status": None},
        lambda dict_: {**dict_, "status": 10},
        lambda dict_: {**dict_, "bom_id": None},
        lambda dict_: {**dict_, "bom_id": 10},
        lambda dict_: {**dict_, "view_id": None},
        lambda dict_: {**dict_, "view_id": 10},
        lambda dict_: {**dict_, "object_type": None},
    ],
    ids=[
        "id_none",
        "id_int",
        "name_none",
        "name_int",
        "reference_int",
        "description_int",
        "status_none",
        "status_int",
        "bom_id_none",
        "bom_id_int",
        "view_id_none",
        "view_id_int",
        "object_type_none",
    ],
)
def test_it_throws_an_exception_if_bom_instance_is_invalid(transformer: Callable):
    content = (FIXTURES_DIR / "valid_bom.json").read_text()
    modified_content = json.loads(content)

    modified_content["instances"][0] = transformer(modified_content["instances"][0])

    with pytest.raises(ValueError):
        BomClient(
            {
                "bom": modified_content,
                "bom_ontology": BomOntology(
                    objects={},
                    object_types={},
                    attributes={},
                    diversities={},
                ),
            }
        )


def test_it_returns_bom_instance_by_name():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    bom_instance = bom_client.get_bom_instance("Guitar Body")
    assert isinstance(bom_instance, BomInstance)
    assert bom_instance.id == "a1d86ee1-def4-4abc-9282-96606db4fb0c"


def test_it_returns_bom_instance_by_id():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    bom_instance = bom_client.get_bom_instance_by_id("a1d86ee1-def4-4abc-9282-96606db4fb0c")
    assert isinstance(bom_instance, BomInstance)
    assert bom_instance.name == "Guitar Body"


def test_it_lists_bom_instances():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    assert len(bom_client.list_bom_instances()) == 39


def test_it_gets_instance_attribute():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    attribute_value = bom_client.get_instance_attribute(
        "a1d86ee1-def4-4abc-9282-96606db4fb0c", "Level"
    )
    assert attribute_value == 4


def test_it_throws_an_exception_if_instance_not_found_when_searching_attribute():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    with pytest.raises(ValueError):
        bom_client.get_instance_attribute("non_existent_id", "Level")


def test_it_sets_instance_attribute():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    bom_client.set_instance_attribute("a1d86ee1-def4-4abc-9282-96606db4fb0c", "Level", "foobar")
    assert (
        bom_client.get_instance_attribute("a1d86ee1-def4-4abc-9282-96606db4fb0c", "Level")
        == "foobar"
    )


def test_it_throws_an_exception_if_instance_not_found_when_setting_attribute():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    with pytest.raises(ValueError):
        bom_client.set_instance_attribute("non_existent_id", "Level", "lorem")


# todo
# test set_instance_attribute with callback
def test_it_sets_instance_attribute_and_calls_the_callback():
    callback = mock.Mock()
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json", callback=callback)

    bom_client.set_instance_attribute("a1d86ee1-def4-4abc-9282-96606db4fb0c", "Level", "foobar")

    callback.assert_called_once()
    call_arguments = callback.call_args[0]

    [attribute_update_input] = call_arguments
    assert attribute_update_input["type"] == BomUpdates.ATTRIBUTE_UPDATE

    attribute_update_payload = attribute_update_input["payload"]
    assert attribute_update_payload["instance_id"] == "a1d86ee1-def4-4abc-9282-96606db4fb0c"

    # attribute Level has id "84b3fb95-14e6-4476-91a8-39cbe2c023f0"
    assert attribute_update_payload["attribute_id"] == "84b3fb95-14e6-4476-91a8-39cbe2c023f0"
    assert attribute_update_payload["attribute_value"] == "foobar"


def test_it_updates_bom_instance():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    bom_client.update_bom_instance("a1d86ee1-def4-4abc-9282-96606db4fb0c", description="foobar")
    bom_instance = bom_client.get_bom_instance_by_id("a1d86ee1-def4-4abc-9282-96606db4fb0c")
    assert bom_instance is not None
    assert bom_instance.description == "foobar" if bom_instance else None


def test_it_raises_exception_if_bom_instance_not_found_when_updating():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")

    update_parameters = BomInstanceUpdate(description="foobar")

    with pytest.raises(ValueError):
        bom_client.update_bom_instance("lorem-ipsum", **update_parameters)


def test_it_updates_bom_instance_and_calls_the_callback():
    callback = mock.Mock()

    bom_client = create_client_with_file_input(
        FIXTURES_DIR / "valid_bom.json",
        callback=callback,
    )

    update_parameters = BomInstanceUpdate(description="foobar")
    bom_client.update_bom_instance("a1d86ee1-def4-4abc-9282-96606db4fb0c", **update_parameters)

    assert callback.call_count == 1

    call_arguments = callback.call_args[0]
    [update_payload] = call_arguments

    assert update_payload["type"] == BomUpdates.INSTANCE_UPDATE
    assert update_payload["payload"]["instance_id"] == "a1d86ee1-def4-4abc-9282-96606db4fb0c"


# --- Tests for create_instance ---
def test_it_creates_a_bom_instance():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")
    initial_instance_count = len(bom_client.list_bom_instances())

    # Mock bom_ontology as it's not fully populated by create_client_with_file_input
    # and create_instance relies on it to find object_type_id.
    part_obj_type_id = "6f76d888-4fdf-4bd6-8930-306ae49046c0"
    part_object_type = ObjectType(
        id=part_obj_type_id,
        name="Part",
        slug="part",
        bom_attributes=[],
        base_unit="unit",
        display_name="Part Display Name",
    )
    bom_client.bom_ontology = BomOntology(
        objects={},
        object_types={part_object_type.id: part_object_type},
        attributes={},
        diversities={},
    )
    # view_id is also needed for new instance creation
    bom_client.view_id = "e5409126-65e5-4b11-adf0-ecc8e1812684"

    instance_data = {
        "name": "New Test Part",
        "object_type": "Part",  # This name must match a name in bom_ontology.object_type
        "description": "A part created for testing",
        "reference": "TEST-001",
        "status": "not_started",
    }

    new_instance = bom_client.create_instance(**instance_data)

    assert isinstance(new_instance, BomInstance)
    assert new_instance.name == instance_data["name"]
    assert new_instance.object_type.name == instance_data["object_type"]
    assert new_instance.description == instance_data["description"]
    assert new_instance.reference == instance_data["reference"]
    assert new_instance.status == instance_data["status"]
    assert new_instance.bom_id == bom_client.bom.id
    assert new_instance.view_id == bom_client.view_id
    assert new_instance.object_type_id == part_object_type.id  # Check if correct ID was picked

    assert len(bom_client.list_bom_instances()) == initial_instance_count + 1
    assert bom_client.get_bom_instance_by_id(new_instance.id) is not None


def test_it_creates_a_bom_instance_and_calls_callback():
    mock_callback = mock.Mock()
    bom_client = create_client_with_file_input(
        FIXTURES_DIR / "valid_bom.json", callback=mock_callback
    )

    part_obj_type_id = "6f76d888-4fdf-4bd6-8930-306ae49046c0"
    part_object_type = ObjectType(
        id=part_obj_type_id,
        name="Part",
        slug="part",
        bom_attributes=[],
        base_unit="unit",
        display_name="Part Display Name",
    )
    bom_client.bom_ontology = BomOntology(
        object_types={part_object_type.id: part_object_type},
        diversities={},
        attributes={},
        objects={},
    )
    bom_client.view_id = "e5409126-65e5-4b11-adf0-ecc8e1812684"

    instance_data = {
        "name": "Callback Test Part",
        "object_type": "Part",
    }
    bom_client.create_instance(**instance_data)

    mock_callback.assert_called_once()
    call_args = mock_callback.call_args[0][0]

    assert call_args["type"] == BomUpdates.CREATE_INSTANCE
    assert "payload" in call_args
    assert isinstance(call_args["payload"]["properties"]["id"], str)
    assert isinstance(call_args["payload"]["properties"]["object_type_id"], str)
    assert call_args["payload"]["properties"]["name"] == instance_data["name"]
    assert call_args["payload"]["properties"]["object_type_id"] == part_object_type.id


def test_create_instance_raises_error_if_object_type_not_found_in_ontology():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")
    # Setup bom_ontology with a known type, but we'll try to create an unknown one
    known_obj_type_id = "some_id"
    known_object_type = ObjectType(
        id=known_obj_type_id,
        name="KnownType",
        slug="knowntype",
        bom_attributes=[],
        base_unit="unit",
        display_name="Known Type Display Name",
    )
    bom_client.bom_ontology = BomOntology(
        object_types={known_object_type.id: known_object_type},
        diversities={},
        attributes={},
        objects={},
    )

    instance_data = {"name": "Test", "object_type": "NonExistentType"}
    with pytest.raises(ValueError, match="object_type is required to create a BOM instance"):
        bom_client.create_instance(**instance_data)


def test_create_instance_raises_attribute_error_if_object_type_kwarg_missing_or_none():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")
    # bom_ontology needs to be populated for the check to pass before .lower() is called
    part_obj_type_id = "some_id"
    part_object_type = ObjectType(
        id=part_obj_type_id,
        name="Part",
        slug="part",
        bom_attributes=[],
        base_unit="unit",
        display_name="Part Display Name",
    )
    bom_client.bom_ontology = BomOntology(
        object_types={part_object_type.id: part_object_type},
        diversities={},
        attributes={},
        objects={},
    )

    # Test with object_type missing
    with pytest.raises(ValueError, match="object_type is required to create a BOM instance"):
        bom_client.create_instance(name="Test Part No Type")

    # Test with object_type as None
    with pytest.raises(ValueError, match="object_type is required to create a BOM instance"):
        bom_client.create_instance(name="Test Part None Type", object_type=None)


# --- Tests for delete_instance ---
def test_it_deletes_a_bom_instance():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")
    instance_to_delete_id = "a1d86ee1-def4-4abc-9282-96606db4fb0c"  # Exists in valid_bom.json
    assert bom_client.get_bom_instance_by_id(instance_to_delete_id) is not None
    initial_instance_count = len(bom_client.list_bom_instances())

    bom_client.delete_instance(instance_to_delete_id)

    assert bom_client.get_bom_instance_by_id(instance_to_delete_id) is None
    assert len(bom_client.list_bom_instances()) == initial_instance_count - 1


def test_it_deletes_a_bom_instance_and_calls_callback():
    mock_callback = mock.Mock()
    bom_client = create_client_with_file_input(
        FIXTURES_DIR / "valid_bom.json", callback=mock_callback
    )
    instance_to_delete_id = "a1d86ee1-def4-4abc-9282-96606db4fb0c"

    bom_client.delete_instance(instance_to_delete_id)

    mock_callback.assert_called_once()
    call_args = mock_callback.call_args[0][0]
    assert call_args["type"] == BomUpdates.DELETE_INSTANCE
    assert "instance_id" in call_args["payload"]
    assert call_args["payload"]["instance_id"] == instance_to_delete_id


def test_get_object_reference_returns_none_if_instance_not_found():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")
    non_existent_id = str(uuid.uuid4())
    with pytest.raises(ValueError, match=f"BOM instance with ID {non_existent_id} not found"):
        bom_client.get_object_reference(non_existent_id, diversity=None)


def test_get_object_reference_diversity_instance_not_found():
    bom_client = create_client_with_file_input(FIXTURES_DIR / "valid_bom.json")
    instance_id = GUITAR_BODY_ID  # "Guitar Body" - no diversity options

    # Try to get with diversity, should return None as no diverse instance exists
    obj_ref = bom_client.get_object_reference(instance_id, diversity="region:emea")
    assert obj_ref is None
