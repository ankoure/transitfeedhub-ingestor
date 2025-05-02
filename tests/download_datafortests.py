import datetime
import time

import requests

i: int = 1
while i < 120:
    r = requests.get("https://cdn.mbta.com/realtime/VehiclePositions.pb", timeout=30)
    now = datetime.datetime.now()
    with open(f"tests/mockapi_data/VehiclePositions_{now}.pb", "wb") as f:
        f.write(r.content)
    i += 1
    time.sleep(30)
