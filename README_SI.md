# Gemini Safe MCP Server

මෙය Gemini Custom App එකකට සම්බන්ධ කළ හැකි Streamable HTTP MCP server scaffold එකකි. මෙය සම්පූර්ණ server-control shell එකක් නොවේ: files `MCP_WORKSPACE` ඇතුළත පමණක් වන අතර command allowlist එකක් පමණක් ක්‍රියා කරයි.

## Local run

```bash
cd /home/ubuntu/gemini-safe-mcp
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
mkdir -p /home/ubuntu/gemini-workspace
MCP_WORKSPACE=/home/ubuntu/gemini-workspace python server.py
```

Default MCP URL:

```text
http://127.0.0.1:8000/mcp
```

Gemini වෙත සම්බන්ධ කිරීමට public HTTPS URL එකක් අවශ්‍ය වේ. `localhost` හෝ මෙහි sandbox URL එක production ලෙස භාවිතා නොකරන්න. VPS එකක්, Cloud Run එකක්, හෝ ඔබේම HTTPS reverse proxy එකක් යටතේ deploy කරන්න.

## Exposed tools

- `list_files(path)`
- `read_file(path)`
- `write_file(path, content)`
- `run_command(command, timeout_seconds)` — `pwd`, `ls`, `find`, `git`, `python3`, `node`, `npm`, `pnpm` පමණයි; shell operators disabled.

## Unsafe local-only mode

ඔබ explicitly තෝරාගත් local-only mode එකේදී ඕනෑම shell command එකක් run කළ හැකි tool එකක් enable කළ හැක:

```bash
MCP_UNSAFE_LOCAL=1 MCP_HOST=127.0.0.1 MCP_WORKSPACE=/home/ubuntu/gemini-workspace python server.py
```

මෙම mode එකේ server එක code මඟින් `127.0.0.1` වෙත force කරයි. `MCP_HOST=0.0.0.0` දුන්නත් public bind නොවේ. මෙම mode එකේදී temporary forwarding URL, public VPS, හෝ Gemini Custom App එකට connect නොකරන්න. `run_any_shell_command` tool එක සම්පූර්ණ shell access ලබා දෙන නිසා credentials, SSH keys සහ personal files අවදානමට ලක්විය හැක.

## ආරක්ෂාව

1. TLS/HTTPS අනිවාර්ය කරන්න.
2. Authentication එකක් නැතිව public internet එකට expose නොකරන්න.
3. `MCP_WORKSPACE` තුළ secrets, SSH keys, `.env` files තබන්න එපා.
4. Gemini write actions manual confirmation ඉල්ලුවත්, tool permissions සහ logs පරීක්ෂා කරන්න.
5. අවශ්‍ය නැති විට app එක disconnect/revoke කරන්න.
