import hashlib
import json
import os
import time

# import webbrowser
from datetime import datetime, timezone

from database_mysql_local.generic_crud import GenericCRUD
from google.auth import exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from logger_local.MetaLogger import MetaLogger
from python_sdk_remote.utilities import our_get_env

from user_external_local.user_externals_local import UserExternalsLocal
from user_external_local.token__user_external import TokenUserExternals
from profile_local.profiles_local import ProfilesLocal
from logger_local.LoggerLocal import Logger

from .google_account_local_constants import GoogleAccountLocalConstants

SLEEP_TIME = 5
TIMEOUT = 50

USER_EXTERNAL_SCHEMA_NAME = "user_external"
USER_EXTERNAL_TABLE_NAME = "user_external_table"
USER_EXTERNAL_VIEW_NAME = "user_external_view"
USER_EXTERNAL_DEFAULT_COLUMN_NAME = "user_external_id"

# Static token details
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/contacts",
    "openid",
]  # Both scopes must be allowed within the project!


class GoogleAccountLocal(
    GenericCRUD,
    metaclass=MetaLogger,
    object=GoogleAccountLocalConstants.LoggerSetupConstants.GOOGLE_ACCOUNT_LOCAL_CODE_LOGGER_OBJECT,
):
    """
    Manages OAuth 2.0 authentication with Google services.

    This class handles the full authentication flow with Google, including:
    - Initial authorization and token acquisition
    - Token storage and management in database
    - Token refresh when credentials expire
    - User verification against expected email
    - *Note:* a token is valid for 1 hour.
    """

    def __init__(self, is_test_data: bool = False) -> None:
        """
        Initialize the GoogleAccountLocal instance.

        Sets up database connections, loads environment variables, and initializes
        the necessary properties for Google OAuth authentication.

        Args:
            is_test_data (bool, optional): Flag indicating if test data should be used.
                Defaults to False.
        """
        GenericCRUD.__init__(
            self,
            default_schema_name=USER_EXTERNAL_SCHEMA_NAME,
            default_table_name=USER_EXTERNAL_TABLE_NAME,
            default_view_table_name=USER_EXTERNAL_VIEW_NAME,
            default_column_name=USER_EXTERNAL_DEFAULT_COLUMN_NAME,
            is_test_data=is_test_data,
        )

        self.user_externals_local = UserExternalsLocal()
        self.token__user_external = TokenUserExternals()
        self.profile_local = ProfilesLocal()
        self.logger = Logger.create_logger(object=GoogleAccountLocalConstants.LoggerSetupConstants.GOOGLE_ACCOUNT_LOCAL_CODE_LOGGER_OBJECT)

        self.service = None
        self.creds = None
        self.user_email_address = our_get_env(
            "GOOGLE_USER_EXTERNAL_USERNAME", raise_if_empty=False,
            raise_if_not_found=False, default=None
        )
        self.google_client_id = our_get_env("GOOGLE_CLIENT_ID", raise_if_empty=True)
        self.google_client_secret = our_get_env(
            "GOOGLE_CLIENT_SECRET", raise_if_empty=True
        )
        # self.google_port_for_authentication = int(our_get_env("GOOGLE_PORT_FOR_AUTHENTICATION", raise_if_empty=True))
        self.google_redirect_uris = our_get_env(
            "GOOGLE_REDIRECT_URIS", raise_if_empty=True
        )
        self.google_auth_uri = our_get_env("GOOGLE_AUTH_URI",
                                           raise_if_empty=True)
        self.google_token_uri = our_get_env("GOOGLE_TOKEN_URI",
                                            raise_if_empty=True)

    # TODO: rename email to username everywhere
    def authenticate(self, email: str):
        """
        Authenticate with Google services using OAuth 2.0.

        This method updates the credentials for the Google account associated with the provided email address.
        - for the user_external_table it updates the access_token, refresh_token, and expiry.
        if the user already exists. inserts a new record otherwise.
        - for the token_user_external_table it it always inserts a new record.

        Args:
            email (str): The email address to authenticate with Google.
                This email is used to lookup profile information and
                is verified against the authenticated Google account.

        Raises:
            Exception: If the authenticated email doesn't match the expected email,
                      if no access token is found, or if profile lookup fails.
        """
        user_external_id = None
        profile_id = self.profile_local.get_profile_id_by_email_address(
            email_address=email
        )
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:

            # TODO: move this to a separate method
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # self.creds.refresh(Request())
                self.__refresh_and_update_token(
                    refresh_token=self.creds.refresh_token,
                    user_external_id=user_external_id,
                    profile_id=profile_id,
                )
            else:
                auth_details = self.user_externals_local.get_auth_details(
                    system_id=GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
                    username=email,
                    profile_id=profile_id
                )
                # the old where: where="username=%s AND is_refresh_token_valid=TRUE AND system_id=%s",
                if auth_details:
                    is_refresh_token_valid = \
                        auth_details.get("is_refresh_token_valid",)

                if auth_details is None or is_refresh_token_valid is False:
                # if True:  # noqa
                    self.logger.info(
                        "Google account is not valid, please reauthorize. \n the link to reauthorize is: ",
                    )
                    user_external_id = self.__authorize()

                    auth_details = self.user_externals_local.get_auth_details(
                        system_id=GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
                        username=email,
                        profile_id=profile_id
                    )

                refresh_token = auth_details.get("refresh_token")
                access_token = auth_details.get("access_token")
                user_external_id = auth_details.get("user_external_id")
                oauth_state = auth_details.get("oauth_state")
                expiry = auth_details.get("expiry")

                if not refresh_token:
                    user_external_id = \
                        self.__authorize(oauth_state=oauth_state)
                elif refresh_token and self.check_if_expired(expiry):

                    self.creds = Credentials(
                        token=access_token,
                        refresh_token=refresh_token,
                        token_uri=self.google_token_uri,
                        client_id=self.google_client_id,
                        client_secret=self.google_client_secret,
                    )

                    self.__refresh_and_update_token(
                        refresh_token=refresh_token,
                        user_external_id=user_external_id,
                        profile_id=profile_id,
                    )
                else:
                    self.creds = Credentials(
                        token=access_token,
                        refresh_token=refresh_token,
                        token_uri=self.google_token_uri,
                        client_id=self.google_client_id,
                        client_secret=self.google_client_secret,
                    )

            # Fetch the user's user_email for profile_id in our DB
            # TODO Can we wrap all indirect calls with Api Management?
            # self.service = build("oauth2", "v2", credentials=self.creds)

            self.service, user_info = self.__our_build_service_and_execute(
                service_name="oauth2", version="v2", credentials=self.creds
            )

            if user_info.get("email") != email:
                if user_external_id is not None:
                    # self.delete_by_column_and_value(
                    #     schema_name="user_external",
                    #     table_name="user_external_table",
                    #     column_name="user_external_id",
                    #     column_value=user_external_id,
                    # )

                    self.user_externals_local.delete_access_token(
                        system_id=GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
                        username=email,
                        profile_id=profile_id,
                    )

                raise Exception(
                    "The email address of the connected Google account does not match the provided email."
                )

            self.user_email_address = user_info.get(
                "email"
            )
            # Cannot be "user_email" because we get it from the API
            # is_verified_email = user_info.get("verified_email")
            # user_account_id = user_info.get("id")  # TODO DO we need this?
            # user_picture = user_info.get("picture")  # TODO: save in storage

            # # Deserialize the token_data into a Python dictionary
            # token_data_dict = json.loads(self.creds.to_json())

            # self.logger.info(
            #     f"Token data dict: {token_data_dict}",
            #     object=token_data_dict,
            # )
            # # TODO: What other data can we get from token_data_dict?

            # # Extract the access_token, expires_in, and refresh_token to insert into our DB
            # access_token = token_data_dict.get("token")
            # expires_in = token_data_dict.get("expiry")
            # refresh_token = token_data_dict.get("refresh_token")

            # if access_token and user_external_id is None:
            #     # TODO: Do we still need this if case?
            #     try:
            #         self.user_externals_local.insert_or_update_user_external_access_token(
            #             system_id=GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
            #             username=self.user_email,
            #             access_token=access_token,
            #             profile_id=profile_id,
            #             expiry=expires_in,
            #             refresh_token=refresh_token,
            #         )
            #     except Exception as e:
            #         self.logger.error(
            #             f"Failed to insert or update user_external access token: {e}",
            #             object={
            #                 "user_external_id": user_external_id,
            #                 "name": self.user_email,
            #                 "profile_id": profile_id,
            #                 "access_token": access_token,
            #                 "expiry": expires_in,
            #                 "refresh_token": refresh_token,
            #             },
            #         )
            #         raise

            #     # ! we no longer insert tokens to the user_external table
            #     # self.user_externals_local.insert_or_update_user_external_access_token(
            #     #     system_id=GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
            #     #     username=self.user_email,
            #     #     # We can't get profile_id by user_email for play1@circ.zone because it's not in profile_view,
            #     #     # this method will always select from view
            #     #     profile_id=profile_id,
            #     #     access_token=access_token,
            #     #     expiry=expires_in,
            #     #     refresh_token=refresh_token)

            # elif access_token and user_external_id is not None:
            #     try:
            #         self.user_externals_local.insert_or_update_user_external_access_token(
            #             system_id=GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
            #             username=self.user_email,
            #             profile_id=profile_id,
            #             access_token=access_token,
            #             expiry=expires_in,
            #             refresh_token=refresh_token,
            #         )
            #     except Exception as e:
            #         self.logger.error(
            #             f"Failed to insert or update user_external access token: {e}",
            #             object={
            #                 "user_external_id": user_external_id,
            #                 "name": self.user_email,
            #                 "profile_id": profile_id,
            #                 "access_token": access_token,
            #                 "expiry": expires_in,
            #                 "refresh_token": refresh_token,
            #             },
            #         )
            #         raise

            #     # self.update_by_column_and_value(
            #     #     schema_name="user_external", table_name="user_external_table",
            #     #     column_name="user_external_id", column_value=user_external_id,
            #     #     data_dict={"access_token": access_token, "expiry": expires_in, "refresh_token": refresh_token,
            #     #                "is_refresh_token_valid": True, "username": self.user_email,
            #     #                "system_id": GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID})
            #     # data_dict = {"profile_id": profile_id, "user_external_id": user_external_id}
            #     # self.insert(schema_name="profile_user_external", table_name="profile_user_external_table",
            #     #             data_dict=data_dict)
            # else:
            #     raise Exception("Access token not found in token_data.")

    def __authorize(self, oauth_state: str = None) -> int:
        """
        Initiate the OAuth 2.0 authorization flow with Google.

        This private method:
        1. Creates an OAuth flow with the configured client credentials
        2. Generates a state parameter and authorization URL
        3. Displays the URL for the user to visit
        4. Polls the database for the authorization code
        5. Exchanges the code for OAuth tokens

        Args:
            oauth_state (str, optional): An existing OAuth state to use.
                Defaults to None, in which case a new state is generated.

        Returns:
            int: The user_external_id of the created/updated record

        Raises:
            Exception: If profile ID is not found for the email
                      or if the auth code is not found in the database
                      within the timeout period
        """
        client_config = {
            "installed": {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "redirect_uris": self.google_redirect_uris,
                "auth_uri": self.google_auth_uri,
                "token_uri": self.google_token_uri,
            }
        }
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        flow = InstalledAppFlow.from_client_config(
            client_config, SCOPES, redirect_uri=self.google_redirect_uris, state=state
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline", prompt="consent"
        )  # access_type='online' won't return a refresh token
        # old: self.creds = flow.run_local_server(port=0)
        # if GOOGLE_REDIRECT_URIS is localhost it must be
        # GOOGLE_REDIRECT_URIS=http://localhost:54415/
        # if the port number is 54415 and we must also pass that port
        # to the run_local_server function
        # and also add EXACTLY http://localhost:54415/
        # to Authorised redirect URIs in the
        # OAuth 2.0 Client IDs in Google Cloud Platform

        # main_profile_id = self.select_one_value_by_column_and_value(
        #     schema_name="profile",
        #     view_table_name="profile_view",
        #     select_clause_value="profile_id",
        #     column_value=self.user_email,
        #     column_name="profile.main_email_address",
        # )

        main_profile_id = self.profile_local.get_profile_id_by_email_address(
            email_address=self.user_email_address
        )

        user_external_data_dict = {
            "oauth_state": state,
            "username": self.user_email_address,
            "system_id": GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
            "is_refresh_token_valid": True,
        }

        if main_profile_id:
            user_external_data_dict["main_profile_id"] = main_profile_id
        else:
            exception_message = f"Profile ID not found for email {self.user_email_address}"
            self.logger.error(exception_message)
            raise Exception(exception_message)

        data_dict_compare_user_external = {
            "main_profile_id": main_profile_id,
            # TODO Shall this be self.user_email_address
            "username": self.user_email_address,
            "system_id": GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
        }

        user_external_id = self.user_externals_local.upsert(
            data_dict=user_external_data_dict,
            data_dict_compare=data_dict_compare_user_external,
        )

        token__user_external_id = \
            self.user_externals_local.token__user_externals.insert_or_update_user_external_access_token(
                user_external_id=user_external_id,
                username=self.user_email_address,
                profile_id=main_profile_id,
                access_token=None,
                expiry=None,
        )

        self.logger.info(
            f"token__user_external_id: {token__user_external_id}",
        )

        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ')
        # TODO Can we add the profile name to the bellow message?
        print(f'google-account-local-python-package: Please open the browser in the right profile (i.e, play1@circ.zone) and go to this URL and authorize the application: {auth_url}', flush=True)  # flash=True is for GHA
        print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ')
        # TODO How can we check if we are in GHA or not?
        # webbrowser.open(auth_url) - doesn't work in GHA

        # TODO user_external_id = UserExternal.insert()
        # TODO "oauth_state": oauth_state

        # If the url is
        # http://localhost:54219/?state=yp8FP2BF7cI9xExjUB70Oyaol0oDNG&code=4/0AdLIrYclkHjKFCb_yJn625Htr8FejaRjFawe7mldEqWINitBz6VD_E0ZOWx0K5d4eocYZg&scope=email%20openid%20https://www.googleapis.com/auth/contacts.readonly%20https://www.googleapis.com/auth/userinfo.email&authuser=0&prompt=consent
        # the auth_code is 4/0AdLIrYclkHjKFCb_yJn625Htr8FejaRjFawe7mldEqWINitBz6VD_E0ZOWx0K5d4eocYZg
        # is found after the code= in the url
        auth_code = None
        # Trying every 5 seconds to get the auth code from the database with a timeout of 50 seconds.
        print(f'Waiting for {TIMEOUT} seconds, for you to choose account {self.user_email_address} in this URL {auth_url}', flush=True)  # flash=True is for GHA  # noqa
        for i in range(TIMEOUT // SLEEP_TIME):
            # selecting by primary key is faster, so we don't select by state
            # auth_code = self.select_one_value_by_column_and_value(
            #     select_clause_value="access_token",
            #     column_value=user_external_inserted_id,
            # )

            auth_code = self.user_externals_local.get_access_token(
                system_id=GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
                username=self.user_email_address,
                profile_id=main_profile_id,
            )

            if auth_code:
                self.logger.info(
                    f"Auth code found in the database after {i + 1} times out of {TIMEOUT // SLEEP_TIME}."
                )
                break
            time.sleep(SLEEP_TIME)
            self.logger.info(
                f"Failed to get the auth code from the database for the {i + 1} time out of {TIMEOUT // SLEEP_TIME}."
            )

        if not auth_code:
            # TODO Add the UserContext.username() in the begging of the Exception text
            self.logger.error(
                f"Auth code not found in the database after {TIMEOUT} seconds. "
                f"Please check if you have chosen the correct Google account {self.user_email_address} in the browser opened."
            )
            raise Exception("Auth code not found in the database, you probably didn't choose the Google Account to use in the browser opened.")
        # TODO How can we check that the user choose the expected Google Account or not?
        flow.fetch_token(code=auth_code)
        self.creds = flow.credentials

        self.__save_credentials(
            user_external_id=user_external_id,
            state=state,
            creds=self.creds,
        )

        return user_external_id
        # self.creds = flow.run_local_server(port=self.port)

    def get_email_address(self):
        """
        Get the email address of the authenticated Google account.

        Returns:
            str: The email address of the authenticated Google account,
                 or None if not authenticated.
        """
        return self.user_email_address

    def __our_build_service_and_execute(
        self, service_name: str = "oauth2", version: str = "v2", credentials: Credentials = None
    ) -> tuple[object, dict]:
        """
        Build a Google API service and execute a request.

        Args:
            service_name (str): The name of the Google API service to build.
            version (str): The version of the Google API service to build.
            credentials (Credentials): The credentials to use for authentication.

        Returns:
            object: The built service object.
        """
        if not credentials:
            raise ValueError("Credentials must be provided to build the service.")

        service = build(service_name, version, credentials=credentials)

        try:
            user_info = service.userinfo().get().execute()
        except Exception as e:
            self.logger.error(
                f"Failed to execute userinfo request: {e}",
                object={"service_name": service_name, "version": version},
            )
            raise

        return service, user_info

    def __save_credentials(self, user_external_id: int, state: str, creds: Credentials):
        """
        Save the credentials to a file.

        Args:
            user_external_id (int): The user_external_id to associate with the credentials.
            creds (Credentials): The credentials to save.
        """
        creds_dict = json.loads(creds.to_json())

        access_token = creds_dict.get("token")
        refresh_token = creds_dict.get("refresh_token")
        expiry = creds_dict.get("expiry")

        token_user_external_data_dict = {
            "user_external_id": user_external_id,
            "access_token": access_token,
            "expiry": expiry,
            "oauth_state": state,
        }

        data_dict_compare = {
            "user_external_id": user_external_id,
        }

        token__user_external_id = self.token__user_external.upsert(
            schema_name="user_external",
            table_name="token__user_external_table",
            data_dict=token_user_external_data_dict,
            data_dict_compare=data_dict_compare,
        )
        self.logger.info(
            f"Token data dict: {token_user_external_data_dict}/n Token user_external inserted ID: {token__user_external_id}",
            object=token_user_external_data_dict,
        )

        updated_rows = self.user_externals_local.update_refresh_token_by_user_external_id(
            user_external_id=user_external_id,
            refresh_token=refresh_token,
        )

        self.logger.info(
            f"Updated {updated_rows} rows in user_external table with refresh token.",
            object={"user_external_id": user_external_id},
        )

    def __refresh_and_update_token(
        self, refresh_token: str, user_external_id: int, profile_id: int
    ):
        """
        Refresh the access token using the refresh token and update the database.

        Keyword arguments:
        argument --
        - refresh_token: The refresh token to use for refreshing the access token.
        - user_external_id: The user_external_id to update in the database.
        - profile_id: The profile_id to update in the database.

        Return: None
        """

        try:
            self.creds.refresh(Request())

            refreshed_access_token = self.creds.token
            refresh_expiry = self.creds.expiry
            self.logger.info(
                f"refreshing access token for user_external_id: {user_external_id}, "
                f"new expiry: {refresh_expiry}",
                object={
                    "user_external_id": user_external_id,
                    "refreshed_access_token": refreshed_access_token,
                    "refresh_expiry": refresh_expiry,
                },
            )

            self.user_externals_local.update_user_external_access_token(
                user_external_id=user_external_id,
                system_id=GoogleAccountLocalConstants.GOOGLE_SYSTEM_ID,
                username=self.user_email_address,
                profile_id=profile_id,
                access_token=refreshed_access_token,
                expiry=refresh_expiry,
            )

        except exceptions.RefreshError as exception:
            self.logger.error(
                "google-contact-local Google Refresh token failed.",
                object={"exception": exception},
            )
            exception_message = str(exception)
            if (
                "Token has been expired or revoked"
                in exception_message
            ) or (
                "The credentials returned by the refresh_handler are already expired"
                in exception_message
            ):
                # # The refresh token can become an invalid
                # self.update_by_column_and_value(
                #     schema_name="user_external",
                #     table_name="user_external_table",
                #     column_name="refresh_token",
                #     column_value=refresh_token,
                #     data_dict={"is_refresh_token_valid": False},
                # )
                # "end_timestamp": datetime.now(ZoneInfo("UTC"))})

                self.user_externals_local.update_is_refresh_token_valid_status_by_refresh_token(
                    refresh_token=refresh_token,
                    is_refresh_token_valid=False,
                )

                user_external_id = self.__authorize()

    def check_if_expired(self, expiry: str) -> bool:
        """
        Check if the token is expired.

        Args:
            expiry (str): The expiry time of the token.

        Returns:
            bool: True if the token is expired, False otherwise.
        """
        if not expiry:
            return True

        # Most common formats
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",   # With microseconds
            "%Y-%m-%d %H:%M:%S",      # Without microseconds
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with Z
            "%Y-%m-%dT%H:%M:%SZ"      # ISO format without microseconds
        ]
        is_expired = True

        for fmt in formats:
            try:
                # Parse the timestamp
                expiry_timestamp = datetime.strptime(expiry, fmt)

                # Make timezone-aware if not already
                if expiry_timestamp.tzinfo is None:
                    expiry_timestamp = expiry_timestamp.replace(tzinfo=timezone.utc)

                # Check expiration
                current_time = datetime.now(timezone.utc)
                is_expired = current_time > expiry_timestamp
                self.logger.info(
                        f"Token expiry check: {is_expired}. Current time: {current_time}, Expiry time: {expiry_timestamp}",
                        object={"is_expired": is_expired},
                    )
                return is_expired
            except ValueError:
                continue

        return is_expired  # Default to True if all formats fail
