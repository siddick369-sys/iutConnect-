// // Spinner disparition après chargement
// window.addEventListener("load", () => {
//     setTimeout(() => {
//         document.getElementById("spinner").style.display = "none";
//     }, 1200);
// });

// // Animation des champs input
// document.querySelectorAll(".input-icon input").forEach(input => {
//     input.addEventListener("focus", () => {
//         input.parentElement.style.boxShadow = "0 0 15px rgba(255,123,84,0.4)";
//     });
//     input.addEventListener("blur", () => {
//         input.parentElement.style.boxShadow = "none";
//     });
// });



// ==== MODAL PROFIL ====
const profileModal = document.getElementById("profileModal");
const confirmModal = document.getElementById("confirmModal");
const openProfile = document.getElementById("openProfile");
const closeProfile = document.getElementById("closeProfile");
const logoutBtn = document.getElementById("logoutBtn");
const confirmYes = document.getElementById("confirmYes");
const confirmNo = document.getElementById("confirmNo");

// Ouvrir le profil
openProfile.addEventListener("click", (e) => {
    e.preventDefault();
    profileModal.style.display = "flex";
});

// Fermer le profil
closeProfile.addEventListener("click", () => {
    profileModal.style.display = "none";
});

// Ouvrir confirmation
logoutBtn.addEventListener("click", () => {
    confirmModal.style.display = "flex";
});
confirmYes.addEventListener("click", () => {
    confirmModal.style.display = "none";
    profileModal.style.display = "none";

    const badge = document.getElementById("logoutBadge");
    badge.classList.add("show");

    // Cache le badge après 2,5 secondes
    setTimeout(() => {
        badge.classList.remove("show");
        // Ici tu peux rediriger vers login.html si tu veux :
        // window.location.href = "login.html";
    }, 2500);
});