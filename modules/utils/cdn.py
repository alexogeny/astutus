import io
import mimetypes
import aioboto3


class CDN(object):
    def __init__(self, host: str, space: str, access_key: str, secret_key: str):
        self.host = f"https://i.{host}/"
        self.space = space
        self.session = aioboto3.Session()
        self.client = self.session.client(
            "s3",
            region_name="sfo2",
            endpoint_url="https://sfo2.digitaloceanspaces.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    async def upload_file(self, kind, objid, contents):
        full_path = f"{kind}/{objid}/{contents.filename}"
        data = await contents.read()
        with io.BytesIO(data) as img:
            await self.client.upload_fileobj(
                img,
                self.space,
                full_path,
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": mimetypes.guess_type(contents.filename)[0],
                },
            )
        return f"{self.host}{full_path}"
