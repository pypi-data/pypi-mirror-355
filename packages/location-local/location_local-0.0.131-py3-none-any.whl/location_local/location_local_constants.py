from database_mysql_local.point import Point
from language_remote.lang_code import LangCode
from logger_local.LoggerComponentEnum import LoggerComponentEnum


class LocationLocalConstants:
    LOCATION_LOCAL_PYTHON_PACKAGE_COMPONENT_ID = 113
    LOCATION_LOCAL_PYTHON_PACKAGE_COMPONENT_NAME = 'location local python package'
    OBJECT_FOR_LOGGER_CODE = {
        'component_id': LOCATION_LOCAL_PYTHON_PACKAGE_COMPONENT_ID,
        'component_name': LOCATION_LOCAL_PYTHON_PACKAGE_COMPONENT_NAME,
        'component_category': LoggerComponentEnum.ComponentCategory.Code.value,
        'developer_email': 'tal.g@circ.zone'
    }

    OBJECT_FOR_LOGGER_TEST = {
        'component_id': LOCATION_LOCAL_PYTHON_PACKAGE_COMPONENT_ID,
        'component_name': LOCATION_LOCAL_PYTHON_PACKAGE_COMPONENT_NAME,
        'component_category': LoggerComponentEnum.ComponentCategory.Unit_Test.value,
        'developer_email': 'tal.g@circ.zone'
    }

    DEFAULT_LANG_CODE = LangCode.ENGLISH
    UNKNOWN_LOCATION_ID = 0
    DEFAULT_NEGIHBORHOOD_NAME = None
    DEFAULT_COUNTY_NAME = None
    DEFAULT_REGION_NAME = None
    DEFAULT_STATE_NAME = 'UNKNOWN'  # not null
    DEFAULT_COUNTRY_NAME = 'UNKNOWN'  # Cannot be None, `name` is an index
    DEFAULT_ADDRESS_LOCAL_LANGUAGE = None
    DEFAULT_ADDRESS_ENGLISH = None
    DEFAULT_POSTAL_CODE = None
    DEFAULT_PHONECODE = None
    # TODO Change the DEFAULT_COORDINATE to something real (i.e. Rishon Startup)
    DEFAULT_COORDINATE = Point(0, 0)
    LOCATION_SCHEMA_NAME = 'location'
    LOCATION_TABLE_NAME = 'location_table'
    LOCATION_VIEW_NAME = 'location_view'
    LOCATION_ID_COLUMN_NAME = 'location_id'
    COUNTRY_TABLE_NAME = 'country_table'
    COUNTRY_ID_COLUMN_NAME = 'country_id'
    COUNTRY_ML_TABLE_NAME = 'country_ml_table'
    COUNTRY_ML_VIEW_NAME = 'country_ml_view'
    COUNTRY_ML_ID_COLUMN_NAME = 'country_ml_id'
    COUNTY_TABLE_NAME = 'county_table'
    COUNTY_ID_COLUMN_NAME = 'county_id'
    COUNTY_ML_TABLE_NAME = 'county_ml_table'
    COUNTY_ML_VIEW_NAME = 'county_ml_view'
    COUNTY_ML_WITH_DELETED_AND_TEST_DATA_VIEW = 'county_ml_with_deleted_and_test_data_view'
    COUNTY_ML_ID_COLUMN_NAME = 'county_ml_id'
    NEIGHBORHOOD_TABLE_NAME = 'neighborhood_table'
    NEIGHBORHOOD_ID_COLUMN_NAME = 'neighborhood_id'
    NEIGHBORHOOD_ML_TABLE_NAME = 'neighborhood_ml_table'
    NEIGHBORHOOD_ML_VIEW_NAME = 'neighborhood_ml_view'
    NEIGHBORHOOD_ML_WITH_DELETED_AND_TEST_DATA_VIEW = 'neighborhood_ml_with_deleted_and_test_data_view'
    NEIGHBORHOOD_ML_ID_COLUMN_NAME = 'neighborhood_ml_id'
    REGION_TABLE_NAME = 'region_table'
    REGION_ID_COLUMN_NAME = 'region_id'
    REGION_ML_TABLE_NAME = 'region_ml_table'
    REGION_ML_VIEW_NAME = 'region_ml_view'
    REGION_ML_WITH_DELETED_AND_TEST_DATA_VIEW = 'region_ml_with_deleted_and_test_data_view'
    REGION_ML_ID_COLUMN_NAME = 'region_ml_id'
    STATE_TABLE_NAME = 'state_table'
    STATE_ID_COLUMN_NAME = 'state_id'
    STATE_ML_TABLE_NAME = 'state_ml_table'
    STATE_ML_VIEW_NAME = 'state_ml_view'
    STATE_ML_ID_COLUMN_NAME = 'state_ml_id'
    CITY_TABLE_NAME = 'city_table'
    CITY_ID_COLUMN_NAME = 'city_id'
    CITY_ML_TABLE_NAME = 'city_ml_table'
    CITY_ML_VIEW_NAME = 'city_ml_view'
    CITY_ML_ID_COLUMN_NAME = 'city_ml_id'
    DEFAULT_POINT_COLUMN_NAME = 'coordinate'

    # TODO: I think we have to delete created_timestamp,
    #                            created_user_id, updated_timestamp,
    #                            updated_user_id, start_timestamp,
    #                            end_timestamp
    # from the following columns
    LOCATION_TABLE_COLUMNS = '''location_id, ST_X(coordinate),
                                ST_Y(coordinate), address_local_language,
                                address_english, neighborhood_id, city_id,
                                county_id, region_id, state_id, country_id,
                                postal_code, phonecode, is_approved,
                                is_community_active, created_timestamp,
                                created_user_id, updated_timestamp,
                                updated_user_id, start_timestamp,
                                end_timestamp'''

    CITY_TABLE_COLUMNS = '''city_id, ST_X(coordinate), ST_Y(coordinate),
                            name, phonecode, group_id, created_timestamp,
                            created_user_id, updated_timestamp,
                            updated_user_id, new_city_id, country_id'''

    COUNTRY_TABLE_COLUMNS = '''country_id, ST_X(coordinate), ST_Y(coordinate),
                               iso, name, nicename, iso3, numcode, phonecode,
                               group_id, created_timestamp, created_user_id,
                               updated_timestamp, updated_user_id'''

    COUNTY_TABLE_COLUMNS = '''county_id, ST_X(coordinate), ST_Y(coordinate),
                              group_id, created_timestamp, created_user_id,
                              updated_timestamp, updated_user_id'''

    NEIGHBORHOOD_TABLE_COLUMNS = '''neighborhood_id, city_id, ST_X(coordinate),
                                    ST_Y(coordinate), group_id,
                                    created_timestamp, created_user_id,
                                    updated_timestamp, updated_user_id'''

    REGION_TABLE_COLUMNS = '''region_id, country_id, ST_X(coordinate),
                              ST_Y(coordinate), group_id, created_timestamp,
                              created_user_id, updated_timestamp,
                              updated_user_id'''

    STATE_TABLE_COLUMNS = '''state_id, ST_X(coordinate), ST_Y(coordinate),
                             group_id, created_timestamp, created_user_id,
                             updated_timestamp, updated_user_id'''

    # TODO Move this to a separate file
    DOMAIN_TO_COUNTRY = {
        'uk': 'United Kingdom',
        'au': 'Australia',
        'fr': 'France',
        'de': 'Germany',
        'ca': 'Canada',
        'jp': 'Japan',
        'ru': 'Russia',
        'us': 'United States',
        'cn': 'China',
        'it': 'Italy',
        'pl': 'Poland',
        'es': 'Spain',
        'za': 'South Africa',
        'br': 'Brazil',
        'se': 'Sweden',
        'no': 'Norway',
        'dk': 'Denmark',
        'fi': 'Finland',
        'nl': 'Netherlands',
        'il': 'Israel',
        'sg': 'Singapore',
        'mx': 'Mexico',
        'ar': 'Argentina',
        'cl': 'Chile',
        'in': 'India',
        'pt': 'Portugal',
        'th': 'Thailand',
        'nz': 'New Zealand',
        'ch': 'Switzerland',
        'at': 'Austria',
        'be': 'Belgium',
        'ie': 'Ireland',
        'kr': 'South Korea',
        'hk': 'Hong Kong',
        'my': 'Malaysia',
        'tw': 'Taiwan',
        'ae': 'United Arab Emirates'
        # More mappings can be added as necessary
    }
