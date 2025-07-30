import logging
import requests
import os
import json


class Firefish:

    LOGGER_DEFAULT_NAME = "firefish_wrapper"

    bearer_token: str = None
    api_base_url: str = None
    client_name = None

    @staticmethod
    def create_app(client_name: str, api_base_url: str, to_file: str):
        '''
        Do we even need to register the app?
        Not really, but this approach help us to define the API url and
            have it stored in a file.

        So we emulate the behaviour in Mastodon.py:
            - Create / Overwrite a file.
            - Write the client_name
            - Write the api_base_url
        '''

        if client_name is None or \
           api_base_url is None or \
           to_file is None:
            raise RuntimeError("All params are mandatory")

        # Clean the given API base URL before keeping it in mem.
        if api_base_url[-1] == "/":
            api_base_url = api_base_url[:-1]

        # Write both. Order is important.
        with open(to_file, 'w') as file:
            file.write(api_base_url + "\n")
            file.write(client_name)

    def __init__(
        self,
        client_id: str = None,
        api_base_url: str = None,
        access_token: str = None,
        feature_set: str = None,
        logger: logging.Logger = None
    ):
        '''
        If client_id comes we expect to find a file called like client_id
            which contains the api_base_url.
        If access_token comes we expect to find a file called like access_token
            which contains both api_base_url and the user token from login.
        If api_base_url comes we just take it.
        We just ignore feature_set.

        This is just to emulate the 2 step init that we have with Mastodon.py
        '''

        # So we received a client_id,
        # this is actually a filename so read it and get the params.
        if client_id is not None:
            with open(client_id, 'r') as file:
                self.api_base_url = file.readline().strip()
                self.client_name = file.readline().strip()

        # So we received an access_token,
        # this is actually a filename so read it and get the params.
        if access_token is not None:
            with open(access_token, 'r') as file:
                self.api_base_url = file.readline().strip()
                self.client_name = file.readline().strip()
                self.bearer_token = file.readline().strip()

        if api_base_url is not None:
            self.api_base_url = api_base_url

        self._logger = logger if logger is not None else logging.getLogger(
            self.LOGGER_DEFAULT_NAME
        )

        # If we don't have a client_name, means that nothing came with. Error!
        if self.client_name is None and self.api_base_url is None:
            raise RuntimeError(
                "Mandatory params not found. Did you specify client_id or access_token?"
            )

    def log_in(self, username: str = None, password: str = None, to_file: str = None):
        '''
        I only need a Bearer token for authentication. Let's use "password" to receive it.
        If the method is called, I assume that the class instatiaton was using the client_id,
            so we should have already the client_id params in memory.
        If the to_file param is filled, we want to save the authentication into a file.
        '''
        if password is None:
            raise RuntimeError(
                "I need a Bearer token set into the 'password' param." +
                "Generate it and give it to me!"
            )

        self.bearer_token = password

        if to_file is not None:
            with open(to_file, 'w') as file:
                file.write(self.api_base_url + "\n")
                file.write(self.client_name + "\n")
                file.write(self.bearer_token)

    def __post_call(
        self,
        endpoint: str,
        headers: dict = {},
        json_data: dict = None,
        data: str = None,
        files: dict = None
    ):
        '''
        This is the method that proxies (and builds) all API POST calls.

        Take a look at this for extending to work with sessions:
            https://stackoverflow.com/a/37118451
        '''
        self._logger.debug(
            f"Calling {self.api_base_url}/{endpoint} with " +
            f"{len(json_data)} JSON data objects and {len(headers)+1} headers"
        )
        response = requests.post(
            url=f"{self.api_base_url}/{endpoint}",
            headers={
                **headers, **{
                    'Authorization': 'Bearer ' + self.bearer_token,
                }
            },
            json=json_data,
            data=data,
            files=files
        )

        if response.status_code == 200:
            return response.content
        else:
            raise RuntimeError(
                f"API Request ERROR -> {response.status_code}: {response.reason}"
            )

    def status_post(
        self,
        status: str,
        in_reply_to_id=None,
        media_ids=None,
        sensitive=False,
        visibility=None,
        spoiler_text=None,
        language=None,
        idempotency_key=None,
        content_type=None,
        scheduled_at=None,
        poll=None,
        quote_id=None
    ):
        '''
        Post a status. Can optionally be in reply to
            another status and contain media.

        media_ids should be a list. (If it’s not, the function
            will turn it into one.) It can contain up to four
            pieces of media (uploaded via media_post()).
            media_ids can also be the `media dicts`_
            returned by media_post() - they are unpacked
            automatically.

        [to implement] The sensitive boolean decides whether
            or not media attached to the post should be marked
            as sensitive, which hides it by default on the
            Mastodon web front-end.

        The visibility parameter is a string value and
            accepts any of: ‘direct’ - post will be visible
            only to mentioned users ‘private’ - post will be
            visible only to followers ‘unlisted’ - post will be
            public but not appear on the public timeline
            ‘public’ - post will be public

        If not passed in, visibility defaults to match the
            current account’s default-privacy setting
            (starting with Mastodon version 1.6) or its locked
            setting - private if the account is locked,
            public otherwise (for Mastodon versions lower than 1.6).

        [to implement] The spoiler_text parameter is a string to be
            shown as a warning before the text of the status.
            If no text is passed in, no warning will be displayed.

        Specify language to override automatic language detection.
            The parameter accepts all valid ISO 639-1 (2-letter)
            or for languages where that do not have one,
            639-3 (three letter) language codes.

        [to implement] You can set idempotency_key to a value to
            uniquely identify an attempt at posting a status.
            Even if you call this function more than once,
            if you call it with the same idempotency_key,
            only one status will be created.

        [to implement] Pass a datetime as scheduled_at to schedule
            the toot for a specific time (the time must be
            at least 5 minutes into the future). If this is passed,
            status_post returns a scheduled status dict instead.

        [to implement] Pass poll to attach a poll to the status.
            An appropriate object can be constructed using make_poll().
            Note that as of Mastodon version 2.8.2, you can only
            have either media or a poll attached, not both at the same time.

        [to implement] Specific to “pleroma” feature set::
            Specify content_type to set the content type of your
            post on Pleroma. It accepts ‘text/plain’ (default),
            ‘text/markdown’, ‘text/html’ and ‘text/bbcode’.
            This parameter is not supported on Mastodon servers,
            but will be safely ignored if set.

        [to implement] Specific to “fedibird” feature set::
            The quote_id parameter is a non-standard extension
            that specifies the id of a quoted status.

        [to implement] Returns a status dict with the new status.

        https://firefish.social/api-doc#operation/notes/create
        '''
        ENDPOINT = "api/notes/create"

        if status is None:
            raise RuntimeError("Field 'status' is mandatory")

        # Text is mandatory
        json_data = {
            "text": status,
        }

        # Do we have files?
        if media_ids is not None:
            json_data["fileIds"] = media_ids

        # Do we control visibility?
        if visibility is not None:
            # Translate the values from Mastodon to Firefish
            firefish_values_by_mastodon = {
                "public": "public",  # "": "home",
                "private": "followers",
                "direct": "specified",
                "unlisted": "hidden"
            }
            json_data["visibility"] = firefish_values_by_mastodon[visibility]

        # Do we define the language?
        if language is not None:
            json_data["lang"] = str(language).replace("_", "-")

        # Is this a reply to another status?
        if in_reply_to_id is not None:
            json_data["replyId"] = in_reply_to_id

        # Make the call
        result = self.__post_call(endpoint=ENDPOINT, json_data=json_data)

        # (dict[1]){
        #     "createdNote": (dict[17]){
        #         "id": (str[16])"9lxgx1y4qk9qi1vv",
        #         "createdAt": (str[24])"2023-11-11T10:28:25.756Z",
        #         "userId": (str[16])"9kdeh1m4mvk02stu",
        #         "user": (dict[14]){
        #         "id": (str[16])"9kdeh1m4mvk02stu",
        #         "name": (str[4])"Test",
        #         "username": (str[4])"test",
        #         "host": (NoneType)None,
        #         "avatarUrl": (str[96])"https://cdn.devnamic.com/social." +
        #           "devnamic.com/thumbnail-ed661faa-591c-4204-9356-9884c56a735a.webp",
        #         "avatarBlurhash": (str[102])"yJH-e*t606WYoJkCR-03WVIUWB-" +
        #           "ijsjs0qWX~2jrxvoeI]=;oLt7j@EmbIRPIvazNIa}WAWW-3xVjZxYj" +
        #           "[WrfPS6Itayayj[sljsR+",
        #         "avatarColor": (NoneType)None,
        #         "isBot": (bool)True,
        #         "isLocked": (bool)False,
        #         "isIndexable": (bool)True,
        #         "speakAsCat": (bool)True,
        #         "emojis": (list[0])[],
        #         "onlineStatus": (str[7])"offline",
        #         "driveCapacityOverrideMb": (NoneType)None
        #         },
        #         "text": (str[407])"Lorem ipsum dolor sit amet, consectetur" +
        #           " adipiscing elit. Nunc ac congue turpis, eu facilisis " +
        #           "lacus. Sed augue felis, posuere vitae ex in, luctus " +
        #           "lacinia erat. Nulla quis tempor nibh, sed placerat erat." +
        #           " Sed ac diam a orci dictum convallis nec a ex. Vestibulum" +
        #           " a metus in lorem malesuada finibus sit amet ut nisi. " +
        #           "Etiam vel arcu in metus gravida mattis. In ipsum felis," +
        #           " molestie sollicitudin feugiat se

        #     (1/3)",
        #         "cw": (NoneType)None,
        #         "visibility": (str[6])"public",
        #         "renoteCount": (int)0,
        #         "repliesCount": (int)0,
        #         "reactions": (dict[0]){},
        #         "reactionEmojis": (list[0])[],
        #         "emojis": (list[0])[],
        #         "fileIds": (list[1])[(str[16])"9lxgx1dteouqeio9"],
        #         "files": (list[1])[
        #         (dict[16]){
        #             "id": (str[16])"9lxgx1dteouqeio9",
        #             "createdAt": (str[24])"2023-11-11T10:28:25.025Z",
        #             "name": (str[4])"file",
        #             "type": (str[10])"image/jpeg",
        #             "md5": (str[32])"6fdd2bebd3bebfc45e1d8a1a50b9ea9c",
        #             "size": (int)88674,
        #             "isSensitive": (bool)False,
        #             "blurhash": (str[102])"ytMQ*KWB%Mof%Mt7xu~qWBs:ayays;" +
        #               "RjD%ofj]j[j[WBofkCj[WBazoLoLbH-:aya}f6WVbHaxNGj[ofa" +
        #               "{oLjZa}ayoLWBfka}WVj[",
        #             "properties": (dict[2]){"width": (int)598, "height": (int)771},
        #             "url": (str[85])"https://cdn.devnamic.com/social.devnamic" +
        #               ".com/74cefbcd-ec3b-44bb-a529-7862e8a6892c.jpg",
        #             "thumbnailUrl": (str[96])"https://cdn.devnamic.com/social." +
        #               "devnamic.com/thumbnail-91b86dee-2d03-43a1-b421-f9653e54" +
        #               "f879.webp",
        #             "comment": (NoneType)None,
        #             "folderId": (NoneType)None,
        #             "folder": (NoneType)None,
        #             "userId": (NoneType)None,
        #             "user": (NoneType)None
        #         }
        #         ],
        #         "replyId": (NoneType)None,
        #         "renoteId": (NoneType)None,
        #         "lang": (str[2])"la"
        #     }
        # }

        # Prepare the result and return
        result = json.loads(result)
        if "createdNote" in result:
            return result["createdNote"]
        else:
            return result

    def media_post(
        self,
        media_file,
        mime_type=None,
        description=None,
        focus=None,
        file_name=None,
        thumbnail=None,
        thumbnail_mime_type=None,
        synchronous=False
    ):
        """
        Post an image, video or audio file.

        media_file is the binary content. Can either be data as binary
            or a file name as string.

        [to implement] mime_type is the Mime Type of the media_file.
            If data is passed directly, the mime type has to be specified
            manually, otherwise, it is determined from the file name.

        [to implement] focus should be a tuple of floats between -1 and 1,
            giving the x and y coordinates of the images focus point for cropping
            (with the origin being the images center).

        [to implement] Throws a MastodonIllegalArgumentError if the mime type of the
            passed data or file can not be determined properly.

        file_name can be specified to upload a file with the given name, which
            is ignored by Mastodon, but some other Fediverse server software
            will display it. If no name is specified, a random name will be
            generated. The filename of a file specified in media_file will be
            ignored.

        [to implement] Starting with Mastodon 3.2.0, thumbnail can be specified in the
            same way as media_file to upload a custom thumbnail image for audio
            and video files.

        Returns a media dict. This contains the id that can be used in status_post
            to attach the media file to a toot.

        https://firefish.social/api-doc#operation/drive/files/create
        """

        ENDPOINT = "api/drive/files/create"

        if media_file is None:
            raise RuntimeError("Field 'media_file' is mandatory")

        # The content of the file is mandatory, but goes set in the files section.
        json_data = {}

        if isinstance(media_file, str):
            content = None
            # So we have the filename, we need to open the file in binary mode
            with open(media_file, 'rb') as file:
                content = file.read()

            json_data["name"] = os.path.basename(media_file)
            media_file = content

        elif not isinstance(media_file, bytes):
            raise RuntimeError("Field 'media_file' does not seem to be a string of bytes")

        # Do we have a file_name?
        # Still, it seems to be ignored in the firefish side.
        if file_name is not None:
            json_data["name"] = file_name

        # Do we have a description?
        if description is not None:
            json_data["comment"] = description

        # Make the call
        result = self.__post_call(
            endpoint=ENDPOINT, json_data=json_data, files={"file": media_file}
        )

        # (dict[16]){
        #   "id": (str[16])"9luwyawuhi3hf43i",
        #   "createdAt": (str[24])"2023-11-09T15:33:59.358Z",
        #   "name": (str[4])"file",
        #   "type": (str[10])"image/jpeg",
        #   "md5": (str[32])"9dd5f75501ee4d795610470d76ef702c",
        #   "size": (int)53746,
        #   "isSensitive": (bool)False,
        #   "blurhash": (str[102])"yeL4ytof-;t7%Mxut7D%ofRjWBRjj[WB~qj[M{j[WBWBWBD" +
        #         "%oft7oft7WBt7RjRjfPayM{j[jtxuayj[oft7ofayRjj[ayayayayay",
        #   "properties": (dict[2]){"width": (int)800, "height": (int)533},
        #   "url": (str[85])"https://cdn.devnamic.com/social.devnamic.com/" +
        #         "d86fb425-d090-4699-9ed4-a10f540e64e4.jpg",
        #   "thumbnailUrl": (str[96])"https://cdn.devnamic.com/social.devnamic.com/" +
        #         "thumbnail-c7088923-7051-4dc0-8620-079bf59d04f1.webp",
        #   "comment": (NoneType)None,
        #   "folderId": (NoneType)None,
        #   "folder": (NoneType)None,
        #   "userId": (NoneType)None,
        #   "user": (NoneType)None
        # }

        # Prepare the result and return
        return json.loads(result)
