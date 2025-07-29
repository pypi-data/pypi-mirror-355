from typing import Dict

from database_mysql_local.generic_crud import GenericCRUD
from database_mysql_local.point import Point
from language_remote.lang_code import LangCode
from logger_local.LoggerLocal import Logger
from opencage.geocoder import OpenCageGeocode
from phonenumbers import geocoder as phonenumbers_geocoder
from phonenumbers import parse
from python_sdk_remote.utilities import our_get_env
from user_context_remote.user_context import UserContext

from .country_ml import CountryMl
from .location_local_constants import LocationLocalConstants
from .util import LocationsUtil

logger = Logger.create_logger(
    object=LocationLocalConstants.OBJECT_FOR_LOGGER_CODE)
user_context = UserContext()

# TODO We should write inheriance to implement geocoder in diffrent technologies (Opencage, Google ...)
# TODO If geocoder can be used outside of country.py, think we should move OPENCAGE_API_KEY_NAME to location_local_constants.py
OPENCAGE_API_KEY_NAME = "OPENCAGE_KEY"
# TODO Change variable name to OPENCAGE_API_KEY everythere and make sure all GHA are fully Green
# OPENCAGE_API_KEY_NAME = "OPENCAGE_API_KEY"


# TODO Can we use GenericMl
class CountriesLocal(GenericCRUD):
    def __init__(self, is_test_data: bool = False):
        logger.start("start init Country")

        GenericCRUD.__init__(
            self,
            default_schema_name=LocationLocalConstants.LOCATION_SCHEMA_NAME,
            default_table_name=LocationLocalConstants.COUNTRY_TABLE_NAME,
            default_view_table_name=LocationLocalConstants.COUNTRY_ML_VIEW_NAME,
            default_column_name=LocationLocalConstants.COUNTRY_ID_COLUMN_NAME,
            is_test_data=is_test_data)
        self.country_ml = None
        opencage_api_key = our_get_env(OPENCAGE_API_KEY_NAME, raise_if_empty=False, raise_if_not_found=False)

        if opencage_api_key is None:
            logger.info("location-main-local-python-package ContriesLocal.__init__ OPENCAGE_API_KEY_NAME is None")
            self.open_cage_geocoder = None
        else:
            # I think the try is not mandatory
            try:
                self.open_cage_geocoder = OpenCageGeocode(opencage_api_key)
            except Exception as e:
                self.open_cage_geocoder = None
                logger.error("location-main-local-python-package ContriesLocal.__init__ Can't create self.geocoder")
                logger.exception(e)

        logger.end("end init Country")

    # TODO: test this method
    def insert(self, *, country: str,  # noqa
               lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE,
               is_title_approved: bool = None,
               new_country_data: Dict[str, any] = None,
               coordinate: Point = None, ignore_duplicate: bool = False) -> int | None:
        logger.start("start insert country",
                     object={'coordinate': coordinate, 'country': country,
                             'lang_code': lang_code,
                             'is_title_approved': is_title_approved,
                             'new_country_data': new_country_data})
        is_valid = LocationsUtil.validate_insert_args(
            name=country, lang_code=lang_code, is_title_approved=is_title_approved, coordinate=coordinate)
        if not is_valid:
            logger.end(log_message="Country was not inserted because no country name was provided")
            return None
        lang_code = lang_code or LangCode.detect_lang_code(country)
        new_country_data = new_country_data or {}
        try:
            country_dict = {
                key: value for key, value in {
                    'coordinate': coordinate,
                    'iso': new_country_data.get("iso"),
                    'name': country,
                    'nicename': new_country_data.get("nicename"),
                    'iso3': new_country_data.get("iso3"),
                    'numcode': new_country_data.get("numcode"),
                    'phonecode': new_country_data.get("phonecode")
                }.items() if value is not None
            }
            # TODO Can we use GenericMl
            country_id = super().insert(data_dict=country_dict, ignore_duplicate=ignore_duplicate)

        except Exception as e:
            logger.exception("error in insert country")
            logger.end()
            raise e
        try:
            self.country_ml = self.country_ml or CountryMl()
            country_ml_id = self.country_ml.insert(
                country=country,
                country_id=country_id,
                lang_code=lang_code,
                is_title_approved=is_title_approved)
        # TODO Replace e with exception everywhere
        except Exception as e:
            logger.exception("error in insert country")
            logger.end()
            raise e
        logger.end("end insert country",
                   object={'country_id': country_id,
                           'country_ml_id': country_ml_id})
        return country_id

    # TODO: test this method
    # TODO: the read function is duplicated in all classes
    def read(self, location_id: int) -> dict:
        logger.start("start read location",
                     object={'location_id': location_id})
        result = super().select_one_dict_by_column_and_value(
            column_value=location_id,
            select_clause_value=LocationLocalConstants.COUNTRY_TABLE_COLUMNS)

        result = LocationsUtil.extract_coordinates_and_replace_by_point(
            data_dict=result)
        logger.end("end read location",
                   object={"result": result})
        return result

    def get_country_id_by_country_name(self, country_name: str,
                                       lang_code: LangCode = LocationLocalConstants.DEFAULT_LANG_CODE) -> int | None:
        logger.start("start get_country_id_by_country_name",
                     object={'country_name': country_name})
        if country_name is None:
            logger.end(log_message="end get_country_id_by_country_name",
                       object={'country_id': None})
            return None
        LangCode.validate(lang_code)
        lang_code = lang_code or LangCode.detect_lang_code(country_name)
        where_clause = f"title='{country_name}' AND lang_code='{lang_code.value}'"

        self.country_ml = self.country_ml or CountryMl()
        country_id_dict = self.country_ml.select_one_dict_by_where(
            select_clause_value=LocationLocalConstants.COUNTRY_ID_COLUMN_NAME,
            where=where_clause,
            order_by="country_id DESC")
        country_id = country_id_dict.get(LocationLocalConstants.COUNTRY_ID_COLUMN_NAME)

        logger.end("end get_country_id_by_country_name",
                   object={'country_id': country_id})
        return country_id

    # TODO Rename to get_country_name_by_address() and add get_country_name() which calls get_country_name_by_address() for backward compatability
    def get_country_name(self, location: str) -> str:
        # Create a geocoder instance
        logger.start("start get_country_name",
                     object={'location': location})

        # Define the city or state
        # TODO Please create new class GeoCode and GeoCodeOpenCage Class which interit from GeoCode Class.
        # Please move those calls to the GeoCodeOpenCage.geocode(location).
        # TODO Please add calls to ApiManagement Indirect from GeoCode class

        # Use geocoding to get the location details (using OPENCAGE)
        # I think the if is not mandatory
        if self.open_cage_geocoder:
            # geocoder.geocode(location) can cause NotAuthorizedError exception with message "Your API key is not authorized. You may have entered it incorrectly."  # noqa
            try:
                results = self.open_cage_geocoder.geocode(location)
            except Exception as e:
                results = None
                logger.error("location-main-local-python-package CountriesLocal get_country_name() geocoder.geocode(location) raised exception")
                logger.error(f"exception: {e}")
                return results

            if results and len(results) > 0:
                first_result = results[0]
                components = first_result['components']

                # Extract the country from components
                country_name = components.get('country', '')
                if not country_name:
                    # If country is not found, check for country_code
                    # as an alternative
                    country_name = components.get('country_code', '')
            else:
                country_name = None
                logger.error("country didnt  found for %s." % location)
            logger.end("end get_country_name",
                       object={'country_name': country_name})
        else:
            country_name = None

        return country_name

    @staticmethod
    # This method is not using the database therefore it is static
    def get_country_name_by_phone_number(phone_number: str) -> str:
        logger.start("start get_country_name_by_phone_number",
                     object={'phone_number': phone_number})
        # Parse the phone number
        parsed_number = parse(phone_number)
        # Get the country from the phone number
        country_name = phonenumbers_geocoder.country_name_for_number(parsed_number, 'en')
        if country_name == '' and phone_number.startswith('+1'):
            # Default to United States if the country is not found and the phone number starts with +1
            country_name = 'United States'
        if country_name == '' and phone_number.startswith('+972'):
            # Default to Israel if the country is not found and the phone number starts with +972
            country_name = 'Israel'
        logger.end("Successfully retrieved country name",
                   object={'phone_number': phone_number, 'country_name': country_name})
        result = country_name.upper()
        return result

    @staticmethod
    def get_country_name_by_email_address(email_address: str) -> str:
        logger.start("start get_country_name_by_email_address",
                     object={'email_address': email_address})
        # Extract domain from the email address
        domain_parts = email_address.split('@')[-1].split('.')
        # Create domain suffixes that might include second-level domains
        domain_suffixes = [
            '.'.join(domain_parts[-(i + 1):]) for i in range(min(2, len(domain_parts) - 1))
        ]
        # Check each possible domain suffix until a match is found
        for suffix in domain_suffixes:
            if suffix in LocationLocalConstants.DOMAIN_TO_COUNTRY:
                country_name = LocationLocalConstants.DOMAIN_TO_COUNTRY.get(suffix)
                logger.end("Successfully retrieved country name",
                           object={'email_address': email_address, 'country_name': country_name})
                country_name_upper = country_name.upper()
                return country_name_upper
        logger.end("Country name not found",
                   object={'email_address': email_address})


# TODO Create Country class which store one country
class Country(CountriesLocal):
    pass  # backward compatibility
