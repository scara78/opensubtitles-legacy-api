# OpenSubtitles Legacy API

A FastAPI-based proxy service that provides backward compatibility with the old OpenSubtitles REST API while using the new OpenSubtitles JSON API under the hood. This service allows legacy applications to continue working without modification while leveraging the modern OpenSubtitles API.

## Features

- **Legacy API Compatibility**: Emulates the old OpenSubtitles REST API format
- **Modern Backend**: Uses the new OpenSubtitles JSON API for data retrieval
- **Local Caching**: Downloads and stores subtitle files locally for faster access
- **Search Caching**: Caches search results to reduce API calls
- **Multiple Download Formats**: Serves both raw `.srt` files and compressed `.zip` archives
- **Language Support**: Full language mapping between old and new API formats
- **Docker Ready**: Containerized deployment with Docker Compose
- **Tailscale Integration**: Built-in support for expose the API with Tailscale Funnel

## API Endpoints

### Search Subtitles

- **TV Episodes**: `/search/episode-{episode}/imdbid-tt{imdb_id}/season-{season}/sublanguageid-{language}`
- **Movies**: `/search/imdbid-tt{imdb_id}/sublanguageid-{language}`

### Download Files

- **Raw File**: `/download/file/{file_id}` - Returns the subtitle file as `.srt`
- **Zipped File**: `/download/zip/{file_id}` - Returns the subtitle file as `.zip`

## Requirements

- Docker and Docker Compose
- OpenSubtitles API key (get one at [opensubtitles.com](https://opensubtitles.com))
- Tailscale account

## Installation

### 1. Download Required Files

Download the following files from the [Releases](../../releases) page:

- `opensubtitles_legacy_api-{version}-py3-none-any.whl` (Python wheel file)
- `compose.yml` (Docker Compose configuration)
- `Dockerfile` (Docker build configuration)
- `serve-config.json` (Server configuration)
- `start.sh` (Startup script)
- `supervisord.conf` (Process supervisor configuration)

### 2. Environment Configuration

Copy the environment template and configure it:

```bash
cp .env.example .env
```

Edit `.env` file:

```bash
# BASE URL for the API - MUST match your Tailscale funnel or public URL
BASE_URL=https://your-tailscale-domain.ts.net
# API ENVIRONMENT: production/development
ENVIRONMENT=production
```

> **Important**: The `BASE_URL` must match the URL where your service will be accessible, especially if using Tailscale funnel.

### 3. Tailscale Configuration

Edit `compose.yml` and replace the Tailscale auth key:

```yaml
environment:
  - TS_AUTHKEY=tskey-auth-YOUR_ACTUAL_AUTH_KEY_HERE
```

Get your Tailscale auth key from [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys).

### 4. Create Required Directories

Create the necessary directories for data storage:

```bash
mkdir -p data subtitles logs
```

### 5. Deploy with Docker Compose

Start the services:

```bash
docker compose up -d
```

## Usage

### Basic API Call

Using the legacy API format with your OpenSubtitles API key:

```bash
# Search for movie subtitles
curl "http://your-domain/search/imdbid-tt0133093/sublanguageid-eng?apiKey=YOUR_API_KEY"

# Search for TV episode subtitles
curl "http://your-domain/search/episode-1/imdbid-tt0944947/season-1/sublanguageid-eng?apiKey=YOUR_API_KEY"
```

### Download Subtitles

```bash
# Download raw subtitle file
curl "http://your-domain/download/file/12345678" -o subtitle.srt

# Download zipped subtitle file
curl "http://your-domain/download/zip/12345678" -o subtitle.zip
```

### Language Codes

The service supports both old and new language codes:

- `eng` → `en` (English)
- `fre` → `fr` (French)
- `ger` → `de` (German)
- `spa` → `es` (Spanish)
- And many more...

## Configuration Options

### Environment Variables

| Variable      | Description                            | Default                 |
| ------------- | -------------------------------------- | ----------------------- |
| `BASE_URL`    | Public URL where the API is accessible | `http://localhost:8000` |
| `ENVIRONMENT` | Runtime environment                    | `production`            |

### Docker Volumes

The service uses several volumes for persistent data:

- `./data` → `/app/data` - Database files and cache
- `./subtitles` → `/app/subtitles` - Downloaded subtitle files
- `./logs` → `/app/logs` - Application logs
- `ts_state` - Tailscale state (managed by Docker)

### Database Stats

The service automatically maintains statistics about:

- Cached subtitle files
- Search result cache
- Storage usage

### Cleanup

The service automatically cleans up old files (30+ days) to manage disk space.

## Troubleshooting

### Common Issues

1. **Service not accessible**: Check that `BASE_URL` in `.env` matches your access URL
2. **Tailscale auth issues**: Verify your `TS_AUTHKEY` is valid and not expired
3. **Permission errors**: Ensure directories have proper write permissions
4. **API key errors**: Verify your OpenSubtitles API key is valid

### Debug Mode

Enable development mode for detailed logging:

```bash
# In .env file
ENVIRONMENT=development
```

## Development

### Local Development Setup

1. Install dependencies:

```bash
uv sync
```

2. Run the development server:

```bash
uv run uvicorn ola.main:app --reload --host 0.0.0.0 --port 8000
```

### Building the Wheel

```bash
uv build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
