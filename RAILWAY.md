# Railway deployment

මෙය **safe mode** deployment එකකි. `MCP_UNSAFE_LOCAL=1` Railway එකේ set කරන්න එපා.

Required variables:

```text
MCP_AUTH_TOKEN=<long-random-secret>
MCP_WORKSPACE=/data/workspace
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_UNSAFE_LOCAL=0
```

Railway public URL එක `/mcp` path එකෙන් භාවිතා වේ. Bearer header එකක් අවශ්‍යයි:

```text
Authorization: Bearer <MCP_AUTH_TOKEN>
```

Gemini Custom Apps OAuth credentials ඉල්ලන්නේ නම්, මෙය static bearer token එකක් නිසා Gemini OAuth flow එකට වෙනම OAuth provider/proxy එකක් අවශ්‍ය විය හැක. `MCP_AUTH_TOKEN` GitHub එකට commit නොකරන්න; Railway Variables තුළ පමණක් තබන්න.
