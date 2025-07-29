# Kobalt
Working with Cobalt API

# Methods
| Method             | Usage                                                                               | Arguments (allowed values)                                                                                  |
|--------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `CobaltApi`         | Class constructor, initializes API URL, headers, and optional token                 | `api_url: str = "https://co.itsv1eds.ru/"`, `token: str = None`                                            |
| `quality`          | Set the desired video quality                                                       | `quality: str` — only "max", "4320", "2160", "1440", "1080", "720", "480", "360", "240", "144"             |
| `filename_pattern` | Set the filename style for downloads                                                | `pattern: str` — only "classic", "pretty", "basic", "nerdy"                                                |
| `vcodec`           | Set the preferred video codec                                                       | `codec: str` — only "h264", "av1", "vp9"                                                                   |
| `aformat`          | Set the audio format                                                                | `aformat: str` — only "best", "mp3", "ogg", "wav", "opus"                                                  |
| `mode`             | Set the download mode (audio only, muted video, or auto)                            | `mode: str` — only "audio", "mute", "auto"                                                                 |
| `services`         | Retrieve the list of supported services/platforms                                   | —                                                                                                           |
| `tunnel`           | Get a direct download link for the file via the API                                 | `url: str`                                                                                                  |
| `download`         | Download the file using the API and save it locally                                 | `url: str`                                                                                                  |



# Example of use
<pre language="python">  from Kobalt import CobaltApi

  cobalt = CobaltApi()
  cobalt.filename_pattern("classic") # Not necessarily
  result = cobalt.download("https://example.com/OOOOO/")
  print(f"Downloaded! File Name: {result}")
</pre>

