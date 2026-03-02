function copyTablePNG() {
    html2canvas(document.getElementById("tableSection")).then(canvas => {
        const link = document.createElement("a");
        link.download = "table.png";
        link.href = canvas.toDataURL();
        link.click();
    });
}

function copyPagePNG() {
    html2canvas(document.body).then(canvas => {
        const link = document.createElement("a");
        link.download = "full_page.png";
        link.href = canvas.toDataURL();
        link.click();
    });
}

function resetPage() {
    window.location.href = "/";
}
