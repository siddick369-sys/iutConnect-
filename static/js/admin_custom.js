// === Petites particules dorées flottantes ===
document.addEventListener('DOMContentLoaded', () => {
    const container = document.body;
    for (let i = 0; i < 20; i++) {
        let particle = document.createElement('div');
        particle.classList.add('particle');
        container.appendChild(particle);

        const size = Math.random() * 5 + 3;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.background = 'rgba(212,175,55,0.6)';
        particle.style.position = 'fixed';
        particle.style.borderRadius = '50%';
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.animation = `float ${5 + Math.random() * 10}s ease-in-out infinite`;
    }
});

const style = document.createElement('style');
style.textContent = `
@keyframes float {
    0%, 100% { transform: translateY(0); opacity: 0.8; }
    50% { transform: translateY(-30px); opacity: 1; }
}
`;
document.head.appendChild(style);