window.onload = function(){
    document.querySelectorAll('.counter').forEach(counter=>{
        let target = +counter.getAttribute('data-target');
        let count = 0;
        let step = target/50;

        let interval = setInterval(()=>{
            count += step;
            if(count >= target){
                counter.innerText = target;
                clearInterval(interval);
            } else {
                counter.innerText = Math.floor(count);
            }
        },20);
    });
};

async function copyFullTable(){
    const wrapper = document.querySelector(".table-container");

    wrapper.style.maxHeight="none";
    wrapper.style.overflow="visible";

    const shadow = document.createElement("div");
    shadow.style.position="fixed";
    shadow.style.top="0";
    shadow.style.left="0";
    shadow.style.width="100%";
    shadow.style.height="100%";
    shadow.style.background="rgba(0,0,0,0.7)";
    shadow.style.zIndex="9999";
    document.body.appendChild(shadow);

    const canvas = await html2canvas(wrapper,{scale:3});

    canvas.toBlob(async function(blob){
        await navigator.clipboard.write([
            new ClipboardItem({'image/png':blob})
        ]);
        alert("Full Table Copied (Ultra HD)");
    });

    document.body.removeChild(shadow);
    wrapper.style.maxHeight="500px";
    wrapper.style.overflow="auto";
}
