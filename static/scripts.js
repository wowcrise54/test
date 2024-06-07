document.addEventListener("DOMContentLoaded", function() {
    const buttons = document.querySelectorAll(".btn");

    buttons.forEach(button => {
        button.addEventListener("mouseover", () => {
            button.classList.add("hover");
        });

        button.addEventListener("mouseout", () => {
            button.classList.remove("hover");
        });
    });

    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = "0";
            setTimeout(() => {
                alert.remove();
            }, 600);
        }, 3000);
    });
});
