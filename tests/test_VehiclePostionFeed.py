from transitfeedhub_ingestor.helpers.VehiclePositionFeed import VehiclePositionFeed


def test_vehiclepositionfeed():
    feed_url: str = "https://cdn.mbta.com/realtime/VehiclePositions.pb"
    agency_name: str = "MBTA"
    file_path: str = "/MBTA"
    s3_bucketname: str = "TestBucket"
    VPFeed = VehiclePositionFeed(url=feed_url, agency=agency_name, file_path=file_path, s3_bucket=s3_bucketname)

    assert VPFeed.url == feed_url
    assert VPFeed.agency == agency_name
    assert VPFeed.file_path == file_path
    assert VPFeed.entities == []
    assert VPFeed.headers is None
    assert VPFeed.query_params is None
    assert VPFeed.s3_bucket == s3_bucketname
    assert VPFeed.https_verify is True
    assert VPFeed.timeout == 30


def test_vehiclepositionfeed_find_entity_doesntexist():
    feed_url: str = "https://cdn.mbta.com/realtime/VehiclePositions.pb"
    agency_name: str = "MBTA"
    file_path: str = "/MBTA"
    s3_bucketname: str = "TestBucket"
    VPFeed = VehiclePositionFeed(url=feed_url, agency=agency_name, file_path=file_path, s3_bucket=s3_bucketname)
    assert VPFeed.find_entity("y187") is None


def test_vehiclepositionfeed_updatetimeout():
    feed_url: str = "https://cdn.mbta.com/realtime/VehiclePositions.pb"
    agency_name: str = "MBTA"
    file_path: str = "/MBTA"
    s3_bucketname: str = "TestBucket"
    VPFeed = VehiclePositionFeed(url=feed_url, agency=agency_name, file_path=file_path, s3_bucket=s3_bucketname)

    VPFeed.updatetimeout(45)
    assert VPFeed.timeout == 45
