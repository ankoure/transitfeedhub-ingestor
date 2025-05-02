import datetime
import json
import os
import uuid
from typing import cast

from transitfeedhub_ingestor.protobuf import gtfs_realtime_pb2

from .s3Uploader import upload_file
from .types import FeatureDict


class Carriage:
    """Summary line.

    This class represents a single carriage from the optional multi_carriage_details element.
    The MBTA Subways use this element to represent each car in the train, and will have occupancy status here instead of the top level Vehicle Position Message.

    Args:
        carriage_details: entity.vehicle.multi_carriage_details where entity represents a single vehicle from the feed message.

    Returns:
        Creates a class represeting:
        label: string for train number or other identifier
        carriage_sequence: integer representing order of train car placement. I.e 1 is the front
        occupancy_status: list of integers representing the occupancy status enum from GTFS RT Standard

    """

    def __init__(self, carriage_details: gtfs_realtime_pb2.VehiclePosition.CarriageDetails):
        self.label: str = carriage_details.label
        self.carriage_sequence: int = carriage_details.carriage_sequence
        self.occupancy_status: list[int] = [carriage_details.occupancy_status]

    def Update(self, carriage_details: gtfs_realtime_pb2.VehiclePosition.CarriageDetails):
        self.occupancy_status.append(carriage_details.occupancy_status)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Entity:
    def __init__(self, entity: gtfs_realtime_pb2.VehiclePosition):
        self.entity_id: str = entity.vehicle.id

        # Static
        self.direction_id: int = entity.trip.direction_id
        self.label: str = entity.vehicle.label
        # TODO: self.revenue = attributes.get("revenue", None)
        self.created = datetime.datetime.now()
        self.route_id: str = entity.trip.route_id
        self.trip_id: str = entity.trip.trip_id
        self.schedule_relationship: int = entity.trip.schedule_relationship
        self.start_date: str = entity.trip.start_date
        self.start_time: str = entity.trip.start_time
        self.vehicle_id: str = entity.vehicle.id
        self.vehicle_label: str = entity.vehicle.label
        self.license_plate: str = entity.vehicle.license_plate

        # Temporal
        self.bearing: list[float] = [entity.position.bearing]
        self.current_status: list[int] = [entity.current_status]
        self.odometer: list[float] = [entity.position.odometer]
        self.speed: list[float] = [entity.position.speed]
        self.stop_id: list[str] = [entity.stop_id]
        self.updated_at: list[str] = [datetime.datetime.fromtimestamp(entity.timestamp).isoformat()]
        self.current_stop_sequence: list[int] = [entity.current_stop_sequence]
        self.coordinates: list[list[float]] = [[entity.position.longitude, entity.position.latitude]]
        self.occupancy_status: list[int] = [entity.occupancy_status]
        self.occupancy_percentage: list[int] = [entity.occupancy_percentage]
        self.congestion_level: list[int] = [entity.congestion_level]

        self.carriages = [Carriage(c) for c in entity.multi_carriage_details]

        # TODO: get multicarriage details
        # print(entity.vehicle.multi_carriage_details)
        # print(entity.vehicle.multi_carriage_details[0].label)
        # print(entity.vehicle.multi_carriage_details[0].carriage_sequence)
        # first two = static, third = temporal
        # print(entity.vehicle.multi_carriage_details[0].occupancy_status)

    def update(self, entity: gtfs_realtime_pb2.VehiclePosition):
        # Temporal
        self.bearing.append(entity.position.bearing)
        self.current_status.append(entity.current_status)
        self.current_stop_sequence.append(entity.current_stop_sequence)
        self.coordinates.append([entity.position.longitude, entity.position.latitude])
        self.occupancy_status.append(entity.occupancy_status)
        self.occupancy_percentage.append(entity.occupancy_percentage)
        self.speed.append(entity.position.speed)
        self.odometer.append(entity.position.odometer)
        # TODO: need to convert to ISO 8601 format
        self.updated_at.append(datetime.datetime.fromtimestamp(entity.timestamp).isoformat())
        self.stop_id.append(entity.stop_id)
        self.congestion_level.append(entity.congestion_level)

        for carriage in entity.multi_carriage_details:
            carriage_obj = next((c for c in self.carriages if c.label == carriage.label), None)
            if carriage_obj:
                carriage_obj.Update(carriage)

    def checkage(self):
        # checks age of object and returns age in seconds
        return (datetime.datetime.now() - self.created).total_seconds()

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def toMFJSON(self) -> str:
        # TODO: add carriage details
        # TODO: Need to update properties being written out
        dict_template = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "temporalGeometry": {
                        "type": "MovingPoint",
                        "coordinates": self.coordinates,
                        "datetimes": self.updated_at,
                        "interpolation": "Linear",
                    },
                    "properties": {
                        "trajectory_id": 0,
                        "entity_id": self.entity_id,
                        "direction_id": self.direction_id,
                        "label": self.label,
                        "trip_id": self.trip_id,
                        "route_id": self.route_id,
                        "schedule_relationship": self.schedule_relationship,
                        "trip_start_date": self.start_date,
                        "trip_start_time": self.start_time,
                        "vehicle_id": self.vehicle_id,
                        "vehicle_label": self.vehicle_label,
                        "license_plate": self.license_plate,
                    },
                    "temporalProperties": [
                        {
                            "datetimes": self.updated_at,
                            "bearing": {
                                "type": "Measure",
                                "values": self.bearing,
                                "interpolation": "Linear",
                            },
                            "current_status": {
                                "type": "Measure",
                                "values": self.current_status,
                                "interpolation": "Discrete",
                            },
                            "odometer": {
                                "type": "Measure",
                                "values": self.odometer,
                                "interpolation": "Discrete",
                            },
                            "speed": {
                                "type": "Measure",
                                "values": self.speed,
                                "interpolation": "Linear",
                            },
                            "stop_id": {
                                "type": "Measure",
                                "values": self.stop_id,
                                "interpolation": "Discrete",
                            },
                            "current_stop_sequence": {
                                "type": "Measure",
                                "values": self.current_stop_sequence,
                                "interpolation": "Discrete",
                            },
                            "occupancy_status": {
                                "type": "Measure",
                                "values": self.occupancy_status,
                                "interpolation": "Discrete",
                            },
                            "occupancy_percentage": {
                                "type": "Measure",
                                "values": self.occupancy_percentage,
                                "interpolation": "Discrete",
                            },
                            "congestion_level": {
                                "type": "Measure",
                                "values": self.congestion_level,
                                "interpolation": "Discrete",
                            },
                        }
                    ],
                }
            ],
        }
        first_feature = cast(FeatureDict, dict_template["features"][0])
        temporal_properties = first_feature["temporalProperties"][0]
        for carriage in self.carriages:
            carriage_key = f"carriage_{carriage.carriage_sequence}_{carriage.label}"
            temporal_properties[carriage_key] = {
                "type": "Measure",
                "values": carriage.occupancy_status,
                "interpolation": "Discrete",
            }

        return json.dumps(
            dict_template,
            indent=4,
        )

    def save(self, file_path: str):
        isExist = os.path.exists(f"{file_path}/{self.route_id}")
        if isExist is False:
            os.makedirs(f"{file_path}/{self.route_id}", mode=0o777, exist_ok=False)
            with open(f"{file_path}/{self.route_id}/{uuid.uuid4()}.mfjson", "w") as f:
                f.write(self.toMFJSON())
        else:
            with open(f"{file_path}/{self.route_id}/{uuid.uuid4()}.mfjson", "w") as f:
                f.write(self.toMFJSON())

    def savetos3(self, bucket: str, file_path: str):
        upload_file(self.toMFJSON(), bucket, f"{file_path}/{uuid.uuid4()}.mfjson")
