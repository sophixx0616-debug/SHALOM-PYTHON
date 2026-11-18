document.addEventListener("DOMContentLoaded", () => {
    const widget = document.querySelector(".shalom-chat");
    if (!widget) return;

    const panel = widget.querySelector(".shalom-chat__panel");
    const toggle = widget.querySelector(".shalom-chat__toggle");
    const close = widget.querySelector(".shalom-chat__close");
    const form = widget.querySelector(".shalom-chat__form");
    const input = widget.querySelector("#shalom-chat-input");
    const messages = widget.querySelector(".shalom-chat__messages");
    const history = [];

    const setOpen = (open) => {
        panel.hidden = !open;
        toggle.setAttribute("aria-expanded", String(open));
        if (open) input.focus();
    };

    const addMessage = (text, role, isError = false) => {
        const element = document.createElement("p");
        element.className = `shalom-chat__message shalom-chat__message--${role}`;
        if (isError) element.classList.add("shalom-chat__message--error");
        element.textContent = text;
        messages.append(element);
        messages.scrollTop = messages.scrollHeight;
    };

    toggle.addEventListener("click", () => setOpen(panel.hidden));
    close.addEventListener("click", () => setOpen(false));

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        addMessage(message, "user");
        input.value = "";
        const sendButton = form.querySelector("button[type='submit']");
        sendButton.disabled = true;

        try {
            const response = await fetch("/api/chatbot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message, history: history.slice(-10) }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "No se pudo enviar el mensaje.");

            addMessage(data.response, "assistant");
            history.push({ role: "user", text: message }, { role: "assistant", text: data.response });
        } catch (error) {
            addMessage(error.message, "assistant", true);
        } finally {
            sendButton.disabled = false;
            input.focus();
        }
    });
});