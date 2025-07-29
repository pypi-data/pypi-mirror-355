from database_mysql_local.generic_crud import GenericCRUD
from database_mysql_local.point import Point
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from user_context_remote.user_context import UserContext

from .location_local_constants import LocationLocalConstants
from .neighborhood_ml import NeighborhoodMl
from .util import LocationsUtil

logger = Logger.create_logger(
    object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()


class Neighborhood(GenericCRUD):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init Neighborhood")
        GenericCRUD.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.NEIGHBORHOOD_TABLE_NAME,
            default_view_table_name=LocationLocalConstants.NEIGHBORHOOD_ML_VIEW_NAME,
            default_column_name=LocationLocalConstants.NEIGHBORHOOD_ID_COLUMN_NAME,
            is_test_data=is_test_data)

        self.neighborhood_ml = None

        logger.end("end init Neighborhood")

    # TODO: test this method
    def insert(self, *,  # noqa
               coordinate: Point, is_title_approved: bool = False, city_id: int = None,
               neighborhood: str, lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE,
               group_id: int = None) -> int | None:
        logger.start("start insert neighborhood",
                     object={'coordinate': coordinate,
                             'neighborhood': neighborhood,
                             'lang_code': lang_code,
                             'is_title_approved': is_title_approved,
                             'city_id': city_id,
                             'group_id': group_id})
        is_valid = LocationsUtil.validate_insert_args(
            name=neighborhood, lang_code=lang_code, is_title_approved=is_title_approved, coordinate=coordinate)
        if not is_valid:
            logger.end(log_message="Neighborhood was not inserted because no neighborhood name was provided")
            return None
        lang_code = lang_code or user_context.get_effective_profile_preferred_lang_code()
        neighborhood_dict = {
            key: value for key, value in {
                'coordinate': coordinate,
                'city_id': city_id,
                'group_id': group_id
            }.items() if value is not None
        }
        neighborhood_id = super().insert(data_dict=neighborhood_dict, ignore_duplicate=True)

        self.neighborhood_ml = self.neighborhood_ml or NeighborhoodMl()
        neighborhood_ml_id = self.neighborhood_ml.insert(
            neighborhood=neighborhood, neighborhood_id=neighborhood_id,
            lang_code=lang_code, is_title_approved=is_title_approved)

        logger.end("end insert neighborhood",
                   object={'neighborhood_id': neighborhood_id,
                           'neighborhood_ml_id': neighborhood_ml_id})
        return neighborhood_id

    # TODO: test this method
    def read(self, location_id: int):
        logger.start("start read location",
                     object={'location_id': location_id})
        result = super().select_one_dict_by_column_and_value(
            column_value=location_id,
            select_clause_value=LocationLocalConstants.NEIGHBORHOOD_TABLE_COLUMNS)

        result = LocationsUtil.extract_coordinates_and_replace_by_point(
            data_dict=result)
        logger.end("end read location",
                   object={"result": result})
        return result

    def get_neighborhood_id_by_neighborhood_name(
            self, neighborhood_name: str, city_id: int = None,
            lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int | None:
        # TODO should return also the city_id if known
        logger.start("start get_neighborhood_id_by_neighborhood_name",
                     object={'neighborhood_name': neighborhood_name,
                             'city_id': city_id})
        if neighborhood_name is None:
            logger.end(log_message="end get_neighborhood_id_by_neighborhood_name",
                       object={'neighborhood_id': None})
            return None
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(neighborhood_name)
        where_clause = f"title='{neighborhood_name}' AND lang_code='{lang_code.value}'"
        if city_id is not None:
            where_clause += f" AND city_id={city_id}"

        self.neighborhood_ml = self.neighborhood_ml or NeighborhoodMl()
        neighborhood_id_dict = self.neighborhood_ml.select_one_dict_by_where(
            select_clause_value=LocationLocalConstants.NEIGHBORHOOD_ID_COLUMN_NAME,
            where=where_clause,
            order_by="neighborhood_id DESC")
        neighborhood_id = neighborhood_id_dict.get(
            LocationLocalConstants.NEIGHBORHOOD_ID_COLUMN_NAME)

        logger.end("end get_neighborhood_id_by_neighborhood_name",
                   object={'neighborhood_id': neighborhood_id})
        return neighborhood_id
