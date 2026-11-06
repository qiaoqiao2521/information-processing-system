# Google radar subscriptions and RSS

## Goal

Complete the supplied 22 Scholar and 18 Google Alerts queries for the information mailbox, without duplicate subscriptions. Add the six supplied Google News RSS feeds to the 436 information site through its existing collection workflow.

## Requirements

- Use the user's existing daily Chrome and selected information mailbox from this conversation.
- Stop Google browser operations immediately if a verification or unusual-traffic page appears; notify the user and preserve the page.
- Keep existing subscriptions. Replace the original narrow Scholar query only after its expanded replacement is saved.
- Reuse native RSS collection, publication and scheduling. Preserve dates and source links. Do not add an Agent, notifications, paid collection, or a new RSS collection timer. Move the existing processing workflow timer to 436 as the user requested.
- Preserve frontend and unrelated runtime settings. Deploy the source additions and verify real ingestion and public readback.
- Latest user correction: article processing must run on 436, not the local desktop. Inspect and reuse server authentication/workflow; do not require local OpenCode login or copy desktop credentials.

## Phases

1. Inventory current reminders and RSS implementation — complete.
2. Add missing Scholar and Google Alerts queries — complete.
3. Integrate and test the six RSS feeds — complete.
4. Deploy to 436, verify ingestion/public output, commit and push — in_progress.
5. Run the processing workflow on 436 using its existing model authentication — complete.

## Next Step

Complete Git delivery and clean the temporary transfer package.
