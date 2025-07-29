from .. import login, http_client
import json

class Publish:
    def __init__(self, media_path: list = None, text = None) -> None:
        """
        initialize the Publish object

        parameters:
        - media_path (list): A list of file paths for the media to be uploaded.
        - text (str): The text content of the status to be posted
        """
        self.login = login
        self.path = media_path
        self.text = text
        self.media_upload_url = 'https://mastodon.social/api/v2/media'
        self.upload_status = 'https://mastodon.social/api/v1/statuses'
        self.total_upload = []

    def upload_media(self) -> list:
        """
        uploads all media files in self.path to Mastodon

        returns:
        - list: a list of media ids that were successfully uploaded
        """
        for media in self.path:
            with open(media, 'rb') as file:
                response = http_client.rq_post(
                    self.media_upload_url, headers=self.login, files={'file': file}
                )
                self.total_upload.append(json.loads(response.text)['id'])
        return (self.total_upload)

    def status(self) -> list:
        """
        creates a new status (post) on Mastodon.
        if media is included, it uploads the media first and attaches it to the post
        """
        data = {
            "status": self.text,
            "in_reply_to_id": None,
            "sensitive": False,
            "spoiler_text": "",
            "visibility": "public",
            "poll": None,
            "language": "en"
        }
        if self.path is not None:
            data["media_ids"] = self.upload_media()
            
        response = http_client.rq_post(
            self.upload_status, headers=self.login, json=data
        )
        return (json.loads(response.text))
