from __future__ import annotations
from pyxavi import Config, Media, TerminalColor
from .mastodon_helper import MastodonHelper, StatusPost,\
    MastodonConnectionParams, MastodonInstanceType
from logging import Logger
import time


class MastodonPublisher:
    '''
    MastodonPublisherException

    It is responsible to publish status posts.
    '''

    MAX_RETRIES = 3
    SLEEP_TIME = 10
    DEFAULT_NAMED_ACCOUNT = "default"

    def __init__(
        self,
        config: Config,
        logger: Logger,
        named_account: str = None,
        base_path: str = None
    ) -> None:
        self._config = config
        self._logger = logger
        self._base_path = base_path

        self.load_connection_params(named_account=named_account)
        self.load_mastodon_instance()

        self._is_dry_run = config.get("publisher.dry_run", False)
        self._media_storage = config.get("publisher.media_storage")

    def load_connection_params(self, named_account=None) -> None:
        if named_account is None:
            named_account = self._config.get(
                "publisher.named_account", self.DEFAULT_NAMED_ACCOUNT
            )
        self._connection_params = MastodonConnectionParams.from_dict(
            self._config.get(f"mastodon.named_accounts.{named_account}")
        )

    def load_mastodon_instance(self) -> None:
        self._mastodon = MastodonHelper.get_instance(
            connection_params=self._connection_params,
            logger=self._logger,
            base_path=self._base_path
        )

    def publish_text(self, text: str) -> dict:
        return self.publish_status_post(
            status_post=StatusPost(
                status=text,
                visibility=self._connection_params.status_params.visibility,
                content_type=self._connection_params.status_params.content_type,
            )
        )

    def publish_media(self, media: list = None) -> list:
        if self._is_dry_run:
            self._logger.debug("It's a Dry Run, not publishing Media.")
            return None

        self._logger.info(
            f"{TerminalColor.CYAN}Publishing %s media items{TerminalColor.END}", len(media)
        )
        posted_media = []
        for item in media:
            shall_download = True
            if "url" in item and item["url"] is not None:
                media_file = item["url"]
            elif "path" in item and item["path"] is not None:
                media_file = item["path"]
                shall_download = False

            else:
                self._logger.warning(
                    f"{TerminalColor.RED}the Media to post does " +
                    f"not have an URL or a PATH{TerminalColor.END}"
                )
                continue
            posted_result = self._do_media_publish(
                media_file=media_file,
                download_file=shall_download,
                description=item["alt_text"] if "alt_text" in item else None,
                mime_type=item["mime_type"] if "mime_type" in item else None
            )
            if posted_result:
                posted_media.append(posted_result["id"])
            else:
                self._logger.info(
                    f"{TerminalColor.RED}Could not post %s{TerminalColor.END}", media_file
                )

        return posted_media

    def publish_status_post(self, status_post: StatusPost, media: list = None) -> dict:
        if self._is_dry_run:
            self._logger.debug("It's a Dry Run, not publishing StatusPost.")
            return None

        if media is not None and len(media) > 0:
            posted_media = self.publish_media(media=media)
            if len(posted_media) > 0:
                status_post.media_ids = posted_media

        # Let's ensure that it fits according to the params
        status_post.status = self.__slice_status_if_longer_than_defined(
            status=status_post.status
        )

        # Avoid posting if there's no image AND no body
        if (status_post.media_ids is None or len(status_post.media_ids) == 0)\
           and len(status_post.status) == 0:
            self._logger.warning("No media AND no body, skipping this post")
            return None

        retry = 0
        published = None
        while published is None:
            try:
                self._logger.info(
                    f"{TerminalColor.CYAN}Publishing new post (retry {retry}) for " +
                    f"instance type {self._connection_params.instance_type} and account " +
                    f"{self._connection_params.app_name}{TerminalColor.END}"
                )
                published = self._do_status_publish(status_post=status_post)
                return published
            except Exception as e:
                self._logger.exception(e)
                self._logger.debug(f"sleeping {self.SLEEP_TIME} seconds")
                time.sleep(self.SLEEP_TIME)
                retry += 1
                if retry >= self.MAX_RETRIES:
                    self._logger.error(
                        f"{TerminalColor.RED_BRIGHT}MAX RETRIES of {self.MAX_RETRIES}" +
                        f" is reached. Stop trying.{TerminalColor.END}"
                    )
                    raise MastodonPublisherException(f"Could not publish the post: {e}")

    def _do_status_publish(self, status_post: StatusPost) -> dict:
        """
        This is the method that executes the post of the status.

        No checks, no validations, just the action.
        """

        if self._connection_params.instance_type == MastodonInstanceType.MASTODON:
            published = self._mastodon.status_post(
                status=status_post.status,
                in_reply_to_id=status_post.in_reply_to_id,
                media_ids=status_post.media_ids,
                sensitive=status_post.sensitive,
                visibility=status_post.visibility,
                spoiler_text=status_post.spoiler_text,
                language=status_post.language,
                idempotency_key=status_post.idempotency_key,
                scheduled_at=status_post.scheduled_at,
                poll=status_post.poll
            )
        elif self._connection_params.instance_type == MastodonInstanceType.PLEROMA:
            published = self._mastodon.status_post(
                status=status_post.status,
                in_reply_to_id=status_post.in_reply_to_id,
                media_ids=status_post.media_ids,
                sensitive=status_post.sensitive,
                visibility=status_post.visibility,
                spoiler_text=status_post.spoiler_text,
                language=status_post.language,
                idempotency_key=status_post.idempotency_key,
                content_type=status_post.content_type,
                scheduled_at=status_post.scheduled_at,
                poll=status_post.poll,
                quote_id=status_post.quote_id
            )
        elif self._connection_params.instance_type == MastodonInstanceType.FIREFISH:
            published = self._mastodon.status_post(
                status=status_post.status,
                in_reply_to_id=status_post.in_reply_to_id,
                media_ids=status_post.media_ids,
                sensitive=status_post.sensitive,
                visibility=status_post.visibility,
                spoiler_text=status_post.spoiler_text,
                language=status_post.language,
                idempotency_key=status_post.idempotency_key,
                content_type=status_post.content_type,
                scheduled_at=status_post.scheduled_at,
                poll=status_post.poll,
                quote_id=status_post.quote_id
            )
        else:
            raise RuntimeError(f"Unknown instance type {self._connection_params.instance_type}")
        return published

    def _do_media_publish(
        self,
        media_file: str,
        download_file: bool,
        description: str,
        mime_type: str = None
    ) -> dict:
        try:
            if download_file is True:
                downloaded = Media().download_from_url(media_file, self._media_storage)
            else:
                downloaded = {"file": media_file, "mime_type": mime_type}
            return self._mastodon.media_post(
                downloaded["file"],
                mime_type=downloaded["mime_type"],
                description=description,
                focus=(0, 1)
            )
        except Exception as e:
            self._logger.exception(e)

    def __slice_status_if_longer_than_defined(self, status: str) -> str:
        max_length = self._connection_params.status_params.max_length
        if len(status) > max_length:
            self._logger.debug(
                f"The status post is longer than the max length of {max_length}. Cutting..."
            )
            status = status[:max_length - 3] + "..."

        return status


class MastodonPublisherException(BaseException):
    pass
