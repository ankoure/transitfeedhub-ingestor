import requests

from transitfeedhub_ingestor.helpers.Entity import Carriage
from transitfeedhub_ingestor.protobuf import gtfs_realtime_pb2


def test_carriage():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get("https://cdn.mbta.com/realtime/VehiclePositions.pb", timeout=30)
    feed.ParseFromString(response.content)

    green_line: list[object] = []

    for entity in feed.entity:
        if entity.HasField("vehicle"):
            vehicle = entity.vehicle
            if vehicle.HasField("vehicle"):
                vehicle_multi_carriage_details = vehicle.multi_carriage_details
                if len(vehicle_multi_carriage_details) > 0:
                    green_line.append(vehicle_multi_carriage_details)

    carriage_details = green_line[0][0]
    print(carriage_details)
    carriage = Carriage(carriage_details)
    assert carriage.label == carriage_details.label
    assert carriage.carriage_sequence == carriage_details.carriage_sequence
    assert carriage.occupancy_status == [carriage_details.occupancy_status]
    new_carriage_details: object = green_line[1][1]
    carriage.Update(new_carriage_details)
    assert carriage.occupancy_status != [carriage_details.occupancy_status]
    assert carriage.occupancy_status == [carriage_details.occupancy_status, new_carriage_details.occupancy_status]
