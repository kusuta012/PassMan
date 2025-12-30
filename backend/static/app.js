let clearTimer = null;

function copyPassword(password) {
    navigator.clipboard.writeText(password)
        .then(() => {
            const status = document.getElementById("copy-status");
            status.textContent = "Password copied! Clipboard clears in 15 seconds.";

            if (clearTimer) {
                clearTimeout(clearTimer);
            }
            
            clearTimer = setTimeout(() => {
                navigator.clipboard.writeText("");
                status.textContent = "cliboard Cleared.";
            },15000);
        })
        .catch(() => {
            alert("CLipbaord access denied.")
        }
    )
}

function generate() {
    const form = new FormData();
    form.append("length", document.getElementById("len").value);
    form.append("upper", document.getElementById("upper").value);
    form.append("lower", document.getElementById("lower").value);
    form.append("digits", document.getElementById("digits").value);
    form.append("symbols", document.getElementById("symbols").value);

    const params = new URLSearchParams({
        length: document.getElementById("len").value,
        upper: document.getElementById("upper").checked,
        lower: document.getElementById("lower").checked,
        digits: document.getElementById("digits").checked,
        symbols: document.getElementById("symbols").checked,
    });

        fetch("/generate?" + params.toString())
        .then(res => res.json())
        .then(data => {
            document.getElementById("result").value = data.password;
            document.getElementById("gen-status").textContent = "Generated!";
        
        });

}

function copyGenerated() {
    const pwd = document.getElementById("result").value;
    if (!pwd) return;
    copyPassword(pwd); 
}

function useGenerated() {
    const pwd = document.getElementById("result").value;
    if (!pwd) return;
    sessionStorage.setItem("generatedPassword", pwd)
    window.location.href = "/add";
}

function refreshTotp(entryId) {
    fetch(`/totp-code/${entryId}`)
        .then(res => res.json())
        .then(data => {
            if (data.code) {
                document.getElementById(`totp-${entryId}`).textContent = ` ${data.code}`;
            }
        });
}

setInterval(() => {
    document.querySelectorAll("[id^='totp-']").forEach(el => {
        const entryId = el.id.replace("totp-", "");
        refreshTotp(entryId);
    });
}, 30000);

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[id^='totp-']").forEach(el => {
        const entryId = el.id.replace("totp-", "");
        refreshTotp(entryId);
    });
});

let inactivityTimer = null;
const INACTIVITY_LIMIT = 5*60*1000;

function resetInactivityTimer() {
    if (inactivityTimer) clearTimeout(inactivityTimer);

    inactivityTimer = setTimeout(() => {
        window.location.href = "/lock";
    }, INACTIVITY_LIMIT);
}

["mousemove", "keydown", "click", "scroll"].forEach(event => {
    document.addEventListener(event, resetInactivityTimer);
});

document.addEventListener("DOMContentLoaded", resetInactivityTimer);


function filterEntries() {
    const q = document.getElementById("search").value.toLowerCase();

    document.querySelectorAll(".entry").forEach(el => {
        const text = 
            el.dataset.site +
            el.dataset.user +
            el.dataset.tags;

        el.style.display = text.includes(q) ? "" : "none";
    });

    document.querySelectorAll(".note").forEach(el => {
        const text =
            el.dataset.title +
            el.dataset.tags;

        el.style.display = text.includes(q) ? "" : "none";
    });
}