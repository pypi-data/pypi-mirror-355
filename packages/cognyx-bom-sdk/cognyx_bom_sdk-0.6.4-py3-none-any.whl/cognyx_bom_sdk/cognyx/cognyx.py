"""Cognyx BOM SDK client."""

import asyncio
from collections.abc import ValuesView

import httpx

from cognyx_bom_sdk.cognyx.helpers import format_bom, format_instance, get_parent_map
from cognyx_bom_sdk.cognyx.models import (
    BomEdge,
    BomInstanceResponse,
    BomNode,
    BomOntology,
    BomResponse,
    BomTree,
    BulkAttributesUpdateResponse,
    Diversity,
    GlobalSettingsResponse,
    LoadedBom,
    RootBomNode,
    VariabilityConfiguration,
)
from cognyx_bom_sdk.models import (
    AttributeDefinition,
    BomInstance,
    BomInstanceCreatePayload,
    BomInstanceUpdate,
    Object,
    ObjectType,
    Originator,
)


def safe_dict_values(dict_or_list: dict | list | None) -> list | ValuesView:
    """Return the values of a dictionary or list."""
    return dict_or_list.values() if isinstance(dict_or_list, dict) else dict_or_list or []


def headers(token: str, originator: Originator | None = None) -> dict[str, str]:
    """Generate headers for the Cognyx API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if originator is not None:
        originator_name = originator.get("name")
        originator_value = originator.get("value")
        if originator_name is not None:
            value: str = originator_value if originator_value is not None else originator_name
            name = f"CX-{originator_name.upper()}"
            headers[name] = value

    return headers


def get_variability_configuration(
    variability_configuration: dict, ontology: BomOntology
) -> VariabilityConfiguration:
    """Get a variability configuration by ID."""
    variability_data = ontology["diversities"][variability_configuration["variability_id"]]
    object_id = (
        variability_configuration.get("entity_id")
        or variability_configuration.get("object_id")
        or None
    )

    object_data = ontology["objects"][object_id] if object_id is not None else None

    variability = Diversity.model_validate(variability_data)
    object = Object.model_validate(object_data) if object_data is not None else None

    return VariabilityConfiguration.model_validate(
        {
            "id": variability_configuration["id"],
            "object_id": object_id,
            "object": object,
            "variability_id": variability_configuration["variability_id"],
            "variability": variability.model_dump(),
            "status": variability_configuration["status"],
        }
    )


def get_instance(instance_data: dict, ontology: BomOntology) -> BomInstanceResponse:
    """Get a BOM instance by ID.

    Args:
        instance_data: The data of the BOM instance
        ontology: objects of the bom

    Returns:
        The BOM instance data
    """
    instance_data["variability_configurations"] = [
        get_variability_configuration(v, ontology) for v in instance_data.get("variabilities", [])
    ]
    return BomInstanceResponse.model_validate(instance_data)


class CognyxClient:
    """Cognyx BOM SDK client."""

    def __init__(self, base_url: str, jwt_token: str) -> None:
        """Initialize the Cognyx client.

        Args:
            base_url: Base URL of the Cognyx API
            jwt_token: JWT token for authentication
        """
        self.base_url = base_url
        self.jwt_token = jwt_token
        self.bom_ontology: BomOntology | None = None

    async def get_bom(self, bom_id: str) -> BomResponse:
        """Get a BOM by ID.

        Args:
            bom_id: ID of the BOM to retrieve

        Returns:
            The BOM data
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/boms/{bom_id}",
                headers=headers(self.jwt_token),
            )
            response.raise_for_status()

            json = response.json()
            bom_data = json["data"]
            return BomResponse.model_validate(bom_data)

    async def get_default_view(self) -> str:
        """Get the default view for a BOM.

        Returns:
            The default view data
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/settings/global",
                headers=headers(self.jwt_token),
            )
            response.raise_for_status()

            settings = GlobalSettingsResponse.model_validate(response.json())

            return settings.features["boms"]["default_view"]

    async def get_bom_tree(self, bom_id: str, view_id: str | None = None) -> BomTree:
        """Get a BOM as a tree.

        Args:
            bom_id: ID of the BOM
            view_id: ID of the view

        Returns:
            The BOM data as a tree
        """
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            view_id = await self.get_default_view() if view_id is None else view_id

            response = await client.get(
                f"{self.base_url}/api/v1/boms/{bom_id}/tree",
                headers=headers(self.jwt_token),
                params={
                    "view_id": view_id,
                    "includeInstances": True,
                },
            )
            response.raise_for_status()

            edges = [BomEdge.model_validate(edge) for edge in response.json()["edges"]]

            parents_map = get_parent_map(edges)

            tree = response.json()

            nodes: list[RootBomNode | BomNode] = []

            diversities: dict[str, Diversity] = {
                diversity["id"]: Diversity.model_validate(diversity)
                for diversity in safe_dict_values(tree["related_entities"]["variabilities"])
            }

            attributes: dict[str, AttributeDefinition] = {
                attribute["id"]: AttributeDefinition.model_validate(attribute)
                for attribute in safe_dict_values(tree["related_entities"]["attributes"])
            }

            object_types: dict[str, ObjectType] = {
                object_type["id"]: ObjectType.model_validate(object_type)
                for object_type in safe_dict_values(tree["related_entities"]["entity_types"])
            }

            objects: dict[str, Object] = {
                entity["id"]: Object.model_validate(
                    {
                        "id": entity["id"],
                        "name": entity["name"],
                        "description": entity["description"],
                        "reference": entity["reference"],
                        "status": entity["status"],
                        "object_type": object_types[entity["entity_type_id"]],
                        "object_type_id": entity["entity_type_id"],
                        "attributes": [
                            {
                                **attributes[attr["attribute_id"]].model_dump(),
                                "attribute_id": attr["attribute_id"],
                                "value": attr["value"],
                            }
                            for attr in entity["attributes"] or []
                        ],
                        "created_at": entity["created_at"],
                        "updated_at": entity["updated_at"],
                    }
                )
                for entity in safe_dict_values(tree["related_entities"]["entities"])
            }

            related_entities = BomOntology(
                diversities=diversities,
                attributes=attributes,
                objects=objects,
                object_types=object_types,
            )

            for node in tree["nodes"]:
                if node["group"] == "Bom":
                    nodes.append(RootBomNode.model_validate(node))
                else:
                    if (parent_id := parents_map.get(node["id"])) is not None:
                        instance = get_instance(
                            node["system_attributes"]["instance"], related_entities
                        )

                        node["system_attributes"]["instance"] = format_instance(
                            instance=instance,
                            bom_id=bom_id,
                            view_id=view_id,
                            parent_id=parent_id,
                            bom_ontology=related_entities,
                        )

                    bom_node = BomNode.model_validate(node)
                    nodes.append(bom_node)

            return BomTree(
                nodes=nodes,
                edges=edges,
                related_entities=related_entities,
            )

    async def get_instance(
        self, instance_id: str, bom_id: str, view_id: str, parent_id: str | None = None
    ) -> BomInstance:
        """Get a BOM instance by ID asynchronously.

        Args:
            instance_id: ID of the BOM instance to retrieve
            bom_id: ID of the BOM
            view_id: ID of the view
            parent_id: ID of the parent instance

        Returns:
            The BOM instance data
        """
        if parent_id is None:
            raise ValueError("Parent ID is required")
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/bom-instances/{instance_id}",
                headers=headers(self.jwt_token),
                params={"include": "entityType,entityType.bomAttributes"},
            )
            response.raise_for_status()
            json = response.json()

            return BomInstance(
                **format_instance(
                    instance=BomInstanceResponse.model_validate(json["data"]),
                    bom_id=bom_id,
                    view_id=view_id,
                    parent_id=parent_id,
                    bom_ontology=self.bom_ontology if hasattr(self, "bom_ontology") else None,
                )
            )

    async def get_bom_instances(
        self,
        bom_id: str,
        nodes: list[BomNode],
        edges: list[BomEdge],
        view_id: str | None = None,
    ) -> list[BomInstance]:
        """Get all BOM instances for a BOM.

        Args:
            bom_id: ID of the BOM
            nodes: List of nodes in the BOM tree
            edges: List of edges in the BOM tree
            view_id: ID of the view

        Returns:
            List of BOM instance data
        """
        parent_map = get_parent_map(edges)
        view_id = await self.get_default_view() if view_id is None else view_id

        return await asyncio.gather(
            *[
                self.get_instance(node.id, bom_id, view_id, parent_map.get(node.id))
                for node in nodes
                if node.group != "Bom"
            ]
        )

    async def load_bom_data(self, bom_id: str, view_id: str | None = None) -> LoadedBom:
        """Load BOM data.

        Args:
            bom_id: ID of the BOM
            view_id: ID of the view

        Returns:
            The formatted BOM data
        """
        bom, bom_tree = await asyncio.gather(
            self.get_bom(bom_id),
            self.get_bom_tree(bom_id, view_id),
        )
        instances = [
            node.system_attributes["instance"]
            for node in bom_tree.nodes
            if isinstance(node, BomNode)
        ]

        self.instances = instances
        self.bom_ontology = bom_tree.related_entities

        return LoadedBom(
            bom=format_bom(bom, instances),
            bom_ontology=bom_tree.related_entities,
        )

    async def update_instance(
        self,
        instance_id: str,
        properties: BomInstanceUpdate,
        originator: Originator | None = None,
    ) -> BomInstanceResponse:
        """Update a BOM instance.

        Args:
            instance_id: ID of the BOM instance to update
            properties: Properties to update
            originator: Originator of the update

        Raises:
            httpx.HTTPStatusError: If the update fails
        """
        async with httpx.AsyncClient() as client:
            payload = {}

            for key, value in properties.items():
                if key == "object_type_id":
                    payload["entity_type_id"] = value
                else:
                    payload[key] = value

            try:
                response = await client.patch(
                    f"{self.base_url}/api/v1/bom-instances/{instance_id}",
                    headers=headers(token=self.jwt_token, originator=originator),
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()["data"]

                return BomInstanceResponse.model_validate(data)

            except httpx.HTTPStatusError as e:
                raise e

    async def update_instance_attribute(
        self,
        instance_id: str,
        attribute_id: str,
        value: str | int | float | bool | dict | list | None,
        originator: Originator | None = None,
    ) -> BulkAttributesUpdateResponse:
        """Update an attribute of a BOM instance.

        Args:
            instance_id: ID of the BOM instance to update
            attribute_id: ID of the attribute to update
            value: Value to set for the attribute
            originator: Originator of the update

        Raises:
            httpx.HTTPStatusError: If the update fails
        """
        async with httpx.AsyncClient() as client:
            payload = {
                "bomInstanceIds": [instance_id],
                "attributes": [
                    {
                        "attribute_id": attribute_id,
                        "value": value,
                    }
                ],
            }

            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/bom-instances/attributes/bulk-update",
                    headers=headers(token=self.jwt_token, originator=originator),
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()["data"]

                return BulkAttributesUpdateResponse.model_validate(data[0])

            except httpx.HTTPStatusError as e:
                raise e

    async def create_instance(
        self,
        instance: BomInstanceCreatePayload,
        bom_id: str,
        view_id: str | None = None,
        originator: Originator | None = None,
    ) -> BomInstance:
        """Create a new BOM instance.

        Args:
            instance: BOM instance data
            bom_id: ID of the BOM
            view_id: ID of the view
            originator: Originator of the instance

        Returns:
            The created BOM instance data
        """
        view_id = await self.get_default_view() if view_id is None else view_id

        uom = instance.get("uom", None)

        if uom is None:
            try:
                uom = (
                    self.bom_ontology["object_types"][instance["object_type_id"]].base_unit
                    if self.bom_ontology is not None
                    and self.bom_ontology["object_types"] is not None
                    and self.bom_ontology["object_types"][instance["object_type_id"]] is not None
                    else "pc"
                )
            except Exception:
                uom = "pc"

        bom_diversities = (
            list(self.bom_ontology.get("diversities", {}).values())
            if self.bom_ontology is not None
            else []
        )

        payload: dict = {
            "name": instance["name"],
            "entity_type_id": instance["object_type_id"],
            "description": instance["description"],
            "quantity": instance["quantity"],
            "reference": instance["reference"],
            "bom_id": bom_id,
            "view_id": view_id,
            "parent_id": instance["parent_id"] or None,
            "custom_attributes": [],
            "variabilities": [
                {"variability_id": diversity.id, "entity_id": None} for diversity in bom_diversities
            ],
            "status": "not_started",
            "uom": uom,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/bom-instances",
                headers=headers(self.jwt_token, originator=originator),
                json=payload,
            )
            response.raise_for_status()
            json = response.json()

            return BomInstance(
                **format_instance(
                    instance=BomInstanceResponse.model_validate(json["data"]),
                    bom_id=bom_id,
                    view_id=view_id,
                    parent_id=instance["parent_id"] or "",
                    bom_ontology=self.bom_ontology if hasattr(self, "bom_ontology") else None,
                )
            )

    async def delete_instance(self, instance_id: str, originator: Originator | None = None) -> None:
        """Delete a BOM instance.

        Args:
            instance_id: ID of the BOM instance to delete
            originator: Originator of the deletion
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/v1/bom-instances/{instance_id}",
                headers=headers(self.jwt_token, originator=originator),
            )
            response.raise_for_status()
