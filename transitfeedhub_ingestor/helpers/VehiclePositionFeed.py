import datetime
from typing import Any

import requests
from google.protobuf.message import DecodeError

from transitfeedhub_ingestor.protobuf import gtfs_realtime_pb2

from .Entity import Entity
from .setup_logger import logger


class VehiclePositionFeed:
    def __init__(
        self,
        url: str,
        agency: str,
        file_path: str,
        s3_bucket: str,
        headers: None = None,
        query_params: None = None,
        https_verify: bool = True,
        timeout: int = 30,
    ):
        self.entities: list[Entity] = []
        self.url: str = url
        self.headers: Any = headers
        self.query_params: Any = query_params
        self.agency: str = agency
        self.file_path: str = file_path
        self.s3_bucket: str = s3_bucket
        self.https_verify: bool = https_verify
        self.timeout: int = timeout

    def find_entity(self, entity_id: str):
        return next((e for e in self.entities if e.entity_id == entity_id), None)

    def updatetimeout(self, timeout: int):
        self.timeout = timeout

    def get_entities(self) -> list[gtfs_realtime_pb2.VehiclePosition] | None:
        feed = None
        try:
            feed = gtfs_realtime_pb2.FeedMessage()
            # TODO: add From and User Agent Headers
            # headers = {
            #     'User-Agent': 'Your App Name/1.0',
            #     'From': 'your_email@example.com'
            # }

            response = requests.get(
                self.url, headers=self.headers, params=self.query_params, verify=self.https_verify, timeout=300
            )

            feed.ParseFromString(response.content)
        except DecodeError as e:
            logger.warning(f"protobuf decode error for {self.url}, {e}")
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for {self.url}")
            # Maybe set up for a retry, or continue in a retry loop
        except requests.exceptions.TooManyRedirects:
            logger.warning(f"Too Many Redirects for {self.url}")
        except requests.exceptions.SSLError:
            logger.warning(f"SSL Error for {self.url}")
        except requests.exceptions.RequestException as e:
            # catastrophic error. bail.
            raise SystemExit(e) from e

        except Exception as e:
            # TODO: update to be more fine-grained in future
            self.updatetimeout(300)
            logger.exception(e)

        feed_entities: list[gtfs_realtime_pb2.VehiclePosition] = []
        if feed:
            # Returns list of feed entities
            try:
                feed_entities: list[gtfs_realtime_pb2.VehiclePosition] = [
                    e.vehicle for e in feed.entity if e.HasField("vehicle")
                ]
            except Exception as e:
                logger.info(f"message does not have vehicle field {e}")

        return feed_entities

    def check_if_empty_protobuf(self, feed_entities: list[gtfs_realtime_pb2.VehiclePosition]) -> bool:
        """Checks if there are any vehicles in the protobuf. If none, it logs a warning, this can be helpful to determine the operating hours of a feed.

        Args:
            feed_entities: A list of GTFS Realtime Binding Vehicle Positions

        Returns:
            Returns boolean representing whether or not there is data.
        """
        if len(feed_entities) == 0:
            logger.warning(f"Empty Protobuf file for {self.url}")
            return True
        else:
            return False

    def check_for_existing_entities(self, feed_entities: list[gtfs_realtime_pb2.VehiclePosition]) -> bool:
        if len(self.entities) == 0:
            # check if any observations exist, if none create all new objects
            for feed_entity in feed_entities:
                entity = Entity(feed_entity)
                self.entities.append(entity)
            return True
        else:
            return False

    def compare_current_ids_to_new_ids(
        self, feed_entities: list[gtfs_realtime_pb2.VehiclePosition]
    ) -> tuple[set[str], set[str], set[str]]:
        entity_ids_of_entity_objects: set[str] = {e.entity_id for e in self.entities}
        entity_ids_in_feed: set[str] = {feed_entity.vehicle.id for feed_entity in feed_entities}
        """Determines which ids need to be created, updated, or deleted (saved).

        This function takes

        Args:
            feed_entities: A list of GTFS Realtime Binding Vehicle Positions

        Returns:
            Returns tuple of three sets representing the ids to create, updated and remove. The order of returning is: entity_ids_to_create, entity_ids_to_update, entity_ids_to_remove.
        """

        # I am in the feed, and I have a corresponding object. Update me!
        entity_ids_to_update = entity_ids_in_feed.intersection(entity_ids_of_entity_objects)
        # I am in the feed but don't have a corresponding object. Create me!
        entity_ids_to_create = (
            entity_ids_in_feed - entity_ids_of_entity_objects
        )  # Set difference return ids in left that are not in right
        # I don't have an id in the feed but I have a corresponding object. Remove me!
        entity_ids_to_remove = (
            entity_ids_of_entity_objects - entity_ids_in_feed
        )  # Set difference return ids in left that are not in right

        return (entity_ids_to_create, entity_ids_to_update, entity_ids_to_remove)

    # check if new direction and old direction are same
    # check if last updated date is equivalent to new date, to prevent duplication

    def save_entity_to_s3(self, entity: Entity):
        if len(entity.updated_at) > 1:
            now = datetime.datetime.now()
            strf_rep = now.strftime("%Y%m%d")
            entity.savetos3(
                self.s3_bucket,
                f"{self.agency}/{strf_rep}/{entity.route_id}",
            )
            logger.debug(f"Saving entity {entity.entity_id} | {self.file_path}")
        # remove from list
        self.entities.remove(entity)

    def consume_pb(self):
        feed_entities = self.get_entities()
        if (
            feed_entities
            and self.check_if_empty_protobuf(feed_entities) is False
            and self.check_for_existing_entities(feed_entities) is False
        ):
            entity_ids_to_create, entity_ids_to_update, entity_ids_to_remove = self.compare_current_ids_to_new_ids(
                feed_entities
            )

            for entity_id in entity_ids_to_create:
                # return vehicle position class, matching by id
                feed_ent = next((e for e in feed_entities if e.vehicle.id == entity_id), None)
                if feed_ent:
                    entity = Entity(feed_ent)
                    self.entities.append(entity)

            for entity_id in entity_ids_to_update:
                update_feed_ent = next((e for e in feed_entities if e.vehicle.id == entity_id), None)
                update_entity = self.find_entity(entity_id)
                if (
                    update_feed_ent
                    and update_entity
                    and update_entity.updated_at[-1]
                    != datetime.datetime.fromtimestamp(update_feed_ent.timestamp).isoformat()
                ):
                    # check if direction changed
                    if update_entity.direction_id == update_feed_ent.trip.direction_id:
                        # if directions are same and not same timestamp update data
                        update_entity.update(update_feed_ent)
                    else:
                        # if direction id changed and timestamp is new. Save out old and create new.
                        self.save_entity_to_s3(update_entity)
                        entity = Entity(update_feed_ent)
                        self.entities.append(entity)

            for entity_id in entity_ids_to_remove:
                # move logic onto object
                entity = self.find_entity(entity_id)
                if entity:
                    # call save method
                    self.save_entity_to_s3(entity)
