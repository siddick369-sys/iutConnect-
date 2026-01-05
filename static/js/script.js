// ===== SPINNER =====
window.addEventListener('load', () => {
    setTimeout(() => {
        document.getElementById('spinner').style.display = 'none';
    }, 1000);
});

// ===== NAVBAR =====
const burger = document.getElementById('hamburger');
const navbar = document.querySelector('.navbar');
burger.addEventListener('click', () => {
    burger.classList.toggle('active');
    navbar.classList.toggle('show');
});
// ===== SMOOTH SCROLL (uniquement ancres internes) =====
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', (e) => {
        const href = link.getAttribute('href') || '';

        // ✅ Si c'est un lien normal (avis.html, http..., etc.), on laisse naviguer
        if (!href.startsWith('#')) return;

        e.preventDefault();
        const target = document.querySelector(href);
        if (!target) return;

        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
});

// ===== TYPEWRITER ROTATOR =====
const rotatingText = document.getElementById("rotatingText");
const phrases = [
    "IUT Connect+",
    "votre plateforme de mentorat",
    "d'événements et d'innovation"
];
let phraseIndex = 0;
let letterIndex = 0;
let isDeleting = false;

function typeWriter() {
    const currentPhrase = phrases[phraseIndex];
    if (!isDeleting) {
        rotatingText.textContent = currentPhrase.substring(0, letterIndex + 1);
        letterIndex++;
        if (letterIndex === currentPhrase.length) {
            isDeleting = true;
            setTimeout(typeWriter, 1500);
            return;
        }
    } else {
        rotatingText.textContent = currentPhrase.substring(0, letterIndex - 1);
        letterIndex--;
        if (letterIndex === 0) {
            isDeleting = false;
            phraseIndex = (phraseIndex + 1) % phrases.length;
        }
    }
    const speed = isDeleting ? 50 : 100;
    setTimeout(typeWriter, speed);
}
typeWriter();

// Animation au scroll
const revealElements = document.querySelectorAll('.reveal');

function revealOnScroll() {
    revealElements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight - 100) {
            el.classList.add('active');
        }
    });
}
window.addEventListener('scroll', revealOnScroll);
revealOnScroll();

// ===== REVEAL BOUNCE ANIMATION =====
const revealBounceElements = document.querySelectorAll('.reveal-bounce');

function revealOnScrolle() {
    revealBounceElements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight - 100) {
            el.classList.add('active');
        }
    });
}
window.addEventListener('scroll', revealOnScrolle);
revealOnScrolle();


// ====== EMAILJS + NOTIFICATION ======
(function() {
    emailjs.init("1JDzSe_39VPXVSWyi");
})();

const contactForm = document.querySelector(".contact-form");
const warningModal = document.getElementById("warningModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const modalMessage = document.getElementById("modalMessage");

// Fermer le modal
if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
        warningModal.classList.remove("show");
    });
}

if (contactForm) {
    contactForm.addEventListener("submit", function(e) {
        e.preventDefault();

        // 1. Récupération du message
        const messageInput = contactForm.querySelector("#message");
        const messageContent = messageInput.value;

        // 2. ANALYSE DU MESSAGE (REGEX)
        const checkResult = checkMessageQuality(messageContent);

        // Si le message est mauvais, on arrête tout et on affiche le modal
        if (!checkResult.valid) {
            modalMessage.innerText = checkResult.reason;
            warningModal.classList.add("show");

            // Petit effet visuel sur le champ message
            messageInput.style.border = "2px solid #ff4b2b";
            setTimeout(() => messageInput.style.border = "", 3000);
            return; // 🛑 ON ARRÊTE L'ENVOI ICI
        }

        // 3. Si tout est OK, on procède à l'envoi
        const btn = contactForm.querySelector(".send-btn");
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = "⏳ Envoi...";

        emailjs.sendForm("service_jv26ku9", "template_3as0j7q", this)
            .then(() => {
                showNotification("✅ Message envoyé avec succès !");
                contactForm.reset();
                btn.disabled = false;
                btn.innerHTML = originalText;
            }, (error) => {
                console.error(error);
                showNotification("❌ Erreur technique. Réessaie plus tard.");
                btn.disabled = false;
                btn.innerHTML = originalText;
            });
    });
}

// ====== FONCTION D'ANALYSE (REGEX) ======
function checkMessageQuality(text) {
    // Nettoyage basique (espaces début/fin)
    const cleanText = text.trim();

    // 1. Test de longueur minimale (évite "yo", "test", "coucou")
    if (cleanText.length < 15) {
        return { valid: false, reason: "Votre message est trop court. Veuillez détailler votre demande (min. 15 caractères)." };
    }

    // 2. Test Charabia / Clavier écrasé (ex: "jlgedbbxlldlsbxhh")
    // Cherche 5 consonnes consécutives ou plus, ou des répétitions excessives (aaaaaa)
    const gibberishRegex = /([bcdfghjklmnpqrstvwxyz]{5,})|(\w)\2{4,}/i;
    // Cherche un mot unique trop long sans espace (+ de 20 char)
    const longWordRegex = /^\S{20,}$/;

    if (gibberishRegex.test(cleanText) || longWordRegex.test(cleanText)) {
        return { valid: false, reason: "Ce message semble contenir du charabia ou une suite de lettres incohérente." };
    }

    // 3. Test Insultes & Mots Offensants (Liste non exhaustive)
    // \b assure qu'on cherche le mot entier (évite de bloquer "assis" pour "ss")
    const badWordsRegex = /\b(merde|stupide|kefero|gros|negre|negro|testicule|cretin|minable|pathetique|blaireau|tocard|sorcier|vampire|fou|cingle|bête|monstre|hideaux|face|phacochere|connard|batard|chien|cafard|malade|cul|babama|baba|mama|forondou|meurs|animal|dent|jaune|maman|papa|laid|bangalan|noyeaux|fesses|salot|culs|connasse|salope|putain|encul|fdp|abruti|idiot|conne|bâtard|tg|nique|con)\b/i;

    if (badWordsRegex.test(cleanText)) {
        return { valid: false, reason: "Merci de rester courtois. Les propos insultants ne sont pas acceptés." };
    }

    // 4. Test de phrases inutiles (ex: "Je suis beau", "rien à dire")
    // On cherche des motifs précis qui reviennent souvent dans le spam manuel
    const spamPhrasesRegex = /^(je suis beau|bla bla|echo|t'aime|heho|hey|bot|boeuf|faible qualite|test|rien|coucou|salut ça va|youpi|azerty)$/i;

    if (spamPhrasesRegex.test(cleanText)) {
        return { valid: false, reason: "Ce message ne semble pas être une demande sérieuse." };
    }

    // Si tout passe
    return { valid: true };
}

// ====== NOTIFICATION SUCCÈS (Toast) ======
function showNotification(message) {
    let notif = document.createElement("div");
    notif.className = "notif";
    notif.innerText = message;
    document.body.appendChild(notif);
    setTimeout(() => notif.classList.add("show"), 10);
    setTimeout(() => {
        notif.classList.remove("show");
        setTimeout(() => notif.remove(), 300);
    }, 3500);
}

// Autres animations (Input focus, Spinner)
window.addEventListener("load", () => {
    const spinner = document.getElementById("spinner");
    if (spinner) setTimeout(() => spinner.style.display = "none", 1200);
});

document.querySelectorAll(".input-icon input, .input-icon textarea").forEach(input => {
    input.addEventListener("focus", () => {
        if (input.parentElement) input.parentElement.style.boxShadow = "0 0 15px rgba(255,123,84,0.4)";
    });
    input.addEventListener("blur", () => {
        if (input.parentElement) input.parentElement.style.boxShadow = "none";
    });
});
document.addEventListener("DOMContentLoaded", function() {

    const profileModal = document.getElementById("profileModal");
    const confirmModal = document.getElementById("confirmModal");

    const openProfile = document.getElementById("openProfile");
    const closeProfile = document.getElementById("closeProfile");
    const closeProfileX = document.getElementById("closeProfileX");
    const logoutBtn = document.getElementById("logoutBtn");

    const confirmYes = document.getElementById("confirmYes");
    const confirmNo = document.getElementById("confirmNo");

    const card = document.getElementById("profileImageCard");

    /* ========= FONCTION FERMETURE GLOBALE ========= */
    function closeAll() {
        if (confirmModal) confirmModal.style.display = "none";
        if (profileModal) profileModal.style.display = "none";
        if (card) card.classList.remove("is-open");
    }

    /* ========= OUVERTURE PROFIL ========= */
    document.addEventListener("click", function(e) {
        const trigger = e.target.closest("#openProfile, [data-open-profile]");
        if (!trigger) return;

        e.preventDefault();
        if (profileModal) profileModal.style.display = "flex";

        // Sync email bas
        const emailTop = document.getElementById("profileEmail");
        const emailBottom = document.getElementById("profileEmail2");
        if (emailTop && emailBottom) {
            emailBottom.textContent = emailTop.textContent;
        }
    });

    /* ========= FERMETURE PROFIL ========= */
    if (closeProfile) closeProfile.addEventListener("click", closeAll);
    if (closeProfileX) closeProfileX.addEventListener("click", closeAll);

    if (profileModal) {
        profileModal.addEventListener("click", function(e) {
            if (e.target === profileModal) closeAll();
        });
    }
    /* ========= LOGOUT ========= */
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function(e) {
            e.preventDefault(); // empêche la redirection immédiate
            if (confirmModal) {
                confirmModal.style.display = "flex";
                confirmModal.classList.add("show");
            }
        });
    }

    /* ========= CONFIRMATION ========= */
    if (confirmNo) {
        confirmNo.addEventListener("click", function() {
            if (confirmModal) {
                confirmModal.classList.remove("show");
                setTimeout(() => confirmModal.style.display = "none", 200);
            }
        });
    }

    if (confirmYes) {
        confirmYes.addEventListener("click", function() {
            console.log("➡️ Bouton 'Oui' cliqué");

            if (confirmModal) confirmModal.style.display = "none";
            if (profileModal) profileModal.style.display = "none";
            if (card) card.classList.remove("is-open");

            const badge = document.getElementById("logoutBadge");
            if (badge) {
                badge.classList.add("show");
                setTimeout(() => badge.classList.remove("show"), 1500);
            }

            // Vérifie si le formulaire existe avant de soumettre
            const logoutForm = document.getElementById("logoutForm");
            if (logoutForm) {
                console.log("✅ Soumission du formulaire de déconnexion...");
                setTimeout(() => logoutForm.submit(), 1200);
            } else {
                console.warn("⚠️ Formulaire de déconnexion introuvable !");
            }
        });
    }

    /* ========= TOUCHE ESC ========= */
    document.addEventListener("keydown", function(e) {
        if (e.key !== "Escape") return;

        if (confirmModal && confirmModal.style.display === "flex") {
            confirmModal.style.display = "none";
        } else if (profileModal && profileModal.style.display === "flex") {
            profileModal.style.display = "none";
        }

        if (card) card.classList.remove("is-open");
    });
    /* ========= TAP MOBILE : REVEAL OVERLAY ========= */
    const isTouch =
        window.matchMedia("(hover: none)").matches ||
        window.matchMedia("(pointer: coarse)").matches;

    if (isTouch && card) {
        card.addEventListener("click", function(e) {
            if (e.target.closest("button, a")) return;
            card.classList.toggle("is-open");
        });
    }

});
// ===== BLOBS (desktop normal, mobile optimisé) =====
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

// Détection mobile / tactile
const isMobile = matchMedia("(max-width: 768px), (hover: none), (pointer: coarse)").matches;

// FPS cible : 60 desktop, 30 mobile
const targetFPS = isMobile ? 30 : 60;
const frameInterval = 1000 / targetFPS;

let t0 = performance.now();
let lastFrame = t0;
let running = true;

// Pause si onglet caché (énorme gain)
document.addEventListener("visibilitychange", () => {
    running = !document.hidden;
});

function tick(now) {
    requestAnimationFrame(tick);
    if (!running) return;

    // throttle FPS uniquement sur mobile
    if (isMobile && (now - lastFrame) < frameInterval) return;
    lastFrame = now;

    const dt = Math.min(32, now - t0);
    t0 = now;
    const time = now * 0.001;

    for (const b of blobs) {
        if (!b.el) continue;

        if (!isMobile) {
            // ===== DESKTOP: identique à ton comportement =====
            b.x += b.vx * (dt * 0.12) + Math.sin(time * 0.9 + b.y * 0.002) * 0.25;
            b.y += b.vy * (dt * 0.12) + Math.cos(time * 0.8 + b.x * 0.002) * 0.25;

            const pad = 140;
            if (b.x < -pad || b.x > w + pad) b.vx *= -1;
            if (b.y < -pad || b.y > h + pad) b.vy *= -1;

            const scale =
                b.s +
                Math.sin(time * 1.2 + b.x * 0.002) * 0.04 +
                Math.cos(time * 1.0 + b.y * 0.002) * 0.04;

            const rot = Math.sin(time * 0.7 + b.x * 0.001) * 8;

            b.el.style.transform =
                `translate3d(${b.x}px, ${b.y}px, 0) scale(${clamp(scale, 0.82, 1.28)}) rotate(${rot}deg)`;
        } else {
            // ===== MOBILE: plus doux + moins coûteux =====
            b.x += b.vx * (dt * 0.075) + Math.sin(time * 0.65 + b.y * 0.0016) * 0.12;
            b.y += b.vy * (dt * 0.075) + Math.cos(time * 0.62 + b.x * 0.0016) * 0.12;

            // pad plus large => moins de rebonds fréquents
            const pad = 240;
            if (b.x < -pad || b.x > w + pad) b.vx *= -1;
            if (b.y < -pad || b.y > h + pad) b.vy *= -1;

            // scale discret + rotation plus faible
            const scale =
                b.s +
                Math.sin(time * 0.85 + b.x * 0.0015) * 0.02 +
                Math.cos(time * 0.82 + b.y * 0.0015) * 0.02;

            const rot = Math.sin(time * 0.45 + b.x * 0.001) * 3;

            b.el.style.transform =
                `translate3d(${b.x}px, ${b.y}px, 0) scale(${clamp(scale, 0.90, 1.18)}) rotate(${rot}deg)`;
        }
    }
}

requestAnimationFrame(tick);

document.addEventListener("DOMContentLoaded", function() {

    /* ===== Welcome badge on load ===== */
    var welcome = document.getElementById("welcomeBadge");
    if (welcome) {
        // show
        setTimeout(function() {
            welcome.classList.add("show");
        }, 250);

        // hide after 3.2s
        setTimeout(function() {
            welcome.classList.remove("show");
            welcome.classList.add("hide");
        }, 3200);

        // remove hide class later (optional)
        setTimeout(function() {
            welcome.classList.remove("hide");
        }, 3800);
    }

    /* ===== Scroll to Top ===== */
    var btn = document.getElementById("scrollTopBtn");
    if (!btn) return;

    function toggleBtn() {
        if (window.scrollY > 420) btn.classList.add("show");
        else btn.classList.remove("show");
    }

    toggleBtn();
    window.addEventListener("scroll", toggleBtn, { passive: true });

    btn.addEventListener("click", function() {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

});

/* Pause animations when tab is hidden (perf + battery) */
(() => {
    const root = document.getElementById("bouquetFX");
    if (!root) return;

    const setPlay = (play) => {
        const state = play ? "running" : "paused";
        root.querySelectorAll("*").forEach(el => {
            if (el && el.style) el.style.animationPlayState = state;
        });
    };

    document.addEventListener("visibilitychange", () => {
        setPlay(!document.hidden);
    });
})();





(() => {
    const rail = document.getElementById("howRail");
    if (!rail) return;

    const cards = Array.from(rail.querySelectorAll(".how-stick"));

    function closeAll(except = null) {
        cards.forEach(c => { if (c !== except) c.classList.remove("is-open"); });
    }
    // Tap/click to toggle
    rail.addEventListener("click", (e) => {
        const card = e.target.closest(".how-stick");
        if (!card) return;

        // si on clique sur un bouton ou un lien, on ne toggle pas (on laisse l'action)
        const isBtn = e.target.closest("button, a");
        if (isBtn) return;

        const willOpen = !card.classList.contains("is-open");
        closeAll(card);
        card.classList.toggle("is-open", willOpen);
    });

    // Keyboard (Enter/Space)
    rail.addEventListener("keydown", (e) => {
        const card = e.target.closest(".how-stick");
        if (!card) return;
        if (e.key !== "Enter" && e.key !== " ") return;

        e.preventDefault();
        const willOpen = !card.classList.contains("is-open");
        closeAll(card);
        card.classList.toggle("is-open", willOpen);
    });

    // Click outside closes (optional)
    document.addEventListener("click", (e) => {
        if (e.target.closest("#howRail")) return;
        closeAll();
    }, { passive: true });
})();