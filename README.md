# inventree-user-activity

InvenTree plugin that generates a comprehensive activity report for a
specific user: stock movements, build/purchase/sales/return orders created
or assigned, parts created, and attachments/note images uploaded.

## What it adds

- A panel titled **"Activity Report"** on each user's detail page
  (`/core/user/<id>/`), showing a count summary per activity category.
- A **"Download full PDF report"** link in that panel, backed by a plugin
  URL endpoint (`/plugin/useractivityreport/report/<user_id>/pdf/`) that
  renders a PDF via WeasyPrint (the same PDF engine InvenTree's core report
  system uses).

## Access control

- Staff and superusers can view the panel/PDF for any user.
- A non-staff user can only view their own activity report.

## Why this isn't a "Report Template"

InvenTree's built-in report system (`ReportTemplate` / `ReportMixin`) only
supports a fixed, core-defined list of models that implement
`InvenTreeReportMixin` (StockItem, Build, PurchaseOrder, SalesOrder,
Part, etc.). `django.contrib.auth.models.User` is not one of them, and a
plugin cannot add a new base class to an already-migrated core model. So
this plugin renders its own HTML template and calls WeasyPrint directly,
instead of going through `ReportTemplate`.

## Installation

1. Ensure plugin support is enabled on your InvenTree instance (Settings >
   Plugins > "Enable URL integration" / plugin support, per InvenTree's
   docs), and that `ENABLE_PLUGINS_URL` is enabled so custom plugin URLs
   are registered.
2. Install this package into the same Python environment as your InvenTree
   server:

   ```bash
   pip install -e /path/to/inventree-user-activity-plugin
   ```

   or add a line to your InvenTree `plugins.txt` and run `invoke plugins`:

   ```
   inventree-user-activity
   ```

3. Restart the InvenTree server and background worker.
4. In the admin UI, go to Settings > Plugins and activate
   "User Activity Report".
5. Visit any user's detail page to see the "Activity Report" panel.

## Development

```bash
pip install -e .
```

Then point your dev InvenTree instance's plugin config at this package (see
step 2 above). Edit `inventree_user_activity/activity.py` to change which
records are aggregated, `templates/inventree_user_activity/report.html` to
change the PDF layout, and `static/activity_panel.js` to change the panel UI.
