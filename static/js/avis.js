// Theme
const html = document.documentElement;
const toggle = document.getElementById("themeToggle");
const themeIcon = document.getElementById("themeIcon");

function setTheme(t) {
    html.setAttribute("data-theme", t);
    localStorage.setItem("theme", t);
    themeIcon.textContent = (t === "light") ? "☀️" : "🌙";
}
setTheme(localStorage.getItem("theme") || "dark");

toggle.addEventListener("click", () => {
    setTheme(html.getAttribute("data-theme") === "dark" ? "light" : "dark");
});

// Toast
const toast = document.getElementById("toast");

function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2200);
}

// Counts
const title = document.getElementById("title");
const message = document.getElementById("message");
const titleCount = document.getElementById("titleCount");
const msgCount = document.getElementById("msgCount");
const titleErr = document.getElementById("titleErr");
const msgErr = document.getElementById("msgErr");
const statusChip = document.getElementById("statusChip");

function updateCounts() {
    titleCount.textContent = `${title.value.length}/60`;
    msgCount.textContent = `${message.value.length}/700`;
}
title.addEventListener("input", updateCounts);
message.addEventListener("input", updateCounts);
updateCounts();

// Rating text + emoji
const ratingText = document.getElementById("ratingText");
const ratingEmoji = document.getElementById("ratingEmoji");
const ratingInputs = [...document.querySelectorAll('input[name="rating"]')];

function ratingUI(val) {
    const map = {
        "1": ["Très mauvais", "😕"],
        "2": ["Moyen", "😐"],
        "3": ["Correct", "🙂"],
        "4": ["Très bien", "😄"],
        "5": ["Excellent", "🤩"],
    };
    if (!val) {
        ratingText.textContent = "Aucune note";
        ratingEmoji.textContent = "🙂";
        return;
    }
    ratingText.textContent = map[val][0];
    ratingEmoji.textContent = map[val][1];
}
ratingInputs.forEach(i => i.addEventListener("change", () => ratingUI(i.value)));
ratingUI(null);

// Draft
const form = document.getElementById("reviewForm");
const draftKey = "review_draft_v1";

function saveDraft() {
    const rating = (document.querySelector('input[name="rating"]:checked') || {}).value || "";
    const data = {
        rating,
        kind: document.getElementById("kind").value,
        email: document.getElementById("email").value,
        title: title.value,
        message: message.value,
        consent: document.getElementById("consent").checked
    };
    localStorage.setItem(draftKey, JSON.stringify(data));
    showToast("Brouillon sauvegardé ✅");
    statusChip.textContent = "Brouillon";
}

function loadDraft() {
    const raw = localStorage.getItem(draftKey);
    if (!raw) return;
    try {
        const d = JSON.parse(raw);
        if (d.rating) document.getElementById("r" + d.rating).checked = true;
        document.getElementById("kind").value = d.kind || "suggestion";
        document.getElementById("email").value = d.email || "";
        title.value = d.title || "";
        message.value = d.message || "";
        document.getElementById("consent").checked = !!d.consent;
        updateCounts();
        ratingUI(d.rating || null);
        statusChip.textContent = "Brouillon";
    } catch {}
}
document.getElementById("saveDraft").addEventListener("click", saveDraft);
loadDraft();

// Validation + submit
form.addEventListener("submit", async(e) => {
    e.preventDefault();
    titleErr.textContent = "";
    msgErr.textContent = "";

    const rating = (document.querySelector('input[name="rating"]:checked') || {}).value || "";
    if (!rating) {
        showToast("Choisis une note ⭐");
        statusChip.textContent = "Erreur";
        return;
    }

    if (title.value.trim().length < 3) {
        titleErr.textContent = "Titre trop court (min 3).";
        statusChip.textContent = "Erreur";
        return;
    }
    if (message.value.trim().length < 10) {
        msgErr.textContent = "Message trop court (min 10).";
        statusChip.textContent = "Erreur";
        return;
    }

    statusChip.textContent = "Envoi…";

    // ⚠️ Ici tu branches ton backend:
    // await fetch("/api/avis", { method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(payload) })

    await new Promise(r => setTimeout(r, 700)); // simulation

    localStorage.removeItem(draftKey);
    form.reset();
    updateCounts();
    ratingUI(null);

    statusChip.textContent = "Envoyé ✅";
    showToast("Merci pour ton avis 🙌");
});

// Blobs animation (mobile-friendly)
const blobs = [
    { el: document.querySelector(".b1"), x: 120, y: 80, vx: 0.55, vy: 0.42, s: 1.00 },
    { el: document.querySelector(".b2"), x: 620, y: 260, vx: -0.38, vy: 0.50, s: 1.12 },
    { el: document.querySelector(".b3"), x: 260, y: 420, vx: 0.44, vy: -0.36, s: 0.92 },
];

let w = innerWidth,
    h = innerHeight;
addEventListener("resize", () => {
    w = innerWidth;
    h = innerHeight;
}, { passive: true });

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const isMobile = matchMedia("(max-width: 768px), (hover: none), (pointer: coarse)").matches;

const targetFPS = isMobile ? 30 : 60;
const frameInterval = 1000 / targetFPS;

let t0 = performance.now();
let lastFrame = t0;
let running = true;

document.addEventListener("visibilitychange", () => { running = !document.hidden; });

function tick(now) {
    requestAnimationFrame(tick);
    if (!running) return;
    if (isMobile && (now - lastFrame) < frameInterval) return;
    lastFrame = now;

    const dt = Math.min(32, now - t0);
    t0 = now;
    const time = now * 0.001;

    for (const b of blobs) {
        if (!b.el) continue;

        if (!isMobile) {
            b.x += b.vx * (dt * 0.12) + Math.sin(time * 0.9 + b.y * 0.002) * 0.25;
            b.y += b.vy * (dt * 0.12) + Math.cos(time * 0.8 + b.x * 0.002) * 0.25;

            const pad = 140;
            if (b.x < -pad || b.x > w + pad) b.vx *= -1;
            if (b.y < -pad || b.y > h + pad) b.vy *= -1;

            const scale = b.s + Math.sin(time * 1.2 + b.x * 0.002) * 0.04 + Math.cos(time * 1.0 + b.y * 0.002) * 0.04;
            const rot = Math.sin(time * 0.7 + b.x * 0.001) * 8;

            b.el.style.transform = `translate3d(${b.x}px, ${b.y}px, 0) scale(${clamp(scale, .82, 1.28)}) rotate(${rot}deg)`;
        } else {
            b.x += b.vx * (dt * 0.075) + Math.sin(time * 0.65 + b.y * 0.0016) * 0.12;
            b.y += b.vy * (dt * 0.075) + Math.cos(time * 0.62 + b.x * 0.0016) * 0.12;

            const pad = 240;
            if (b.x < -pad || b.x > w + pad) b.vx *= -1;
            if (b.y < -pad || b.y > h + pad) b.vy *= -1;

            const scale = b.s + Math.sin(time * 0.85 + b.x * 0.0015) * 0.02 + Math.cos(time * 0.82 + b.y * 0.0015) * 0.02;
            const rot = Math.sin(time * 0.45 + b.x * 0.001) * 3;

            b.el.style.transform = `translate3d(${b.x}px, ${b.y}px, 0) scale(${clamp(scale, .90, 1.18)}) rotate(${rot}deg)`;
        }
    }
}
requestAnimationFrame(tick);


document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('reviewForm');

    // --- 1. FONCTIONS DE DÉTECTION (REGEX & LOGIQUE) ---

    function analyseContenu(texte) {
        texte = texte.toLowerCase().trim();

        // A. LISTE NOIRE (Insultes basiques - à compléter selon tes besoins)
        const badWords = [
            'connard', 'salope', 'pute', 'enculé', 'merde', 'fdp', 'batard',
            'idiot', 'débile', 'conne', 'abruti'
        ];
        // Regex pour trouver les mots entiers (évite les faux positifs comme "concombre")
        const badWordsRegex = new RegExp(`\\b(${badWords.join('|')})\\b`, 'i');

        if (badWordsRegex.test(texte)) {
            return { valid: false, reason: "insult" };
        }

        // B. DÉTECTION DU CHARABIA (GIBBERISH)

        // 1. Répétition excessive de caractères (ex: "trèèèèès", "hhhhhhh")
        // Autorise max 3 lettres identiques à la suite
        if (/(.)\1{3,}/.test(texte)) {
            return { valid: false, reason: "gibberish_repeat" };
        }

        // 2. Mots trop longs sans espace (Keyboard Smash type "azertyuiopqsdfghjklm")
        // En français, les mots > 25 lettres sont rarissimes (sauf anticonstitutionnellement)
        const mots = texte.split(/\s+/);
        const motTropLong = mots.some(mot => mot.length > 25);
        if (motTropLong) {
            return { valid: false, reason: "gibberish_long" };
        }

        // 3. Analyse Consonnes / Voyelles (Le test ultime pour "yjxbdbkekdhdb")
        // Un texte français a environ 45% de voyelles.
        // Si un mot long (>5 lettres) n'a aucune voyelle, c'est suspect.
        // Regex : Mot de 5+ lettres sans a,e,i,o,u,y,é,à,è...
        const sansVoyelle = /\b[bcdfghjklmnpqrstvwxzç]{6,}\b/i;
        if (sansVoyelle.test(texte)) {
            return { valid: false, reason: "gibberish_consonants" };
        }

        // 4. Ratio global (si le message est long)
        // Si le message fait > 20 chars et contient moins de 10% de voyelles -> Rejet
        if (texte.length > 20) {
            const voyellesCount = (texte.match(/[aeiouyéàèùâêîôûëïüÿ]/gi) || []).length;
            const ratio = voyellesCount / texte.length;
            if (ratio < 0.10) {
                return { valid: false, reason: "gibberish_ratio" };
            }
        }

        return { valid: true };
    }

    // --- 2. GESTION DU FORMULAIRE ---

    form.addEventListener('submit', async(e) => {
        e.preventDefault();

        const title = document.getElementById('title').value;
        const message = document.getElementById('message').value;

        // Concaténer Titre + Message pour l'analyse
        const fullText = `${title} ${message}`;

        // Analyse du texte
        const analyse = analyseContenu(fullText);

        if (!analyse.valid) {
            let userMessage = "";

            switch (analyse.reason) {
                case "insult":
                    userMessage = "Oups ! Merci de rester courtois. Les insultes ne sont pas tolérées.";
                    break;
                case "gibberish_repeat":
                    userMessage = "Ton message contient trop de caractères répétés. Essaie d'être plus clair.";
                    break;
                case "gibberish_long":
                case "gibberish_consonants":
                case "gibberish_ratio":
                    userMessage = "Ton message semble incompréhensible. Merci d'écrire des phrases claires.";
                    break;
            }

            // Afficher le Modal d'erreur
            showGlassModal(userMessage, false); // false = erreur (rouge/jaune)
            return; // On arrête l'envoi
        }

        // Si tout est bon, on envoie au serveur Django
        const formData = new FormData(form);

        try {
            // Remplace par ton URL Django réelle
            const response = await fetch('/api/avis/', {
                method: 'POST',
                body: formData,
                headers: {
                    // Si tu utilises le CSRF Django standard dans les cookies
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            const result = await response.json();

            if (result.success) {
                showGlassModal("Merci ! Ton avis a bien été envoyé. 🚀", true);
                form.reset();
            } else {
                showGlassModal("Erreur serveur : " + result.error);
            }

        } catch (error) {
            showGlassModal("Impossible de contacter le serveur.");
        }
    });

    // Helper pour récupérer le cookie CSRF Django
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});