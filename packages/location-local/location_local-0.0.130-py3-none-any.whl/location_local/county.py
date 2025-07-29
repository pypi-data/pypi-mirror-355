from typing import List

from database_mysql_local.generic_crud import GenericCRUD
from database_mysql_local.point import Point
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from user_context_remote.user_context import UserContext

from .county_ml import CountyMl
from .location_local_constants import LocationLocalConstants
from .util import LocationsUtil

logger = Logger.create_logger(
    object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()


class County(GenericCRUD):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init County")

        GenericCRUD.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.COUNTY_TABLE_NAME,
            default_view_table_name=LocationLocalConstants.COUNTY_ML_VIEW_NAME,
            default_column_name=LocationLocalConstants.COUNTY_ID_COLUMN_NAME,
            is_test_data=is_test_data
        )

        self.county_ml = None

        logger.end("end init County")

    # TODO: test this method
    def insert(self, *,  # noqa
               county: str, state_id: int, lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE,
               is_title_approved: bool = None, coordinate: Point = None,
               group_id: int = None) -> int | None:
        logger.start("start insert county",
                     object={'coordinate': coordinate, 'county': county,
                             'lang_code': lang_code, 'state_id': state_id,
                             'is_title_approved': is_title_approved})
        is_valid = LocationsUtil.validate_insert_args(
            name=county, lang_code=lang_code, is_title_approved=is_title_approved, coordinate=coordinate)
        if not is_valid:
            logger.end(log_message="County was not inserted because no county name was provided")
            return None
        lang_code = lang_code or user_context.get_effective_profile_preferred_lang_code()
        county_dict = {'coordinate': coordinate,
                       'group_id': group_id,
                       'state_id': state_id}

        county_id = super().insert(data_dict=county_dict, ignore_duplicate=True)

        self.county_ml = self.county_ml or CountyMl()
        county_ml_id = self.county_ml.insert(county_id=county_id,
                                             county=county,
                                             lang_code=lang_code,
                                             is_title_approved=is_title_approved)

        logger.end("end insert county",
                   object={'county_id': county_id,
                           'county_ml_id': county_ml_id})
        return county_id

    # TODO: test this method
    # TODO read or get? - What is our standard (I think get)?
    # TODO get_location_dict_by_location_id(...) - We might have Location in the future.
    def read_by_location(self, location_id: int) -> dict:
        logger.start("start read location", object={'location_id': location_id})
        result = super().select_one_dict_by_column_and_value(
            column_value=location_id,
            select_clause_value=LocationLocalConstants.COUNTY_TABLE_COLUMNS)

        result = LocationsUtil.extract_coordinates_and_replace_by_point(
            data_dict=result)

        logger.end("end read location", object={"result": result})
        return result

    # TODO: test this method
    def read_by_location_and_state(self, location_id: int, state_id: int) -> List[dict]:
        logger.start("start read location", object={'location_id': location_id})
        result = self.select_multi_dict_by_where(
            where=f"{LocationLocalConstants.LOCATION_ID_COLUMN_NAME}={location_id} AND "
                  f"{LocationLocalConstants.STATE_ID_COLUMN_NAME}={state_id}",
            select_clause_value=LocationLocalConstants.COUNTY_TABLE_COLUMNS)

        result = [LocationsUtil.extract_coordinates_and_replace_by_point(data_dict=county) for county in result]

        logger.end("end read location", object={"result": result})
        return result

    def get_county_id_by_county_name_state_id(
            self, *, county_name: str, state_id: int = None,
            lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int | None:
        logger.start("start get_county_id_by_county_name_state_id",
                     object={'county_name': county_name, 'state_id': state_id})
        if county_name is None:
            logger.end(log_message="end get_county_id_by_county_name_state_id",
                       object={'county_id': None})
            return None
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(county_name)
        where_clause = f"title='{county_name}' AND lang_code='{lang_code.value}'"
        if state_id is not None:
            where_clause += f" AND state_id={state_id}"

        self.county_ml = self.county_ml or CountyMl()
        county_id_dict = self.county_ml.select_one_dict_by_where(
            select_clause_value=LocationLocalConstants.COUNTY_ID_COLUMN_NAME,
            where=where_clause,
            order_by="county_id DESC")
        # TODO logger.info(country_id_dict)
        # TODO Error handing, what happen if we don't have location, we should catch and raise specific exception
        county_id = county_id_dict.get(
            LocationLocalConstants.COUNTY_ID_COLUMN_NAME)

        logger.end("end get_county_id_by_county_name_state_id", object={'county_id': county_id})
        return county_id
