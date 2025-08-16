## Guide: Setting Up Quantumult X with MITM Certificate and OpenSubtitles rewrite

Follow these steps to configure Quantumult X with your rewrite rule for use with the OpenSubtitles API.

***

### 1. Install Quantumult X on iOS

- Download **Quantumult X** from the App Store.

***

### 2. Set Up the MITM Certificate

1. **Open Quantumult X**.
2. Go to **Settings** > **HTTPS Decryption**.
3. Tap **Install Certificate**:
    - A pop-up will prompt to install a profile.
    - Allow it, then open iOS **Settings** > **General** > **VPN & Device Management**.
    - **Install** the “Quantumult X CA” profile.
4. After installation, **trust** the Quantumult X certificate:
    - Go to **Settings** > **General** > **About** > **Certificate Trust Settings**.
    - Enable trust for “Quantumult X CA”.

***

### 3. Obtain Your OpenSubtitles API Key

- Go to: [https://www.opensubtitles.com/en/consumers](https://www.opensubtitles.com/en/consumers)
- Create an account or log in.
- Follow the instructions to obtain your **API Key**.

***

### 4. Edit Quantumult X Configuration

#### In Quantumult X:

1. Go to **Settings** > **Configuration File** > **Edit**.
2. Find (or add) the sections:

   ```
   [rewrite_local]
   ```

   and

   ```
   [mitm]
   ```

3. **Add/Modify as follows** _(replace `YOUR_API_KEY` with your actual key)_:

   ```
   [rewrite_local]
   ^(https?:\/\/rest\.opensubtitles\.org)(\/.*)$ url 302 https://ola.your-tailnet.ts.net$2?apiKey=YOUR_API_KEY

   [mitm]
   hostname=rest.opensubtitles.org
   ```

***

### 5. Save and Enable Your Configuration

1. After editing, tap **Save**.
2. Go back and ensure **HTTPS Decryption** is enabled.
3. Restart Quantumult X, if needed.

***

### 6. Test the Setup

- Access HDO app to see if subtitles is correctly loaded.

***

### Notes

- You must use **your own API key** from OpenSubtitles.
- MITM decryption is necessary for rewrite rules on HTTPS endpoints.
- Some apps or systems may require a device restart for CA changes to take effect.

***
