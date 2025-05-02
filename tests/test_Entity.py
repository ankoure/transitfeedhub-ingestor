import datetime

import requests

from transitfeedhub_ingestor.helpers.Entity import Entity
from transitfeedhub_ingestor.protobuf import gtfs_realtime_pb2


def test_entity():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get("https://cdn.mbta.com/realtime/VehiclePositions.pb", timeout=30)
    feed.ParseFromString(response.content)

    feed_entity = feed.entity[0]
    entity = Entity(feed_entity)

    assert feed_entity.vehicle.trip.direction_id == entity.direction_id
    assert feed_entity.vehicle.vehicle.label == entity.label
    assert isinstance(entity.created, datetime.datetime)
    assert feed_entity.vehicle.trip.route_id == entity.route_id
    assert feed_entity.vehicle.trip.trip_id == entity.trip_id
    assert feed_entity.vehicle.trip.schedule_relationship == entity.schedule_relationship
    assert feed_entity.vehicle.trip.start_date == entity.start_date
    assert feed_entity.vehicle.trip.start_time == entity.start_time
    assert feed_entity.vehicle.vehicle.id == entity.vehicle_id
    assert feed_entity.vehicle.vehicle.label == entity.vehicle_label
    assert feed_entity.vehicle.vehicle.license_plate == entity.license_plate

    assert [feed_entity.vehicle.position.bearing] == entity.bearing
    assert [feed_entity.vehicle.current_status] == entity.current_status
    assert [feed_entity.vehicle.position.odometer] == entity.odometer
    assert [feed_entity.vehicle.position.speed] == entity.speed

    assert [feed_entity.vehicle.stop_id] == entity.stop_id
    assert [datetime.datetime.fromtimestamp(feed_entity.vehicle.timestamp).isoformat()] == entity.updated_at
    assert [feed_entity.vehicle.current_stop_sequence] == entity.current_stop_sequence
    assert [[feed_entity.vehicle.position.longitude, feed_entity.vehicle.position.latitude]] == entity.coordinates

    assert [feed_entity.vehicle.occupancy_status] == entity.occupancy_status
    assert [feed_entity.vehicle.occupancy_percentage] == entity.occupancy_percentage
    assert [feed_entity.vehicle.congestion_level] == entity.congestion_level

    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get("https://cdn.mbta.com/realtime/VehiclePositions.pb", timeout=30)
    feed.ParseFromString(response.content)
