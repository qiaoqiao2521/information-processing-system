// Called by the existing 30-minute reader timer; no models or notifications.
import { reconcileReviews } from '@aihot/backend/admin/upstream-reviews';
import { closeDb } from '@aihot/backend/db';
import { stopBoss } from '@aihot/backend/jobs/queue';
try {console.log(JSON.stringify(await reconcileReviews()));}
finally {await stopBoss();await closeDb();}
