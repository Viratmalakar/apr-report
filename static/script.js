async function copyFullTable(){

    const table = document.getElementById("tableArea");

    // Expand fully
    table.style.maxHeight = "none";
    table.style.overflow = "visible";

    const canvas = await html2canvas(table, {
        scale: 3,
        useCORS: true,
        backgroundColor: null
    });

    canvas.toBlob(async function(blob){
        await navigator.clipboard.write([
            new ClipboardItem({'image/png': blob})
        ]);
        alert("Full table copied with theme!");
    });

    // Restore
    table.style.maxHeight = "500px";
    table.style.overflow = "auto";
}
