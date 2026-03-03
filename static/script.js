document.addEventListener("DOMContentLoaded", function(){

    const form = document.getElementById("uploadForm");
    if(form){
        form.addEventListener("submit", function(){
            document.getElementById("processingOverlay").style.display="flex";
        });
    }

    // Counter Animation
    document.querySelectorAll(".counter-card").forEach(card=>{
        let target = +card.dataset.target;
        let count = 0;
        let step = target/40;

        let interval = setInterval(()=>{
            count += step;
            if(count >= target){
                card.firstChild.nodeValue = target;
                clearInterval(interval);
            } else {
                card.firstChild.nodeValue = Math.floor(count);
            }
        },20);
    });

    // Search Filter
    const searchInput = document.getElementById("searchInput");
    if(searchInput){
        searchInput.addEventListener("keyup", function(){
            const value = this.value.toLowerCase();
            document.querySelectorAll("#tableBody tr").forEach(row=>{
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(value) ? "" : "none";
            });
        });
    }

});

async function copyFullTable(){

    const table = document.getElementById("tableArea");

    table.style.maxHeight="none";
    table.style.overflow="visible";

    const scale = window.devicePixelRatio * 3;

    const canvas = await html2canvas(table, {
        scale: scale,
        useCORS: true,
        backgroundColor: "#111"
    });

    const blob = await new Promise(resolve => canvas.toBlob(resolve,'image/png'));

    await navigator.clipboard.write([
        new ClipboardItem({'image/png': blob})
    ]);

    alert("Crystal clear table copied!");

    table.style.maxHeight="500px";
    table.style.overflow="auto";
}
