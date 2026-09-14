(() => {
  const dismiss = (message) => {
    message.classList.add("is-dismissing");
    window.setTimeout(() => message.remove(), 220);
  };

  document.querySelectorAll(".message").forEach((message) => {
    message.querySelector(".message-close")?.addEventListener("click", () => {
      dismiss(message);
    });

    window.setTimeout(() => dismiss(message), 4000);
  });
})();
