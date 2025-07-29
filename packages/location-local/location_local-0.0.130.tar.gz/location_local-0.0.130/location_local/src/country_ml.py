from database_mysql_local.generic_crud_ml import GenericCRUDML
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from user_context_remote.user_context import UserContext

from .location_local_constants import LocationLocalConstants

logger = Logger.create_logger(object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()


class CountryMl(GenericCRUDML):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init CountryMl")
        GenericCRUDML.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.COUNTRY_TABLE_NAME,
            default_column_name=LocationLocalConstants.COUNTRY_ML_ID_COLUMN_NAME,
            default_view_table_name=LocationLocalConstants.COUNTRY_ML_VIEW_NAME,
            default_ml_view_table_name=LocationLocalConstants.COUNTRY_ML_VIEW_NAME,
            is_test_data=is_test_data)
        logger.end("end init CountryMl")

    # TODO: test this method
    def insert(self, *,  # noqa
               country_id: int, country: str, is_title_approved: bool = None,
               lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int:
        logger.start("start insert country_ml",
                     object={'country_id': country_id, 'country': country,
                             'lang_code': lang_code,
                             'is_title_approved': is_title_approved})
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(country)
        country_ml_dict = {
            'country_id': country_id,
            'lang_code': lang_code.value,
            'title': country,
            'is_title_approved': is_title_approved
        }
        country_ml_id = super().insert(
            table_name=LocationLocalConstants.COUNTRY_ML_TABLE_NAME,
            data_dict=country_ml_dict, ignore_duplicate=True)
        logger.end("end insert country_ml",
                   object={'country_ml_id': country_ml_id})

        return country_ml_id
