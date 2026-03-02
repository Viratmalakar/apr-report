function copyTablePNG() {
    const table = document.getElementById("tableSection");

    html2canvas(table, {
        scale: 3,
        scrollY: -window.scrollY,
        useCORS: true
    }).then(canvas => {
        const link = document.createElement("a");
        link.download = "Full_Table.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    });
}

function copyPagePNG() {
    html2canvas(document.body, {
        scale: 3,
        scrollY: -window.scrollY,
        useCORS: true
    }).then(canvas => {
        const link = document.createElement("a");
        link.download = "Full_Page.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    });
}

function resetPage() {
    window.location.href = "/";
}
