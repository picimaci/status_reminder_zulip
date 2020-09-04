# Status reminder in Zulip

Python script to:
 * check today's messages in Zulip Stream Topic
 * notify users who haven't sent a message today to Zulip Stream Topic

```
docker run \
  -e ZULIP_SITE=https://zulip.example.com \
  -e ZULIP_EMAIL=picimaci-proba-bot@zulip.example.com \
  -e ZULIP_API_KEY=secret \
  -e ZULIP_STREAM=Status \
  -e ZULIP_TOPIC=(no topic) \
  -e NO_STATUS_NEEDED=[] \
  -e ALTERNATIVE_NAMES={} \
  feardapanda/status-reminder-zulip
```
