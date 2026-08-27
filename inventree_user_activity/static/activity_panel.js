const CATEGORIES = [
    { key: "stock_tracking", label: "Stock movements", columns: [
        ["date", "Date"], ["item", "Item"], ["type", "Type"], ["notes", "Notes"],
    ] },
    { key: "builds_issued", label: "Build orders issued", columns: [
        ["reference", "Reference"], ["part", "Part"], ["status", "Status"], ["creation_date", "Created"],
    ] },
    { key: "builds_responsible", label: "Build orders responsible for", columns: [
        ["reference", "Reference"], ["part", "Part"], ["status", "Status"], ["creation_date", "Created"],
    ] },
    { key: "purchase_orders_created", label: "Purchase orders created", columns: [
        ["reference", "Reference"], ["supplier", "Supplier"], ["status", "Status"], ["creation_date", "Created"],
    ] },
    { key: "purchase_orders_responsible", label: "Purchase orders responsible for", columns: [
        ["reference", "Reference"], ["supplier", "Supplier"], ["status", "Status"], ["creation_date", "Created"],
    ] },
    { key: "sales_orders_created", label: "Sales orders created", columns: [
        ["reference", "Reference"], ["customer", "Customer"], ["status", "Status"], ["creation_date", "Created"],
    ] },
    { key: "sales_orders_responsible", label: "Sales orders responsible for", columns: [
        ["reference", "Reference"], ["customer", "Customer"], ["status", "Status"], ["creation_date", "Created"],
    ] },
    { key: "return_orders_created", label: "Return orders created", columns: [
        ["reference", "Reference"], ["customer", "Customer"], ["status", "Status"], ["creation_date", "Created"],
    ] },
    { key: "parts_created", label: "Parts created", columns: [
        ["IPN", "IPN"], ["name", "Name"], ["creation_date", "Created"],
    ] },
    { key: "attachments", label: "Attachments uploaded", columns: [
        ["file", "File"], ["comment", "Comment"], ["upload_date", "Uploaded"],
    ] },
    { key: "notes_images", label: "Note images added", columns: [
        ["image", "Image"], ["date", "Date"],
    ] },
];

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function renderDetailTable(columns, records) {
    if (!records || records.length === 0) {
        return `<p style="color: var(--mantine-color-dimmed, #888); font-style: italic; margin: 0.5em 0;">No records found.</p>`;
    }

    const head = columns.map(([, label]) => `<th style="text-align:left; padding: 0.3em 0.6em; border-bottom: 1px solid rgba(128,128,128,0.3);">${escapeHtml(label)}</th>`).join("");
    const rows = records
        .map((record) => {
            const cells = columns
                .map(([field]) => `<td style="padding: 0.3em 0.6em; border-bottom: 1px solid rgba(128,128,128,0.15);">${escapeHtml(record[field])}</td>`)
                .join("");
            return `<tr>${cells}</tr>`;
        })
        .join("");

    return `
        <table style="width:100%; border-collapse: collapse; font-size: 0.9em; margin: 0.5em 0 1em;">
            <thead><tr>${head}</tr></thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

export function renderActivityPanel(target, data) {
    if (!target) {
        console.error("No target provided to renderActivityPanel");
        return;
    }

    const context = data.context || {};
    const summary = context.summary || {};
    const pdfUrl = context.pdf_url;
    const dataUrl = context.data_url;

    let detailCache = null;
    let expandedKey = null;

    const rowsHtml = CATEGORIES.map(
        (cat) => `
            <tr class="activity-row" data-key="${cat.key}" style="cursor:pointer;">
                <td style="padding: 0.4em 0.6em;">${escapeHtml(cat.label)}</td>
                <td style="padding: 0.4em 0.6em; text-align:right;">${summary[cat.key] ?? 0}</td>
            </tr>
            <tr class="activity-detail-row" data-key-detail="${cat.key}" style="display:none;">
                <td colspan="2" style="padding: 0 0.6em 0.6em;"></td>
            </tr>
        `
    ).join("");

    target.innerHTML = `
        <div>
            <h4>User Activity Summary</h4>
            <p style="color: var(--mantine-color-dimmed, #888); font-size: 0.85em; margin-top: -0.5em;">
                Click a row to view detailed records.
            </p>
            <table style="width:100%; border-collapse: collapse;">
                <tbody id="activity-summary-body">${rowsHtml}</tbody>
            </table>
            ${
                pdfUrl
                    ? `<p style="margin-top: 1em;">
                        <a href="${pdfUrl}" target="_blank" rel="noopener noreferrer">
                            Download full PDF report
                        </a>
                       </p>`
                    : ""
            }
        </div>
    `;

    if (!dataUrl) {
        return;
    }

    async function loadDetail() {
        if (detailCache) {
            return detailCache;
        }
        const response = await fetch(dataUrl, { credentials: "same-origin" });
        if (!response.ok) {
            throw new Error(`Failed to load activity detail (${response.status})`);
        }
        detailCache = await response.json();
        return detailCache;
    }

    target.querySelectorAll("tr.activity-row").forEach((row) => {
        row.addEventListener("click", async () => {
            const key = row.getAttribute("data-key");
            const detailRow = target.querySelector(`tr[data-key-detail="${key}"]`);
            const cell = detailRow.querySelector("td");

            if (expandedKey === key) {
                detailRow.style.display = "none";
                expandedKey = null;
                return;
            }

            if (expandedKey) {
                const prevRow = target.querySelector(`tr[data-key-detail="${expandedKey}"]`);
                if (prevRow) {
                    prevRow.style.display = "none";
                }
            }

            cell.innerHTML = `<p style="font-style: italic;">Loading&hellip;</p>`;
            detailRow.style.display = "";
            expandedKey = key;

            try {
                const detail = await loadDetail();
                const category = CATEGORIES.find((c) => c.key === key);
                cell.innerHTML = renderDetailTable(category.columns, detail[key]);
            } catch (err) {
                cell.innerHTML = `<p style="color: var(--mantine-color-red-text, #e03131);">${escapeHtml(err.message)}</p>`;
            }
        });
    });
}
