async function copyTableToClipboard() {

    const tableContainer = document.getElementById("tableSection");

    // Save original styles
    const originalHeight = tableContainer.style.maxHeight;
    const originalOverflow = tableContainer.style.overflow;

    // Remove scroll to expand full table
    tableContainer.style.maxHeight = "none";
    tableContainer.style.overflow = "visible";

    await new Promise(resolve => setTimeout(resolve, 300));

    html2canvas(tableContainer, {
        scale: 4,            // Crystal Clear
        useCORS: true,
        scrollX: 0,
        scrollY: 0,
        windowWidth: tableContainer.scrollWidth,
        windowHeight: tableContainer.scrollHeight
    }).then(canvas => {

        canvas.toBlob(blob => {
            navigator.clipboard.write([
                new ClipboardItem({ "image/png": blob })
            ]);
            alert("Full Table Copied Successfully!");
        });

        // Restore original styles
        tableContainer.style.maxHeight = originalHeight;
        tableContainer.style.overflow = originalOverflow;
    });
}



async function copyPageToClipboard() {

    const body = document.body;

    html2canvas(body, {
        scale: 3,
        useCORS: true
    }).then(canvas => {

        canvas.toBlob(blob => {
            navigator.clipboard.write([
                new ClipboardItem({ "image/png": blob })
            ]);
            alert("Full Page Copied Successfully!");
        });

    });
}



function resetPage() {
    window.location.href = "/";
}



function searchTable() {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let rows = document.querySelectorAll("#dataTable tbody tr");

    rows.forEach(row => {
        let text = row.innerText.toLowerCase();
        row.style.display = text.includes(input) ? "" : "none";
    });
}
