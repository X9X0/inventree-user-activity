const CATEGORY_LABELS = {
    stock_tracking: "Stock movements",
    builds_issued: "Build orders issued",
    builds_responsible: "Build orders responsible for",
    purchase_orders_created: "Purchase orders created",
    purchase_orders_responsible: "Purchase orders responsible for",
    sales_orders_created: "Sales orders created",
    sales_orders_responsible: "Sales orders responsible for",
    return_orders_created: "Return orders created",
    parts_created: "Parts created",
    attachments: "Attachments uploaded",
    notes_images: "Note images added",
};

export function renderActivityPanel(target, data) {
    if (!target) {
        console.error("No target provided to renderActivityPanel");
        return;
    }

    const context = data.context || {};
    const summary = context.summary || {};
    const pdfUrl = context.pdf_url;

    const rows = Object.keys(CATEGORY_LABELS)
        .map((key) => {
            const label = CATEGORY_LABELS[key];
            const count = summary[key] ?? 0;
            return `<tr><td>${label}</td><td style="text-align:right">${count}</td></tr>`;
        })
        .join("");

    target.innerHTML = `
        <div>
            <h4>User Activity Summary</h4>
            <table style="width:100%; border-collapse: collapse;">
                ${rows}
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
}
