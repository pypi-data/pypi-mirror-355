from database_mysql_local.generic_crud_ml import GenericCRUDML
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from user_context_remote.user_context import UserContext

from .location_local_constants import LocationLocalConstants

logger = Logger.create_logger(
    object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()


class RegionMl(GenericCRUDML):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init RegionMl")
        GenericCRUDML.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.REGION_TABLE_NAME,
            default_ml_table_name=LocationLocalConstants.REGION_ML_TABLE_NAME,
            default_column_name=LocationLocalConstants.REGION_ML_ID_COLUMN_NAME,
            default_view_table_name=LocationLocalConstants.REGION_ML_VIEW_NAME,
            default_ml_view_table_name=LocationLocalConstants.REGION_ML_VIEW_NAME,
            default_view_with_deleted_and_test_data=LocationLocalConstants.REGION_ML_WITH_DELETED_AND_TEST_DATA_VIEW,
            is_test_data=is_test_data)
        logger.end("end init RegionMl")

    # TODO: test this method
    def insert(self, *,  # noqa
               region_id: int, region: str, is_title_approved: bool = None,
               lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int:
        logger.start("start insert region_ml",
                     object={'region_id': region_id,
                             'region': region,
                             'lang_code': lang_code,
                             'is_title_approved': is_title_approved})
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(region)
        region_ml_dict = {
            key: value for key, value in {
                'region_id': region_id,
                'lang_code': lang_code.value,
                'title': region,
                'is_title_approved': is_title_approved
            }.items() if value is not None
        }
        region_ml_id = super().insert(
            table_name=LocationLocalConstants.REGION_ML_TABLE_NAME,
            data_dict=region_ml_dict, ignore_duplicate=True)
        logger.end("end insert region_ml",
                   object={'region_ml_id': region_ml_id})

        return region_ml_id

    def upsert_value(self, data_dict: dict, order_by: str = "") -> dict:
        logger.start("start upsert_value region_ml",
                     object={'region_data_dict': data_dict,
                             'order_by': order_by})
        lang_code = LangCode.detect_lang_code_restricted(text=data_dict['title'],
                                                         default_lang_code=LangCode.ENGLISH)
        region_data_dict = {
            'coordinate': data_dict.get('coordinate'),
            'country_id': data_dict.get('country_id'),
            'name': data_dict.get('name') or data_dict.get('title'),
            'group_id': data_dict.get('group_id'),
        }

        region_ml_data_dict = {
            'title': data_dict.get('title') or data_dict.get('name'),
            'is_title_approved': data_dict.get('is_title_approved', None),
        }

        region_id, region_ml_id = super().upsert_value(
            data_ml_dict=region_ml_data_dict,
            data_dict=region_data_dict,
            lang_code=lang_code,
            table_name=LocationLocalConstants.REGION_TABLE_NAME,
            ml_table_name=LocationLocalConstants.REGION_ML_TABLE_NAME,
            is_main=None,
            order_by=order_by
        )

        result_dict = {
            'region_id': region_id,
            'region_ml_id': region_ml_id
        }
        logger.end("end upsert_value region_ml",
                   object={'result_dict': result_dict})
        return result_dict
