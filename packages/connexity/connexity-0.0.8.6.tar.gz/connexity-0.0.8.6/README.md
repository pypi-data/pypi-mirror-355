# CHANGELOG

v0.0.8.6 — 2025-06-13


## New Features
### VAD compensation

Configurable via VADParams
Pass vad_params into initialize(...)
Environment & analyzer tags
Added env and vad_analyzer metadata fields to register_call

### Usage 


```python
from pipecat.audio.vad.vad_analyzer import VADParams
from connexity.metrics.pipecat import ConnexityTwilioObserver

vad_params = VADParams(
    confidence=0.5,
    min_volume=0.6,
    start_secs=0.2,
    stop_secs=0.8,
)

observer = ConnexityTwilioObserver()
await observer.initialize(
    agent_id="YOUR_AGENT_ID",
    api_key="YOUR_CONNEXITY_API_KEY",
    sid=call_sid,
    phone_call_provider="twilio",
    user_phone_number=from_number,
    agent_phone_number=to_number,
    twilio_account_sid="TWILIO_SID",
    twilio_auth_token="TWILIO_TOKEN",
    voice_provider="11labs",
    llm_provider="openai",
    llm_model="gpt-4o",
    call_type="inbound",
    transcriber="deepgram",
    vad_params=vad_params,
    env="development",          # or "production"
    vad_analyzer="silero",      # your chosen VAD engine name
)

pipeline.register_observer(observer)
```
