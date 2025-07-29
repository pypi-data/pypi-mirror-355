import requests
from typing import Literal


class CobaltAPI:
    def __init__(
        self,
        api_url: str = "https://co.itsv1eds.ru/",
        token: str = None
        ):
        self.api_url = api_url
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if token:
            assert token.startswith(("Bearer ", "Api-Key ")), \
            'The token must start with "Bearer " or "Api-Key ".'
            self.handlers["Authorization"] = token
        self.options = {}

    def quality(self, quality: Literal["max", "4320", "2160", "1440", "1080", "720", "480", "360", "240", "144"]):
        self.options['videoQuality'] = quality

    def filename_pattern(self, pattern: Literal["classic", "pretty", "basic", "nerdy"]):
        self.options['filenameStyle'] = pattern

    def vcodec(self, codec: Literal["h264", "av1", "vp9"]):
        self.options['youtubeVideoCodec'] = codec

    def aformat(self, aformat: Literal["best", "mp3", "ogg", "wav", "opus"]):
        self.options['audioFormat'] = aformat
        
    def mode(self, mode: Literal["audio", "mute", "auto"]):
        self.options['downloadMode'] = mode
    
    def services(self) -> list:
        response = requests.get(self.api_url)
        response.raise_for_status()
        data = response.json()
        return data["cobalt"]["services"]
    
    def tunnel(self, url: str) -> str:
        data = {'url': url}
        data.update(self.options)
        response = requests.post(
            self.api_url,
            json=data,
            headers=self.headers
            )
        return response.json()["url"]
        
    def download(self, url: str) -> str:
        data = {'url': url}
        data.update(self.options)
        response = requests.post(
            self.api_url,
            json=data,
            headers=self.headers
            )
        response.raise_for_status()
        result = response.json()
        with requests.get(result["url"], stream=True) as r:
            r.raise_for_status()
            with open(result["filename"], "wb") as f:
                f.write(r.content)
        return result["filename"]