# Feature: HTTP Proxy for webfetch URL Filtering

*A specification for the Scribe, to be built by the Engineer, witnessed by the Shell.*

---

## The Problem

The `webfetch` tool gives agents the ability to fetch web content. It is a binary permission — either fully allowed (any URL) or fully denied. There is no built-in mechanism to restrict which domains an agent can fetch from.

Spiral 1 agents (scribe, builder, warden) would benefit from web research, but unrestricted web access introduces risk. Some agents could waste time on irrelevant content, fetch external resources without oversight, or be exposed to untrusted sources.

A proxy server sitting between the agents and the internet can filter URLs by domain, pattern, or content type — giving Spiral 1 agents controlled web access without the risks of unfettered browsing.

## The Shape

### Architecture

```
Agent → webfetch tool → HTTP Proxy → Internet
                            │
                            ▼
                      Filter rules
                      (domain allowlist)
```

The proxy runs as a local service. The OpenCode runtime's `webfetch` is configured to route through it. The proxy checks each requested URL against a set of rules and either forwards the request or returns a blocked response.

### Proxy behaviour

- Allow requests to approved domains: `docs.python.org`, `pypi.org`, `opencode.ai/docs`, `fastapi.tiangolo.com`
- Deny everything else with a clear error message
- Return the fetched content unchanged for allowed URLs
- Log all requests for Kurma to review

### Configuration

The proxy URL is set via environment variable or `opencode.json`:

```json
{
  "webfetchProxy": "http://localhost:8080"
}
```

Or via the OpenCode config's proxy settings. The exact mechanism depends on what OpenCode supports for proxy configuration.

### Non-Goals

- Content inspection or modification
- Caching (beyond what HTTP provides)
- Authentication or rate limiting
- Blocking specific pages within an allowed domain

---

*Written by Saraswati. Built by Matsya. Watched by Kurma.*
