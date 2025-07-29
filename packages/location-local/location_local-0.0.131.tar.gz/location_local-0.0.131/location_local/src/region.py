from database_mysql_local.generic_crud import GenericCRUD
from database_mysql_local.point import Point
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from user_context_remote.user_context import UserContext

from .location_local_constants import LocationLocalConstants
from .region_ml import RegionMl
from .util import LocationsUtil

logger = Logger.create_logger(
    object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()


class Region(GenericCRUD):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init Region")
        GenericCRUD.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.REGION_TABLE_NAME,
            default_view_table_name=LocationLocalConstants.REGION_ML_VIEW_NAME,
            default_column_name=LocationLocalConstants.REGION_ID_COLUMN_NAME,
            is_test_data=is_test_data
        )

        self.region_ml = None

        logger.end("end init Region")

    # TODO: test this method
    def insert(  # noqa
            self, *, coordinate: Point,
            region: str, lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE,
            is_title_approved: bool = None,
            country_id: int = None, group_id: int = None) -> int | None:
        logger.start("start insert Region",
                     object={'coordinate': coordinate, 'region': region,
                             'lang_code': lang_code,
                             'is_title_approved': is_title_approved,
                             'country_id': country_id, 'group_id': group_id})
        is_valid = LocationsUtil.validate_insert_args(
            name=region, lang_code=lang_code, is_title_approved=is_title_approved, coordinate=coordinate)
        if not is_valid:
            logger.end(log_message="Region was not inserted because no region name was provided")
            return None
        lang_code = lang_code or user_context.get_effective_profile_preferred_lang_code()
        region_dict = {
            key: value for key, value in {
                'coordinate': coordinate,
                'country_id': country_id,
                'group_id': group_id
            }.items() if value is not None
        }

        region_id = super().insert(data_dict=region_dict, ignore_duplicate=True)

        self.region_ml = self.region_ml or RegionMl()
        region_ml_id = self.region_ml.insert(region_id=region_id,
                                             region=region,
                                             lang_code=lang_code,
                                             is_title_approved=is_title_approved)

        logger.end("end insert region",
                   object={'region_id': region_id,
                           'region_ml_id': region_ml_id})
        return region_id

    # TODO: test this method
    def read(self, location_id: int):
        logger.start("start read location",
                     object={'location_id': location_id})
        result = super().select_one_dict_by_column_and_value(
            column_value=location_id,
            select_clause_value=LocationLocalConstants.REGION_TABLE_COLUMNS)
        result = LocationsUtil.extract_coordinates_and_replace_by_point(
            data_dict=result)
        logger.end("end read location",
                   object={"result": result})
        return result

    def get_region_id_by_region_name(self, region_name: str, country_id: int = None,
                                     lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int | None:
        logger.start("start get_region_id_by_region_name",
                     object={'region_name': region_name,
                             'country_id': country_id})
        if region_name is None:
            logger.end(log_message="end get_region_id_by_region_name",
                       object={'region_id': None})
            return None
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(region_name)
        where_clause = f"title='{region_name}' AND lang_code='{lang_code.value}'"
        if country_id is not None:
            where_clause += f" AND country_id={country_id}"

        self.region_ml = self.region_ml or RegionMl()
        region_id_dict = self.region_ml.select_one_dict_by_where(
            select_clause_value=LocationLocalConstants.REGION_ID_COLUMN_NAME,
            where=where_clause,
            order_by="region_id DESC")
        region_id = region_id_dict.get(
            LocationLocalConstants.REGION_ID_COLUMN_NAME)

        logger.end("end get_region_id_by_region_name",
                   object={'region_id': region_id})
        return region_id
