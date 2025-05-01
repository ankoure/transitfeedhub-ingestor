from typing import Literal, TypedDict, Union


class MeasureDict(TypedDict):
    type: Literal["Measure"]
    values: list[Union[int, bool, float, str, None]]
    interpolation: Literal["Linear", "Discrete", "Stepwise"]


class TemporalPropsDict(TypedDict, total=False):
    datetimes: list[str]
    bearing: MeasureDict
    current_status: MeasureDict
    odometer: MeasureDict
    speed: MeasureDict
    stop_id: MeasureDict
    current_stop_sequence: MeasureDict
    occupancy_status: MeasureDict
    occupancy_percentage: MeasureDict
    congestion_level: MeasureDict
    # more carriage-specific keys dynamically added


class TemporalGeometryDict(TypedDict):
    type: Literal["MovingPoint"]
    coordinates: list[list[float]]
    datetimes: list[str]
    interpolation: Literal["Linear"]


class PropertiesDict(TypedDict):
    trajectory_id: int
    entity_id: str
    direction_id: Union[int, None]
    label: str
    trip_id: str
    route_id: str
    schedule_relationship: str
    trip_start_date: str
    trip_start_time: str
    vehicle_id: str
    vehicle_label: str
    license_plate: str


class FeatureDict(TypedDict):
    type: Literal["Feature"]
    temporalGeometry: TemporalGeometryDict
    properties: PropertiesDict
    temporalProperties: list[TemporalPropsDict]


class MFJSONDict(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[FeatureDict]
