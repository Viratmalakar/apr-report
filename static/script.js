document.addEventListener("DOMContentLoaded", function(){

    const form = document.getElementById("uploadForm");

    if(form){
        form.addEventListener("submit", function(){
            const loader = document.getElementById("loader");
            if(loader){
                loader.style.display="flex";
            }
        });
    }

});

async function copyFullTable(){

    const table = document.getElementById("tableArea");

    table.style.maxHeight="none";
    table.style.overflow="visible";

    const canvas = await html2canvas(table, {
        scale: 5,
        useCORS: true,
        backgroundColor: "#111"
    });

    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));

    await navigator.clipboard.write([
        new ClipboardItem({'image/png': blob})
    ]);

    alert("Crystal clear table copied!");

    table.style.maxHeight="500px";
    table.style.overflow="auto";
}
