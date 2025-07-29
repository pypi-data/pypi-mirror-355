from typing import List

from database_mysql_local.generic_crud import GenericCRUD
from database_mysql_local.point import Point
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from user_context_remote.user_context import UserContext

from .city_ml import CityMl
from .location_local_constants import LocationLocalConstants
from .util import LocationsUtil

logger = Logger.create_logger(
    object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()


# TODO: migrate all classes to the meta logger
class City(GenericCRUD):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init City")

        GenericCRUD.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.CITY_TABLE_NAME,
            default_view_table_name=LocationLocalConstants.CITY_ML_VIEW_NAME,
            default_column_name=LocationLocalConstants.CITY_ID_COLUMN_NAME,
            is_test_data=is_test_data)
        self.city_ml = None

        logger.end("end init City")

    # TODO: test this method
    def insert(self, *,  # noqa
               city: str, state_id: int, lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE,
               is_title_approved: bool = None, coordinate: Point = None,
               # TODO group_id -> city_group_id
               group_id: int = None, phonecode: int = None,
               is_main: int = None) -> int | None:
        """A city can have multiple state_id
        https://www.cheapflights.com/news/seeing-double-us-cities-nice-used-name-twice"""
        logger.start("start insert city",
                     object={'coordinate': coordinate, 'city': city,
                             'lang_code': lang_code,
                             'state_id': state_id,
                             'is_title_approved': is_title_approved,
                             'is_main': is_main})
        is_valid = LocationsUtil.validate_insert_args(
            name=city, lang_code=lang_code, is_title_approved=is_title_approved, coordinate=coordinate)
        if not is_valid:
            logger.end(log_message="City was not inserted because no city name was provided")
            return None
        lang_code = lang_code or LangCode.detect_lang_code(city)
        city_dict = {
            key: value for key, value in {
                # TODO Can we add here country_id, region_id
                'coordinate': coordinate,
                'name': city,
                'state_id': state_id,
                'phonecode': phonecode,
                'group_id': group_id
                # TODO add city_ml: lang_code, title ...
            }.items() if value is not None
        }

        city_id = super().insert(data_dict=city_dict, ignore_duplicate=True)

        self.city_ml = self.city_ml or CityMl()
        city_ml_id = self.city_ml.insert(city_id=city_id,
                                         city=city,
                                         lang_code=lang_code,
                                         is_title_approved=is_title_approved,
                                         is_main=is_main)

        logger.end("end insert city",
                   object={'city_id': city_id,
                           'city_ml_id': city_ml_id})
        return city_id

    # TODO: test this method
    def read_by_location(self, location_id: int) -> dict:
        """Read city by location_id"""
        logger.start("start read city", object={'location_id': location_id})
        result = super().select_one_dict_by_column_and_value(
            column_value=location_id,
            select_clause_value=LocationLocalConstants.CITY_TABLE_COLUMNS)
        result = LocationsUtil.extract_coordinates_and_replace_by_point(
            data_dict=result)
        logger.end("end read location", object={"result": result})
        return result

    # TODO: test this method
    def read_by_location_and_state(self, location_id: int, state_id: int) -> List[dict]:
        logger.start("start read city", object={'location_id': location_id, 'state_id': state_id})
        result = self.select_multi_dict_by_where(
            where=f"{LocationLocalConstants.CITY_ID_COLUMN_NAME}={location_id} AND "
                  f"{LocationLocalConstants.STATE_ID_COLUMN_NAME}={state_id}",
            select_clause_value=LocationLocalConstants.CITY_TABLE_COLUMNS)
        result = [LocationsUtil.extract_coordinates_and_replace_by_point(data_dict=city) for city in result]
        logger.end("end read location", object={"result": result})
        return result

    # TODO: test this method
    def get_city_id_by_city_name(self, city_name: str,
                                 lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int | None:
        logger.start("start get_city_id_by_city_name_state_id",
                     object={'city_name': city_name})
        if city_name is None:
            logger.end(log_message="end get_city_id_by_city_name_state_id",
                       object={'city_id': None})
            return None
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(city_name)
        where_clause = "title=%s AND lang_code=%s"
        params = (city_name, lang_code.value)

        self.city_ml = self.city_ml or CityMl()
        city_id_dict = self.city_ml.select_one_dict_by_where(
            select_clause_value=LocationLocalConstants.CITY_ID_COLUMN_NAME,
            where=where_clause,
            params=params,
            order_by="city_id DESC")
        city_id = city_id_dict.get(LocationLocalConstants.CITY_ID_COLUMN_NAME)

        logger.end("end get_city_id_by_city_name_state_id", object={'city_id': city_id})
        return city_id
