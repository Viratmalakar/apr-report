/* Counter Animation */
document.querySelectorAll('.counter').forEach(counter => {
    const update = () => {
        const target = +counter.getAttribute('data-target');
        const count = +counter.innerText;
        const speed = 50;
        const inc = target / speed;

        if (count < target) {
            counter.innerText = Math.ceil(count + inc);
            setTimeout(update, 20);
        } else {
            counter.innerText = target;
        }
    };
    update();
});

/* Copy Full Table */
async function copyFullTable() {
    const wrapper = document.getElementById("tableWrapper");

    const originalHeight = wrapper.style.maxHeight;
    wrapper.style.maxHeight = "none";
    wrapper.style.overflow = "visible";

    const canvas = await html2canvas(wrapper, {
        scale: 3,
        useCORS: true
    });

    canvas.toBlob(async function(blob) {
        await navigator.clipboard.write([
            new ClipboardItem({ 'image/png': blob })
        ]);
        alert("Full table copied to clipboard!");
    });

    wrapper.style.maxHeight = originalHeight;
    wrapper.style.overflow = "auto";
}
