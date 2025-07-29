from database_mysql_local.generic_crud import GenericCRUD
from database_mysql_local.point import Point
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from user_context_remote.user_context import UserContext

from .location_local_constants import LocationLocalConstants
from .state_ml import StateMl
from .util import LocationsUtil

logger = Logger.create_logger(
    object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()


class State(GenericCRUD):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init State")

        GenericCRUD.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.STATE_TABLE_NAME,
            default_view_table_name=LocationLocalConstants.STATE_ML_VIEW_NAME,
            default_column_name=LocationLocalConstants.STATE_ID_COLUMN_NAME,
            is_test_data=is_test_data)

        self.state_ml = None
        logger.end("End init State")

    def insert(self, *,  # noqa
               coordinate: Point,
               state: str, lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE,
               is_title_approved: bool = None,
               group_id: int = None) -> int | None:
        logger.start("start insert state",
                     object={'coordinate': coordinate, 'state': state,
                             'lang_code': lang_code,
                             'is_title_approved': is_title_approved,
                             'group_id': group_id})
        is_valid = LocationsUtil.validate_insert_args(
            name=state, lang_code=lang_code, is_title_approved=is_title_approved, coordinate=coordinate)
        if not is_valid:
            logger.end(log_message="State was not inserted because no state name was provided")
            return None
        lang_code = lang_code or LangCode.detect_lang_code(state)
        state_dict = {
            key: value for key, value in {
                'coordinate': coordinate,
                'group_id': group_id
            }.items() if value is not None
        }

        state_id = super().insert(data_dict=state_dict, ignore_duplicate=True)

        self.state_ml = self.state_ml or StateMl()
        state_ml_id = self.state_ml.insert(state_id=state_id, state=state,
                                           lang_code=lang_code,
                                           is_title_approved=is_title_approved)

        logger.end("end insert state",
                   object={'state_id': state_id,
                           'state_ml_id': state_ml_id})
        return state_id

    # TODO: test this method
    def read(self, location_id: int):
        logger.start("start read location",
                     object={'location_id': location_id})
        result = super().select_one_dict_by_column_and_value(
            column_value=location_id,
            select_clause_value=LocationLocalConstants.STATE_TABLE_COLUMNS)
        result = LocationsUtil.extract_coordinates_and_replace_by_point(
            data_dict=result)
        logger.end("end read location",
                   object={"result": result})
        return result

    def get_state_id_by_state_name(self, state_name: str,
                                   lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int | None:
        logger.start("start get_state_id_by_state_name",
                     object={'state_name': state_name})
        if state_name is None:
            logger.end(log_message="State name was not provided",
                       object={'state_id': None})
            return None
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(state_name)
        where_clause = f"title='{state_name}' AND lang_code='{lang_code.value}'"

        self.state_ml = self.state_ml or StateMl()
        state_id_dict = self.state_ml.select_one_dict_by_where(
            select_clause_value=LocationLocalConstants.STATE_ID_COLUMN_NAME,
            where=where_clause,
            order_by="state_id DESC")
        state_id = state_id_dict.get(
            LocationLocalConstants.STATE_ID_COLUMN_NAME)

        logger.end("end get_state_id_by_state_name",
                   object={'state_ids': state_id})
        return state_id
