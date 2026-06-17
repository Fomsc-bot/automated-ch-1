# Automated AI Life Hacks YouTube Channel Pipeline 🤖🎥

[![Test Rendering Pipeline](https://github.com/your-username/ai-lifehacks-channel/actions/workflows/test_pipeline.yml/badge.svg)](https://github.com/your-username/ai-lifehacks-channel/actions/workflows/test_pipeline.yml)
[![Daily Upload Status](https://github.com/your-username/ai-lifehacks-channel/actions/workflows/daily_short.yml/badge.svg)](https://github.com/your-username/ai-lifehacks-channel/actions/workflows/daily_short.yml)

A fully automated, zero-human-intervention content creation engine that generates, renders, and publishes daily YouTube Shorts focused on "AI and Productivity Life Hacks". Built with Python, MoviePy, Pillow, OpenAI GPT-4o, and Google Cloud TTS, orchestrated via GitHub Actions.

---

## 🌟 Key Features

- **Automated Topic Rotation**: Selects and rotates topics from a curated pool of 75+ productivity scenarios. Falls back to GPT-4o to generate fresh concepts.
- **AI-Powered Copywriting**: Crafts high-retention, punchy narration scripts (≤145 words) in three distinct hook variants (Story, List-style, Authoritative) alongside SEO-optimized titles, descriptions, and tags.
- **No-Dependency Subtitling**: Renders customizable subtitles word-by-word synced to the voiceover, bypassing any need for complex local ImageMagick installations.
- **High-CTR Thumbnails**: pillow programmatically builds clean 1280x720 JPEG templates complete with high-contrast text outlines, custom gradients, and brand markers.
- **Headless YouTube Integration**: Secure OAuth2 refresh token pipeline uploads the video, updates metadata, binds captions, and sets the thumbnail automatically.
- **Zero Running Costs**: Leveraging GitHub Actions' free tiers and Google Cloud TTS's 1M characters/month free allowance allows the entire system to run for ~$2–5/month (mostly API costs for GPT-4o).

---

## 🛠 Repository Architecture

```
├── .github/workflows/
│   ├── daily_short.yml          # Runs on daily cron trigger (picks topic -> uploads)
│   └── test_pipeline.yml        # Runs manual test rendering (generates video artifact)
├── pipeline/
│   ├── config.py                # Tuning parameters (visuals, colors, TTS, BGM volume)
│   ├── topic_generator.py       # Tracks used topics & manages pool
│   ├── script_writer.py         # Interfaces with OpenAI ChatCompletions (GPT-4o-mini)
│   ├── tts_engine.py            # Converts scripts to audio (WaveNet / ElevenLabs)
│   ├── subtitle_writer.py       # Parses narration to SRT with proportional timing
│   ├── video_builder.py         # Assembles background, audio, BGM, and Pillow captions
│   ├── thumbnail_maker.py       # Outputs bold branding images
│   └── youtube_uploader.py      # Authenticates and pushes to YouTube API
├── scripts/
│   └── auth_youtube.py          # One-time local credentials helper
├── topics/
│   ├── topic_pool.json          # 75+ pre-seeded AI hack templates
│   └── used_topics.json         # State preservation (updated dynamically by bot)
├── requirements.txt
├── SETUP.md                     # Step-by-step API integration guide
└── run_pipeline.py              # Orchestration entry point
```

---

## 🚀 Getting Started

To get this pipeline up and running for your channel, please read our step-by-step credential guide:

👉 **[SETUP.md](file:///SETUP.md)**

### Local Quickstart

If you want to test the video rendering engine on your local machine:

1. Clone this repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your OpenAI key:
   ```bash
   export OPENAI_API_KEY="your-key"
   ```
4. Perform a dry run test (this will render the video to `/output` but skip uploading):
   ```bash
   python run_pipeline.py --dry-run true --upload false
   ```

---

## 📜 Legal & Compliance

- **Original Assets**: Audio, visual templates, and text overlays are uniquely compiled on-the-fly, ensuring compliance with YouTube's policies regarding reused/unoriginal content.
- **COPPA & Ads Friendly**: Content remains neutral, informative, and designated as "Not Made for Kids" to allow full AdSense CPM categorization.
- **API Guidelines**: Upload quotas and OAuth consent levels are strictly managed within Google Cloud limits.
