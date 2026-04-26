const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

document.querySelectorAll(".flash").forEach((flash) => {
  setTimeout(() => {
    flash.style.opacity = "0";
    flash.style.transform = "translateY(-8px)";
  }, 4500);
});

const participantType = document.querySelector("#id_participant_type");
const dynamicFields = document.querySelectorAll("[data-for]");

function syncDynamicFields() {
  if (!participantType) return;
  const current = participantType.value;
  dynamicFields.forEach((field) => {
    const enabled = field.dataset.for.split(" ").includes(current);
    field.style.display = enabled ? "grid" : "none";
    field.querySelectorAll("input").forEach((input) => {
      input.disabled = !enabled;
    });
  });
}

if (participantType) {
  participantType.addEventListener("change", syncDynamicFields);
  syncDynamicFields();
}

const liveCards = document.querySelectorAll("[data-live-card]");
if (liveCards.length) {
  function randomPercent(base) {
    const delta = Math.floor(Math.random() * 10) - 5;
    return Math.max(58, Math.min(98, base + delta));
  }

  setInterval(() => {
    liveCards.forEach((card) => {
      const valueNode = card.querySelector("[data-live-value]");
      const meterNode = card.querySelector("[data-live-meter]");
      const current = Number.parseInt(valueNode.textContent, 10) || 80;
      const next = randomPercent(current);
      valueNode.textContent = `${next}%`;
      meterNode.style.width = `${next}%`;
    });
  }, 2200);
}

const heroPanel = document.querySelector(".hero-copy");
const speakerPanel = document.querySelector(".speaker-card");
if (heroPanel && speakerPanel) {
  function tiltPanel(event) {
    const x = (event.clientX / window.innerWidth) - 0.5;
    const y = (event.clientY / window.innerHeight) - 0.5;
    heroPanel.style.transform = `translate3d(${x * 8}px, ${y * 8}px, 0)`;
    speakerPanel.style.transform = `translate3d(${x * -10}px, ${y * -10}px, 0)`;
  }

  function resetPanelTilt() {
    heroPanel.style.transform = "";
    speakerPanel.style.transform = "";
  }

  window.addEventListener("mousemove", tiltPanel, { passive: true });
  window.addEventListener("mouseleave", resetPanelTilt, { passive: true });
}

const matrixCanvas = document.querySelector("#matrixCanvas");
if (matrixCanvas) {
  const ctx = matrixCanvas.getContext("2d");
  const tokens = ["W", "A", "S", "V", "T", "0", "1", "</>", "SQL", "JWT", "TLS", "XSS"];
  let columns = [];

  function resizeMatrix() {
    const ratio = window.devicePixelRatio || 1;
    matrixCanvas.width = window.innerWidth * ratio;
    matrixCanvas.height = window.innerHeight * ratio;
    matrixCanvas.style.width = `${window.innerWidth}px`;
    matrixCanvas.style.height = `${window.innerHeight}px`;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    const count = Math.ceil(window.innerWidth / 34);
    columns = Array.from({ length: count }, (_, index) => ({
      x: index * 34,
      y: Math.random() * window.innerHeight,
      speed: 0.55 + Math.random() * 1.15,
      token: tokens[Math.floor(Math.random() * tokens.length)],
    }));
  }

  function drawMatrix() {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    ctx.font = "12px Consolas, monospace";
    columns.forEach((column) => {
      const gradient = ctx.createLinearGradient(0, column.y - 80, 0, column.y + 20);
      gradient.addColorStop(0, "rgba(55, 213, 255, 0)");
      gradient.addColorStop(1, "rgba(83, 243, 162, 0.55)");
      ctx.fillStyle = gradient;
      ctx.fillText(column.token, column.x, column.y);
      column.y += column.speed;
      if (column.y > window.innerHeight + 40) {
        column.y = -20;
        column.token = tokens[Math.floor(Math.random() * tokens.length)];
      }
    });
    requestAnimationFrame(drawMatrix);
  }

  resizeMatrix();
  drawMatrix();
  window.addEventListener("resize", resizeMatrix);
}
