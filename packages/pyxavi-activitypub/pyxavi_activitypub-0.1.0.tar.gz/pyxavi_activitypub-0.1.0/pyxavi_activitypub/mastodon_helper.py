from __future__ import annotations
from .firefish import Firefish
from mastodon import Mastodon
from datetime import datetime
from logging import Logger
import logging
import os


class MastodonInstanceType:
    """
    The instance_type parameter is a string value and accepts any of:

    "mastodon" - Mastodon instances
    "pleroma" - Pleroma / Akkoma
    "firefish" - Firefish / Calckey
    """
    MASTODON = "mastodon"
    PLEROMA = "pleroma"
    FIREFISH = "firefish"

    @staticmethod
    def valid_or_raise(value: str) -> MastodonInstanceType:
        valid_items = [
            MastodonInstanceType.MASTODON,
            MastodonInstanceType.PLEROMA,
            MastodonInstanceType.FIREFISH
        ]

        if value not in valid_items:
            raise RuntimeError(f"Value [{value}] is not a valid MastodonInstanceType")

        return value


class MastodonHelper:

    FEATURE_SET_BY_INSTANCE_TYPE = {
        MastodonInstanceType.MASTODON: "mainline", MastodonInstanceType.PLEROMA: "pleroma"
    }

    WRAPPER = {
        MastodonInstanceType.MASTODON: Mastodon,
        MastodonInstanceType.PLEROMA: Mastodon,
        MastodonInstanceType.FIREFISH: Firefish
    }

    @staticmethod
    def get_instance(
        connection_params: MastodonConnectionParams,
        logger: Logger = None,
        base_path: str = None
    ) -> Mastodon:
        if logger is None:
            logger = logging.getLogger()

        instance_type = MastodonInstanceType.valid_or_raise(connection_params.instance_type)
        user_file = connection_params.credentials.user_file
        client_file = connection_params.credentials.client_file
        if base_path is not None:
            user_file = os.path.join(base_path, user_file)
            client_file = os.path.join(base_path, client_file)

        if not os.path.exists(client_file):
            logger.debug("The Client file does not exist. Creating the app.")
            MastodonHelper.create_app(
                instance_type=connection_params.instance_type,
                client_name=connection_params.app_name,
                api_base_url=connection_params.api_base_url,
                to_file=client_file
            )

        # All actions are done under a Mastodon API instance
        logger.debug("Starting new Mastodon API instance")
        if (os.path.exists(user_file)):
            logger.debug("Reusing stored User Credentials")
            mastodon = MastodonHelper.WRAPPER[instance_type](
                access_token=user_file,
                feature_set=MastodonHelper.FEATURE_SET_BY_INSTANCE_TYPE[instance_type]
                if instance_type
                in [MastodonInstanceType.MASTODON, MastodonInstanceType.PLEROMA] else None
            )
        else:
            logger.debug("Using Client Credentials")
            mastodon = MastodonHelper.WRAPPER[instance_type](
                client_id=client_file,
                api_base_url=connection_params.api_base_url,
                feature_set=MastodonHelper.FEATURE_SET_BY_INSTANCE_TYPE[instance_type]
                if instance_type
                in [MastodonInstanceType.MASTODON, MastodonInstanceType.PLEROMA] else None
            )

            # Logging in is required for all individual runs
            logger.debug("Logging in")
            mastodon.log_in(
                connection_params.credentials.user.email,
                connection_params.credentials.user.password,
                to_file=user_file
            )

        return mastodon

    @staticmethod
    def create_app(
        instance_type: str, client_name: str, api_base_url: str, to_file: str
    ) -> tuple:
        return MastodonHelper.WRAPPER[instance_type].create_app(
            client_name=client_name, api_base_url=api_base_url, to_file=to_file
        )


class MastodonConnectionParams():

    DEFAULT_INSTANCE_TYPE = MastodonInstanceType.MASTODON

    app_name: str
    instance_type: MastodonInstanceType
    api_base_url: str
    credentials: MastodonCredentials
    status_params: MastodonStatusParams

    def __init__(
        self,
        app_name: str = None,
        instance_type: str = None,
        api_base_url: str = None,
        credentials: MastodonCredentials = None,
        status_params: MastodonStatusParams = None
    ) -> None:
        self.app_name = app_name
        self.instance_type = instance_type\
            if instance_type is not None else self.DEFAULT_INSTANCE_TYPE
        self.api_base_url = api_base_url
        self.credentials = credentials
        # Status Params has always to come, even with the default values
        if status_params is None:
            self.status_params = MastodonStatusParams()
        else:
            self.status_params = status_params

    def to_dict(self) -> dict:
        return {
            "app_name": self.app_name,
            "instance_type": self.instance_type,
            "api_base_url": self.api_base_url,
            "credentials": self.credentials.to_dict()
            if isinstance(self.credentials, MastodonCredentials) else None,
            "status_params": self.status_params.to_dict()
            if isinstance(self.status_params, MastodonStatusParams) else None
        }

    @staticmethod
    def from_dict(connection_params_dict: dict) -> MastodonConnectionParams:
        return MastodonConnectionParams(
            app_name=connection_params_dict["app_name"]
            if "app_name" in connection_params_dict else None,
            instance_type=MastodonInstanceType.valid_or_raise(
                connection_params_dict["instance_type"]
            ) if "instance_type" in connection_params_dict else None,
            api_base_url=connection_params_dict["api_base_url"]
            if "api_base_url" in connection_params_dict else None,
            credentials=MastodonCredentials.from_dict(connection_params_dict["credentials"])
            if "credentials" in connection_params_dict else None,
            status_params=MastodonStatusParams.from_dict(
                connection_params_dict["status_params"]
            ) if "status_params" in connection_params_dict and
            connection_params_dict["status_params"] is not None else None
        )


class MastodonCredentials():

    DEFAULT_USER_FILE = "user.secret"
    DEFAULT_CLIENT_FILE = "client.secret"

    user_file: str
    client_file: str
    user: MastodonUser

    def __init__(
        self,
        user_file: str = None,
        client_file: str = None,
        user: MastodonUser = None
    ) -> None:
        self.user_file = user_file\
            if user_file is not None else self.DEFAULT_USER_FILE
        self.client_file = client_file\
            if client_file is not None else self.DEFAULT_CLIENT_FILE
        self.user = user

    def to_dict(self) -> dict:
        return {
            "user_file": self.user_file,
            "client_file": self.client_file,
            "user": self.user.to_dict() if isinstance(self.user, MastodonUser) else None
        }

    @staticmethod
    def from_dict(credentials_dict: dict) -> MastodonCredentials:
        return MastodonCredentials(
            user_file=credentials_dict["user_file"]
            if "user_file" in credentials_dict else None,
            client_file=credentials_dict["client_file"]
            if "client_file" in credentials_dict else None,
            user=MastodonUser.from_dict(credentials_dict["user"])
            if "user" in credentials_dict else None
        )


class MastodonUser():

    email: str
    password: str

    def __init__(self, email: str = None, password: str = None) -> None:
        self.email = email
        self.password = password

    def to_dict(self) -> dict:
        return {"email": self.email, "password": self.password}

    @staticmethod
    def from_dict(credentials_dict: dict) -> MastodonUser:
        return MastodonUser(
            email=credentials_dict["email"] if "email" in credentials_dict else None,
            password=credentials_dict["password"] if "password" in credentials_dict else None
        )


class StatusPost:
    """
    Object to manage the status posts to be published through the Mastodon API.
    Mastodon.py wrapper version 1.8.0

    Should support Pleroma variations
    """

    status: str = None
    in_reply_to_id: int = None
    media_ids: list[int] = None
    sensitive: bool = None
    visibility: StatusPostVisibility = None
    spoiler_text: str = None
    language: str = None
    idempotency_key: str = None
    content_type: StatusPostContentType = None
    scheduled_at: datetime = None
    poll: any = None  # Poll not supported. It should be here a Poll object
    quote_id: int = None

    def __init__(
        self,
        status: str = None,
        in_reply_to_id: int = None,
        media_ids: list[int] = None,
        sensitive: bool = None,
        visibility: StatusPostVisibility = None,
        spoiler_text: str = None,
        language: str = None,
        idempotency_key: str = None,
        content_type: StatusPostContentType = None,
        scheduled_at: datetime = None,
        poll: any = None,
        quote_id: int = None
    ) -> None:

        self.status = status
        self.in_reply_to_id = in_reply_to_id
        self.media_ids = media_ids
        self.sensitive = sensitive if sensitive is not None else False
        self.visibility = visibility if visibility is not None\
            else StatusPostVisibility.PUBLIC
        self.spoiler_text = spoiler_text
        self.language = language
        self.idempotency_key = idempotency_key
        self.content_type = content_type if content_type is not None\
            else StatusPostContentType.PLAIN
        self.scheduled_at = scheduled_at
        self.poll = poll
        self.quote_id = quote_id

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "in_reply_to_id": self.in_reply_to_id,
            "media_ids": self.media_ids,
            "sensitive": self.sensitive,
            "visibility": self.visibility,
            "spoiler_text": self.spoiler_text,
            "language": self.language,
            "idempotency_key": self.idempotency_key,
            "content_type": self.content_type,
            "scheduled_at": self.scheduled_at.timestamp()
            if self.scheduled_at is not None else None,
            "poll": self.poll,
            "quote_id": self.quote_id,
        }

    def from_dict(status_post_dict: dict) -> StatusPost:
        return StatusPost(
            status_post_dict["status"] if "status" in status_post_dict else None,
            status_post_dict["in_reply_to_id"]
            if "in_reply_to_id" in status_post_dict else None,
            status_post_dict["media_ids"] if "media_ids" in status_post_dict else None,
            status_post_dict["sensitive"] if "sensitive" in status_post_dict else None,
            StatusPostVisibility.valid_or_raise(status_post_dict["visibility"])
            if "visibility" in status_post_dict else None,
            status_post_dict["spoiler_text"] if "spoiler_text" in status_post_dict else None,
            status_post_dict["language"] if "language" in status_post_dict else None,
            status_post_dict["idempotency_key"]
            if "idempotency_key" in status_post_dict else None,
            StatusPostContentType.valid_or_raise(status_post_dict["content_type"])
            if "content_type" in status_post_dict else None,
            datetime.fromtimestamp(status_post_dict["scheduled_at"])
            if "scheduled_at" in status_post_dict else None,
            status_post_dict["poll"] if "poll" in status_post_dict else None,
            status_post_dict["quote_id"] if "quote_id" in status_post_dict else None,
        )


class StatusPostVisibility:
    """
    The visibility parameter is a string value and accepts any of:

    "direct" - post will be visible only to mentioned users
    "private" - post will be visible only to followers
    "unlisted" - post will be public but not appear on the public timeline
    "public" - post will be public
    """
    DIRECT = "direct"
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"

    def valid_or_raise(value: str) -> StatusPostVisibility:
        valid_items = [
            StatusPostVisibility.DIRECT,
            StatusPostVisibility.PRIVATE,
            StatusPostVisibility.UNLISTED,
            StatusPostVisibility.PUBLIC
        ]

        if value not in valid_items:
            raise RuntimeError(f"Value [{value}] is not a valid StatusPostVisibility")

        return value


class StatusPostContentType:
    """
    Specific to “pleroma” feature set:: Specify content_type
    to set the content type of your post on Pleroma. It accepts:

    "text/plain" (default)
    "text/markdown"
    "text/html"
    "text/bbcode"

    This parameter is not supported on Mastodon servers, but will be safely ignored if set.
    """

    PLAIN = "text/plain"
    MARKDOWN = "text/markdown"
    HTML = "text/html"
    BBCODE = "text/bbcode"

    def valid_or_raise(value: str) -> StatusPostContentType:
        valid_items = [
            StatusPostContentType.PLAIN,
            StatusPostContentType.MARKDOWN,
            StatusPostContentType.HTML,
            StatusPostContentType.BBCODE
        ]

        if value not in valid_items:
            raise RuntimeError(f"Value [{value}] is not a valid StatusPostContentType")

        return value


class MastodonStatusParams():

    DEFAULT_MAX_LENGTH = 500
    DEFAULT_CONTENT_TYPE = StatusPostContentType.PLAIN
    DEFAULT_VISIBILITY = StatusPostVisibility.PUBLIC

    max_length: int
    content_type: StatusPostContentType
    visibility: StatusPostVisibility
    username_to_dm: str

    def __init__(
        self,
        max_length: int = None,
        content_type: StatusPostContentType = None,
        visibility: StatusPostVisibility = None,
        username_to_dm: str = None
    ) -> None:
        self.max_length = max_length if max_length is not None else self.DEFAULT_MAX_LENGTH
        self.content_type = StatusPostContentType.valid_or_raise(content_type)\
            if content_type is not None else self.DEFAULT_CONTENT_TYPE
        if visibility is None:
            self.visibility = self.DEFAULT_VISIBILITY
        else:
            self.visibility = StatusPostVisibility.valid_or_raise(visibility)
            if self.visibility == StatusPostVisibility.DIRECT\
               and username_to_dm is None:
                raise ValueError(
                    "The field username_to_dm is mandatory if visibility" +
                    f" is {StatusPostVisibility.DIRECT}"
                )
        self.username_to_dm = username_to_dm

    def to_dict(self) -> dict:
        return {
            "max_length": self.max_length,
            "content_type": self.content_type,
            "visibility": self.visibility,
            "username_to_dm": self.username_to_dm
        }

    @staticmethod
    def from_dict(status_params: dict) -> MastodonStatusParams:
        return MastodonStatusParams(
            max_length=status_params["max_length"] if "max_length" in status_params else None,
            content_type=status_params["content_type"]
            if "content_type" in status_params else None,
            visibility=status_params["visibility"] if "visibility" in status_params else None,
            username_to_dm=status_params["username_to_dm"]
            if "username_to_dm" in status_params else None
        )
