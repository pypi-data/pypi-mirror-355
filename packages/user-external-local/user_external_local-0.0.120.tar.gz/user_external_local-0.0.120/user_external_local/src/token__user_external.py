# from database_mysql_local.connector import Connector
# from mysql.connector.errors import IntegrityError
from database_mysql_local.generic_crud import GenericCRUD
from logger_local.LoggerComponentEnum import LoggerComponentEnum
from logger_local.LoggerLocal import Logger
from logger_local.MetaLogger import MetaLogger

USER_EXTERNAL_LOCAL_PYTHON_PACKAGE_COMPONENT_ID = 115
USER_EXTERNAL_LOCAL_PYTHON_PACKAGE_COMPONENT_NAME = "user_external_local_python"
DEVELOPER_EMAIL = "idan.a@circ.zone"
object_init = {
    "component_id": USER_EXTERNAL_LOCAL_PYTHON_PACKAGE_COMPONENT_ID,
    "component_name": USER_EXTERNAL_LOCAL_PYTHON_PACKAGE_COMPONENT_NAME,
    "component_category": LoggerComponentEnum.ComponentCategory.Code.value,
    "developer_email": DEVELOPER_EMAIL,
}

# TODO TOKEN__USER_EXTERNAL__SCHEMA_NAME =
USER_EXTERNAL_SCHEMA_NAME = "user_external"

TOKEN_USER_EXTERNAL_TABLE_NAME = "token__user_external_table"
TOKEN_USER_EXTERNAL_VIEW_NAME = "token__user_external_view"
TOKEN_USER_EXTERNAL_ID_COLUMN_NAME = "token__user_external_id"

# TODO do we need this in both places? We prefer to define it only once
TOKEN_USER_EXTERNAL_GENERAL_VIEW_NAME = "user_external_latest_token_general_view"

logger = Logger.create_logger(object=object_init)


class TokenUserExternals(GenericCRUD, metaclass=MetaLogger, object=object_init):
    def __init__(self, is_test_data: bool = False):
        super().__init__(
            default_schema_name=USER_EXTERNAL_SCHEMA_NAME,
            default_table_name=TOKEN_USER_EXTERNAL_TABLE_NAME,
            default_view_table_name=TOKEN_USER_EXTERNAL_VIEW_NAME,
            default_column_name=TOKEN_USER_EXTERNAL_ID_COLUMN_NAME,
            is_test_data=is_test_data,
        )

    # TODO we should split to insert_or_update_user_external(username, profile...)->user_external_id
    # TODO and insert_or_update_user_external_access_token(access_token, expiry) -> token__user_external_id
    # TODO Shall we rename insert_or_update... to upsert...
    # TODO Do we have the same method name in both classes? - Shall we?
    def insert_or_update_user_external_access_token(
        self,
        *,
        user_external_id: int,
        username: str,
        profile_id: int,
        access_token: str,
        expiry=None,
    ) -> int:
        """
        Inserts or updates a token for a user's external record
        """
        if not user_external_id:
            raise ValueError("user_external_id is required")
        object_start = {
            "user_external_id": user_external_id,
            "username": username,
            "access_token": access_token,
            "expiry": expiry,
        }
        logger.start(object=object_start)

        # Check if token already exists
        # TODO currenct_access_token
        current_token = self.get_access_token(user_external_id=user_external_id)

        data_dict = {
            "user_external_id": user_external_id,
            # TODO Shall we use current_token / current_access_token?
            "access_token": access_token,
            "expiry": expiry if expiry is not None else "",
        }

        if current_token is not None:
            # Update existing token
            updated_access_token_row = self.update_access_token(
                user_external_id=user_external_id,
                name=username,
                access_token=access_token,
                expiry=expiry,
            )
            logger.info(
                f"Number of updated tokens: {updated_access_token_row}",
                object=data_dict,
            )
            return user_external_id

        # Insert new token
        try:
            inserted_access_token_row = self.insert(
                schema_name=USER_EXTERNAL_SCHEMA_NAME,
                table_name=TOKEN_USER_EXTERNAL_TABLE_NAME,
                data_dict=data_dict,
            )
            logger.info("Token inserted", object=data_dict)
        except Exception as e:
            logger.error(
                log_message="Error inserting token",
                object={
                    "data_dict": data_dict,
                    "error": str(e),
                },
            )
            raise e

        # except IntegrityError as e:
        # ! there is no need to catch IntegrityError as we aleady check if token exists and update it # before inserting a new one
        #     logger.error(
        #         log_message="IntegrityError",
        #         object={
        #             "data_dict": data_dict,
        #             "error": str(e),
        #         },
        #     )
        #     self.update_access_token(
        #         user_external_id=user_external_id,
        #         username=username,
        #         access_token=access_token,
        #         expiry=expiry,
        #     )
        #     logger.info("Token updated after IntegrityError", object=data_dict)

        try:
            data_dict_profile = {
                "user_external_id": user_external_id,
                "profile_id": profile_id,
            }
            data_dict_profile_compare = {
                "user_external_id": user_external_id,
                "profile_id": profile_id,
            }
            # TODO We added Unique Index (profile_id, user_external_id and end_timestamp). We should make sure it works when the profile_user_external already exists, without error  # noqa
            # TODO We should create and call ProfileUserExternalLocal class
            self.upsert(
                schema_name="profile_user_external",
                table_name="profile_user_external_table",
                view_table_name="profile_user_external_view",
                data_dict=data_dict_profile,
                data_dict_compare=data_dict_profile_compare,
            )
            logger.info("Record inserted into profile_user_external", object=data_dict)
        except Exception as e:
            logger.error(
                log_message="Error inserting record into profile_user_external",
                object={
                    "data_dict": data_dict,
                    "error": str(e),
                },
            )
            raise e

        return inserted_access_token_row

    def get_access_token(self, *, user_external_id: int) -> str:
        """
        Gets the access token for a specific user's external record and username
        """
        object_start = {"user_external_id": user_external_id}
        logger.start(object=object_start)

        access_token = self.select_one_value_by_where(
            schema_name=USER_EXTERNAL_SCHEMA_NAME,
            view_table_name=TOKEN_USER_EXTERNAL_VIEW_NAME,
            select_clause_value="access_token",
            where="user_external_id=%s AND end_timestamp IS NULL",
            params=(user_external_id,),
            order_by="updated_timestamp DESC",
        )

        return access_token

    # TODO Why do we need the profile_id?
    def get_access_token_by_username_system_id_and_profile_id(
        self, *, username: str, system_id: int, profile_id: int
    ) -> str:
        """
        Gets the access token for a specific username, system ID, and profile ID
        """
        object_start = {
            "username": username,
            "system_id": system_id,
            "profile_id": profile_id,
        }
        logger.start(object=object_start)

        access_token = self.select_one_value_by_where(
            schema_name=USER_EXTERNAL_SCHEMA_NAME,
            view_table_name=TOKEN_USER_EXTERNAL_GENERAL_VIEW_NAME,
            select_clause_value="access_token",
            where="username=%s AND system_id=%s AND profile_id=%s AND end_timestamp IS NULL",
            params=(username, system_id, profile_id),
            order_by="updated_timestamp DESC",
        )

        return access_token

    def get_access_token_by_username_and_system_id(
        self, *, username: str, system_id: int
    ) -> str:
        """
        Gets the access token for a specific username and system ID
        """
        object_start = {
            "username": username,
            "system_id": system_id,
        }
        logger.start(object=object_start)

        try:
            access_token = self.select_one_value_by_where(
                schema_name=USER_EXTERNAL_SCHEMA_NAME,
                view_table_name=TOKEN_USER_EXTERNAL_GENERAL_VIEW_NAME,
                select_clause_value="access_token",
                where="username=%s AND system_id=%s AND end_timestamp IS NULL",
                params=(username, system_id),
                order_by="updated_timestamp DESC",
            )

            return access_token

        except Exception as e:
            logger.error(
                log_message="Error getting access token by username and system ID",
                object={
                    "username": username,
                    "system_id": system_id,
                    "error": str(e),
                },
            )
            raise e

    def update_access_token(
        self,
        *,
        user_external_id: int,
        # TODO username -> name
        name: str,
        access_token: str,
        expiry=None,
    ) -> int:
        """
        Updates the access token for a specific user's external record and name

        Keyword arguments:
        arguments:
        - user_external_id: the ID of the user's external record
        - name: the name of the user
        - access_token: the new access token to be set
        - expiry: the expiry time of the access token (optional)

        Return: int - the number of rows updated in the database
        """

        object_start = {
            "user_external_id": user_external_id,
            "name": name,
            "access_token": access_token,
        }
        logger.start(object=object_start)

        data_dict = {"access_token": access_token}

        if expiry is not None:
            data_dict["expiry"] = expiry

        try:
            updated_rows = self.update_by_where(
                schema_name=USER_EXTERNAL_SCHEMA_NAME,
                table_name=TOKEN_USER_EXTERNAL_TABLE_NAME,
                where="user_external_id=%s AND end_timestamp IS NULL",
                params=(user_external_id,),
                data_dict=data_dict,
            )
            logger.info("Token updated", object=object_start)
        except Exception as e:
            logger.error(
                log_message="Error updating token",
                object={
                    "user_external_id": user_external_id,
                    "name": name,
                    "data_dict": data_dict,
                    "error": str(e),
                },
            )
            raise e
        return updated_rows

    def delete_access_token_by_user_external_id(
        self, *, user_external_id: int, username: str
    ) -> int:
        """
        Marks a token as deleted by setting end_timestamp to the current time
        """
        object_start = {
            "user_external_id": user_external_id,
            "username": username,
        }
        logger.start(object=object_start)

        try:
            deleted_rows = self.delete_by_where(
                schema_name=USER_EXTERNAL_SCHEMA_NAME,
                table_name=TOKEN_USER_EXTERNAL_TABLE_NAME,
                where="user_external_id=%s AND end_timestamp IS NULL",
                params=(user_external_id,),
            )
            logger.info("Token deleted", object=object_start)
            return deleted_rows
        except Exception as e:
            logger.error(
                log_message="Error deleting token",
                object={
                    "user_external_id": user_external_id,
                    "name": username,
                    "error": str(e),
                },
            )
            raise e

    def delete_access_token_by_token__user_external_id(
        self, *, token__user_external_id: int
    ) -> int:
        """
        Marks a token as deleted by setting end_timestamp to the current time
        """
        object_start = {
            "token__user_external_id": token__user_external_id,
        }
        logger.start(object=object_start)

        try:
            deleted_rows = self.delete_by_where(
                schema_name=USER_EXTERNAL_SCHEMA_NAME,
                table_name=TOKEN_USER_EXTERNAL_TABLE_NAME,
                where="token__user_external_id=%s AND end_timestamp IS NULL",
                params=(token__user_external_id,),
            )
            logger.info("Token deleted", object=object_start)
            return deleted_rows
        except Exception as e:
            logger.error(
                log_message="Error deleting token",
                object={
                    "token__user_external_id": token__user_external_id,
                    "error": str(e),
                },
            )
            raise e

    def get_auth_details(self, *, user_external_id: int) -> dict:
        """
        Gets authentication details including access_token, refresh_token, and expiry

        Keyword arguments:
        user_external_id: the ID of the user's external record

        Return: dict - a dictionary containing:
        - user_external_id
        - access_token
        - refresh_token
        - expiry
        - is_refresh_token_valid
        - oauth_state
        """

        object_start = {
            "user_external_id": user_external_id,
        }
        logger.start(object=object_start)

        try:
            result = self.select_one_dict_by_where(
                schema_name=USER_EXTERNAL_SCHEMA_NAME,
                view_table_name=TOKEN_USER_EXTERNAL_GENERAL_VIEW_NAME,
                select_clause_value="user_external_id, access_token, refresh_token, expiry, is_refresh_token_valid, oauth_state",
                where="user_external_id=%s AND end_timestamp IS NULL",
                params=(user_external_id,),
                order_by="updated_timestamp DESC",
            )

            if not result:
                logger.error(log_message="Token not found", object=object_start)
                return None

            return result
        except Exception as e:
            logger.error(
                log_message="Error getting auth details",
                object={
                    "user_external_id": user_external_id,
                    "error": str(e),
                },
            )
            raise e

    def get_auth_details_by_system_id_and_profile_id(
        self, *, profile_id: int, system_id: int
    ) -> dict:
        """
        Gets authentication details including access_token, refresh_token, and expiry

        Keyword arguments:
        - profile_id: the ID of the profile
        - system_id: the ID of the system

        Return: dict - a dictionary containing user_external_id, access_token, refresh_token, expiry, is_refresh_token_valid, and oauth_state
        """

        object_start = {
            "profile_id": profile_id,
            "system_id": system_id,
        }
        logger.start(object=object_start)

        try:
            result = self.select_one_dict_by_where(
                schema_name=USER_EXTERNAL_SCHEMA_NAME,
                view_table_name=TOKEN_USER_EXTERNAL_GENERAL_VIEW_NAME,
                select_clause_value="user_external_id, access_token, refresh_token, expiry, is_refresh_token_valid, oauth_state",
                where="profile_id=%s AND system_id=%s AND end_timestamp IS NULL",
                params=(profile_id, system_id),
                order_by="updated_timestamp DESC",
            )

            if not result:
                logger.error(log_message="Token not found", object=object_start)
                return None

            return result
        except Exception as e:
            logger.error(
                log_message="Error getting auth details by system ID and profile ID",
                object={
                    "profile_id": profile_id,
                    "system_id": system_id,
                    "error": str(e),
                },
            )
            raise e
