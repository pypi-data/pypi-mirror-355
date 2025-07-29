from database_mysql_local.generic_crud_ml import GenericCRUDML
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from user_context_remote.user_context import UserContext

from .location_local_constants import LocationLocalConstants

logger = Logger.create_logger(
    object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()


# TODO: add method upsert_value, see an example in location-local-python-package\location_local\src\region_ml.py
class NeighborhoodMl(GenericCRUDML):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init NeighborhoodMl")
        GenericCRUDML.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.NEIGHBORHOOD_TABLE_NAME,
            default_column_name=LocationLocalConstants.NEIGHBORHOOD_ML_ID_COLUMN_NAME,
            default_view_table_name=LocationLocalConstants.NEIGHBORHOOD_ML_VIEW_NAME,
            default_view_with_deleted_and_test_data=LocationLocalConstants.NEIGHBORHOOD_ML_WITH_DELETED_AND_TEST_DATA_VIEW,
            default_ml_view_table_name=LocationLocalConstants.NEIGHBORHOOD_ML_VIEW_NAME,
            is_test_data=is_test_data)
        logger.end("end init NeighborhoodMl")

    # TODO: test this method
    def insert(self, *,  # noqa
               neighborhood_id: int, neighborhood: str, is_title_approved: bool = False,
               lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int:
        logger.start("start insert neighborhood_ml",
                     object={'neighborhood_id': neighborhood_id,
                             'neighborhood': neighborhood,
                             'lang_code': lang_code,
                             'is_title_approved': is_title_approved})
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(neighborhood)
        neighborhood_ml_dict = {
            key: value for key, value in {
                'neighborhood_id': neighborhood_id,
                'lang_code': lang_code.value,
                'title': neighborhood,
                'is_title_approved': is_title_approved
            }.items() if value is not None
        }
        # TODO Can we user CrudMl for all those insert()
        neighborhood_ml_id = super().insert(
            table_name=LocationLocalConstants.NEIGHBORHOOD_ML_TABLE_NAME,
            data_dict=neighborhood_ml_dict, ignore_duplicate=True)
        logger.end("end insert neighborhood_ml",
                   object={'neighborhood_ml_id': neighborhood_ml_id})

        return neighborhood_ml_id
