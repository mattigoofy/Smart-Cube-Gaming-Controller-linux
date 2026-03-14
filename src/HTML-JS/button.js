const button = document.getElementById("button");

button.addEventListener("click", async () => {
    button.disabled = true;
    try {
        await connect();
        button.textContent = "Connected";
    } catch (ex) {
        button.disabled = false;
    }
});