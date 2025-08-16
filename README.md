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
- **Tailscale Integration**: Built-in support for secure networking with Tailscale serve

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

- `compose.yml` (Docker Compose configuration)
- `serve-config.json` (Tailscale serve configuration)
- `.env.example` (Environment template)

> **Note**: The application is now available as a pre-built Docker image at `ghcr.io/kd-mm2/ola:0.1.0`, so you no longer need to download additional build files or build locally.

### 2. Environment Configuration

Copy the environment template and configure it:

```bash
cp .env.example .env
```

Edit `.env` file:

```bash
# BASE URL for the API - MUST match your Tailscale serve URL
BASE_URL=https://ola.your-tailnet.ts.net
# API ENVIRONMENT: production/development
ENVIRONMENT=production
```

> **Important**: The `BASE_URL` must match the URL where your service will be accessible via Tailscale serve.

### 3. Tailscale Configuration

Edit `compose.yml` and replace the Tailscale auth key:

```yaml
environment:
  - TS_AUTHKEY=tskey-auth-YOUR_ACTUAL_AUTH_KEY_HERE
```

Get your Tailscale auth key from [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys).

> **Note**: The compose file now includes a `serve-config.json` configuration that automatically sets up Tailscale to serve your application. Make sure this file is in your project directory.

### 4. Create Required Directories

Create the necessary directories for data storage:

```bash
mkdir -p data subtitles logs ts_state
```

### 5. Deploy with Docker Compose

Start the services:

```bash
docker compose up -d
```

> **Note**: The application will automatically be served through Tailscale based on the `serve-config.json` configuration. After deployment, you'll need to enable HTTPS and generate SSL certificates as described in the Tailscale Serve Configuration section.

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

- `./.env` → `/app/.env` - Environment configuration
- `./data` → `/app/data` - Database files and cache
- `./subtitles` → `/app/subtitles` - Downloaded subtitle files
- `./logs` → `/app/logs` - Application logs
- `./ts_state` → `/var/lib/tailscale` - Tailscale state
- `./serve-config.json` → `/config/serve-config.json` - Tailscale serve configuration

### Database Stats

The service automatically maintains statistics about:

- Cached subtitle files
- Search result cache
- Storage usage

### Cleanup

The service automatically cleans up old files (30+ days) to manage disk space.

## Tailscale Serve Configuration

The service is pre-configured with Tailscale serve through the `serve-config.json` file. This automatically exposes your application on your Tailscale network without requiring manual funnel setup.

### HTTPS Setup (Required)

To use HTTPS with Tailscale serve, you need to enable HTTPS and generate SSL certificates:

1. **Enable HTTPS for your tailnet**: Follow the [Tailscale HTTPS guide](https://tailscale.com/kb/1153/enabling-https) to enable HTTPS in your Tailscale admin console.

2. **Generate SSL certificate**: Connect to the Tailscale container and generate the certificate:

```bash
# Access the Tailscale container
docker exec -it ola_ts sh

# Generate SSL certificate for your domain
tailscale cert ola.your-tailnet.ts.net
```

Replace `your-tailnet` with your actual Tailscale tailnet name.

### Access URLs

Once deployed and HTTPS is configured, your service will be available at:

- Internal Tailscale network: `http://ola:8000`
- Tailscale serve URL: `https://ola.your-tailnet.ts.net`

Make sure your `BASE_URL` in the `.env` file matches the Tailscale serve URL for proper functionality.

### Manual Configuration (Advanced)

If you need to modify the Tailscale serve configuration, edit the `serve-config.json` file before deployment. The default configuration serves the application on port 8000.

## Troubleshooting

### Common Issues

1. **Service not accessible**: Check that `BASE_URL` in `.env` matches your access URL
2. **Tailscale auth issues**: Verify your `TS_AUTHKEY` is valid and not expired
3. **HTTPS not working**: Ensure you've enabled HTTPS in your Tailscale admin console and generated SSL certificates using `tailscale cert`
4. **SSL certificate errors**: Re-run `tailscale cert ola.your-tailnet.ts.net` in the container if certificates are expired or invalid
5. **Permission errors**: Ensure directories have proper write permissions
6. **API key errors**: Verify your OpenSubtitles API key is valid

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
