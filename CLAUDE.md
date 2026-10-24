# dpf-dev

The GUI must be stupid friendly. Someone who knows nothing about DPF should get a working deployment.

- A card shows only what the user has to decide. Settings with working defaults go in the advanced tabs.
- Show a note or hint only when it applies, and errors only when something is actually wrong. Each error gets a fix button.
- Never quietly change a setting outside what the user clicked. Instead show the user an error telling them what's incompatible.
- Don't ask the user for things the tool can generate itself
