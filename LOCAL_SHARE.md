# Local Ollama Sharing

This app now runs against a local Ollama instance instead of OpenAI.

## Required Ollama models

Run these once on your machine:

```powershell
ollama pull mistral:latest
```

## Start the app

In one terminal:

```powershell
cd c:\Users\WKI2KOR\Desktop\Chatbot\Hackaton_Chatbot
.\scripts\start_streamlit_local.ps1
```

Open the app locally, then click `Rebuild document index` once.

To print the local and LAN URLs for coworkers on the same network:

```powershell
cd c:\Users\WKI2KOR\Desktop\Chatbot\Hackaton_Chatbot
.\scripts\show_share_urls.ps1
```

## Share it publicly

In a second terminal:

```powershell
cd c:\Users\WKI2KOR\Desktop\Chatbot\Hackaton_Chatbot
.\scripts\start_cloudflare_tunnel.ps1
```

Cloudflare will print a public `https://...trycloudflare.com` URL. Share that URL while your laptop, Ollama, Streamlit, and the tunnel are all still running.

## Notes

- If the app says Ollama is unavailable, start the Ollama desktop app first.
- If the app says a model is missing, run `ollama pull` for that model and retry.
- Anyone using the public tunnel is hitting your local machine, so performance depends on your laptop and internet connection.
