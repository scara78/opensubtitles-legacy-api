# SubDL Integration

This document explains how to use the SubDL integration feature in the OpenSubtitles Legacy API.

## Overview

The OpenSubtitles Legacy API now supports merging subtitles from both OpenSubtitles and SubDL providers. When you provide a SubDL API key, the system will search both providers and return combined results.

## How It Works

1. **Primary Search**: The system first searches OpenSubtitles using your OpenSubtitles API key
2. **Secondary Search**: If a SubDL API key is provided, it also searches SubDL
3. **Result Merging**: Results from both providers are combined and returned together
4. **Provider Identification**: Each result includes a "Provider" field to identify the source
5. **Scoring**: OpenSubtitles results get higher scores (10.0-9.x) while SubDL results get lower scores (5.0-4.x)

## Usage

### Basic Request (OpenSubtitles only)

```
GET /search/imdbid-tt0133093/sublanguageid-eng?apiKey=YOUR_OPENSUBTITLES_KEY
```

### Enhanced Request (OpenSubtitles + SubDL)

```
GET /search/imdbid-tt0133093/sublanguageid-eng?apiKey=YOUR_OPENSUBTITLES_KEY&subdlKey=YOUR_SUBDL_KEY
```

### Example with Python requests

```python
import requests

# Basic search (OpenSubtitles only)
response = requests.get(
    "http://localhost:8000/search/imdbid-tt0133093/sublanguageid-eng",
    params={
        "apiKey": "your_opensubtitles_key"
    }
)

# Enhanced search (OpenSubtitles + SubDL)
response = requests.get(
    "http://localhost:8000/search/imdbid-tt0133093/sublanguageid-eng",
    params={
        "apiKey": "your_opensubtitles_key",
        "subdlKey": "your_subdl_key"
    }
)
```

## API Keys

### OpenSubtitles API Key

- **Required**: Yes
- **How to get**: Sign up at https://opensubtitles.com and go to your account settings
- **Parameter**: `apiKey`

### SubDL API Key

- **Required**: No (optional for enhanced results)
- **How to get**: Sign up at https://subdl.com and find it in your account settings
- **Parameter**: `subdlKey`

## Response Format

The response format remains compatible with the original OpenSubtitles legacy API, but now includes:

### New Fields

- `Provider`: Indicates the source ("OpenSubtitles" or "SubDL")

### Example Response

```json
[
  {
    "IDSubtitleFile": "1234567",
    "SubFileName": "Movie.2023.1080p.BluRay.x264-GROUP.srt",
    "SubLanguageID": "eng",
    "LanguageName": "English",
    "Provider": "OpenSubtitles",
    "Score": 10.0,
    "SubDownloadLink": "http://localhost:8000/download/file/1234567",
    "ZipDownloadLink": "http://localhost:8000/download/zip/1234567",
    ...
  },
  {
    "IDSubtitleFile": "subdl_987654321_0",
    "SubFileName": "Movie.2023.WEB-DL.x264-ANOTHER.srt",
    "SubLanguageID": "eng",
    "LanguageName": "English",
    "Provider": "SubDL",
    "Score": 5.0,
    "SubDownloadLink": "http://localhost:8000/download/file/subdl_987654321_0",
    "ZipDownloadLink": "http://localhost:8000/download/zip/subdl_987654321_0",
    ...
  }
]
```

## Language Mapping

The system automatically maps OpenSubtitles language codes to SubDL language codes:

| OpenSubtitles Code | SubDL Language Code | Language Name         |
| ------------------ | ------------------- | --------------------- |
| eng                | EN                  | English               |
| spa                | ES                  | Spanish               |
| fre                | FR                  | French                |
| ger                | DE                  | German                |
| ita                | IT                  | Italian               |
| por                | PT                  | Portuguese            |
| pob                | BR_PT               | Brazilian Portuguese  |
| rus                | RU                  | Russian               |
| chi                | ZH                  | Chinese               |
| zht                | ZH_BG               | Chinese (Traditional) |
| jpn                | JA                  | Japanese              |
| kor                | KO                  | Korean                |
| ara                | AR                  | Arabic                |
| hin                | HI                  | Hindi                 |
| tha                | TH                  | Thai                  |
| vie                | VI                  | Vietnamese            |
| ind                | ID                  | Indonesian            |
| may                | MS                  | Malay                 |
| fil                | TL                  | Tagalog/Filipino      |
| dut                | NL                  | Dutch                 |
| swe                | SV                  | Swedish               |
| nor                | NO                  | Norwegian             |
| dan                | DA                  | Danish                |
| fin                | FI                  | Finnish               |
| pol                | PL                  | Polish                |
| cze                | CS                  | Czech                 |
| hun                | HU                  | Hungarian             |
| rum                | RO                  | Romanian              |
| bul                | BG                  | Bulgarian             |
| hrv                | HR                  | Croatian              |
| srp                | SR                  | Serbian               |
| ukr                | UK                  | Ukrainian             |
| gre                | EL                  | Greek                 |
| tur                | TR                  | Turkish               |
| per                | FA                  | Persian/Farsi         |
| heb                | HE                  | Hebrew                |
| cat                | CA                  | Catalan               |
| slo                | SK                  | Slovak                |
| slv                | SL                  | Slovenian             |

**Note**: Some languages supported by OpenSubtitles may not be available in SubDL. In such cases, SubDL search will be skipped for those languages.

## Caching

- Results are cached separately for requests with and without SubDL
- Cache keys include the SubDL API key status to ensure correct caching behavior
- Cached results expire after 24 hours

## Download Endpoints

Both OpenSubtitles and SubDL subtitles are downloaded through the same endpoints:

- `/download/file/{file_id}` - Download subtitle file (.srt)
- `/download/zip/{file_id}` - Download zipped subtitle file

SubDL file IDs are prefixed with `subdl_` to distinguish them from OpenSubtitles IDs.

## Error Handling

- If OpenSubtitles API fails, the system will still attempt to search SubDL (if key provided)
- If SubDL API fails, only OpenSubtitles results are returned
- Invalid SubDL API keys are handled gracefully without affecting OpenSubtitles search

## Performance Notes

- Adding SubDL search increases response time as it requires additional API calls
- SubDL files are downloaded and cached locally, same as OpenSubtitles files
- Results are processed in parallel where possible to minimize latency

## Testing

Use the provided test script to verify integration:

```bash
python test_subdl_integration.py
```

Make sure to update the API keys in the test script before running.

## Troubleshooting

### No SubDL Results

1. Verify your SubDL API key is correct
2. Check that the movie/TV show exists in SubDL database
3. Ensure the language is supported by SubDL

### SubDL Downloads Failing

1. Check SubDL API status
2. Verify download URLs are accessible
3. Check local storage permissions

### Mixed Results Issues

1. Compare response with and without SubDL key
2. Check the "Provider" field in results
3. Review server logs for detailed error messages
