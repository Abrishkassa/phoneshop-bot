const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const state = {
  category: "phone",
  priceRange: "all",
  brand: "",
  search: "",
  compareIds: [],
};

const grid = document.getElementById("grid");
const emptyState = document.getElementById("emptyState");
const sheetOverlay = document.getElementById("sheetOverlay");
const sheetContent = document.getElementById("sheetContent");
const compareBar = document.getElementById("compareBar");
const compareText = document.getElementById("compareText");
const compareAvatars = document.getElementById("compareAvatars");
const compareGo = document.getElementById("compareGo");
const brandFilters = document.getElementById("brandFilters");
const searchInput = document.getElementById("searchInput");
const searchClear = document.getElementById("searchClear");

const CATEGORY_ICONS = {
  phone: "smartphone",
  laptop: "laptop",
  earphone: "headphones",
  accessory: "plug-zap",
};

const SPEC_ICONS = [
  ["ram", "memory-stick"],
  ["storage", "hard-drive"],
  ["processor", "cpu"],
  ["battery", "battery-charging"],
  ["display", "monitor"],
  ["screen", "monitor"],
  ["camera", "camera"],
  ["bluetooth", "bluetooth"],
  ["connectivity", "wifi"],
  ["charging", "zap"],
  ["type", "headphones"],
  ["brand", "badge-check"],
];

/* ---------- helpers ---------- */

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function money(n) {
  return Number(n).toLocaleString();
}

function refreshIcons() {
  window.lucide?.createIcons();
}

function haptic(kind = "light") {
  tg?.HapticFeedback?.impactOccurred?.(kind);
}

function hapticResult(ok) {
  tg?.HapticFeedback?.notificationOccurred?.(ok ? "success" : "error");
}

function tgUser() {
  return tg?.initDataUnsafe?.user || null;
}

function specIcon(key) {
  const k = String(key).toLowerCase();
  const hit = SPEC_ICONS.find(([term]) => k.includes(term));
  return hit ? hit[1] : "circle-dot";
}

function stockPill(qty) {
  if (qty === 0) return `<span class="pill pill-out"><i data-lucide="x-circle"></i>Out of stock</span>`;
  if (qty <= 2) return `<span class="pill pill-low"><i data-lucide="flame"></i>Only ${qty} left</span>`;
  return `<span class="pill pill-in"><i data-lucide="check-circle-2"></i>In stock</span>`;
}

let toastTimer;
function toast(message, kind = "success") {
  const el = document.getElementById("toast");
  const icon = kind === "success" ? "check-circle-2" : "circle-alert";
  el.className = `toast ${kind}`;
  el.innerHTML = `<i data-lucide="${icon}"></i><span>${esc(message)}</span>`;
  refreshIcons();
  requestAnimationFrame(() => el.classList.add("show"));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3400);
}

/* ---------- data ---------- */

function renderSkeleton() {
  grid.innerHTML = Array(6)
    .fill(0)
    .map(
      () => `
      <div class="skeleton-card">
        <div class="skeleton-img"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line short"></div>
      </div>`
    )
    .join("");
}

async function fetchBrands() {
  const res = await fetch(`/api/brands?category=${state.category}`, { cache: "no-store" });
  const brands = await res.json();

  if (!brands.length) {
    brandFilters.innerHTML = "";
    return;
  }
  brandFilters.innerHTML =
    `<button class="chip active" data-brand="">All brands</button>` +
    brands.map((b) => `<button class="chip" data-brand="${esc(b)}">${esc(b)}</button>`).join("");
  refreshIcons();
}

async function fetchProducts() {
  renderSkeleton();
  emptyState.classList.add("hidden");

  const params = new URLSearchParams({ category: state.category, price_range: state.priceRange });
  if (state.brand) params.set("brand", state.brand);
  if (state.search) params.set("search", state.search);

  const res = await fetch(`/api/products?${params}`, { cache: "no-store" });
  const products = await res.json();

  if (!products.length) {
    grid.innerHTML = "";
    emptyState.classList.remove("hidden");
    refreshIcons();
    return;
  }
  renderGrid(products);
}

/* ---------- grid ---------- */

function renderGrid(products) {
  grid.innerHTML = products
    .map((p, i) => {
      const hasDiscount = p.discount_price != null;
      const price = hasDiscount ? p.discount_price : p.price;
      const offPct = hasDiscount ? Math.round((1 - p.discount_price / p.price) * 100) : 0;
      const badge = hasDiscount
        ? `<div class="ribbon"><i data-lucide="badge-percent"></i>-${offPct}%</div>`
        : p.is_featured
        ? `<div class="ribbon featured"><i data-lucide="star"></i>Featured</div>`
        : "";

      return `
        <div class="card" data-id="${p.id}" style="animation-delay:${Math.min(i, 8) * 45}ms">
          ${badge}
          <div class="card-img">${
            p.photo_urls?.[0]
              ? `<img src="${esc(p.photo_urls[0])}" alt="${esc(p.name)}" loading="lazy" />`
              : `<i data-lucide="${CATEGORY_ICONS[p.category] || "package"}"></i>`
          }</div>
          <div class="card-body">
            <div class="card-name">${esc(p.name)}</div>
            <div class="card-price-row">
              <span class="card-price">${money(price)} <small>ETB</small></span>
              ${hasDiscount ? `<span class="was">${money(p.price)}</span>` : ""}
            </div>
            ${stockPill(p.stock_qty)}
          </div>
        </div>`;
    })
    .join("");

  grid.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("click", () => openDetail(Number(card.dataset.id)));
  });
  refreshIcons();
}

/* ---------- detail sheet ---------- */

async function openDetail(productId) {
  const res = await fetch(`/api/products/${productId}`, { cache: "no-store" });
  if (!res.ok) return;
  const p = await res.json();

  const hasDiscount = p.discount_price != null;
  const price = hasDiscount ? p.discount_price : p.price;
  const offPct = hasDiscount ? Math.round((1 - p.discount_price / p.price) * 100) : 0;

  const specsRows = Object.entries(p.specs || {})
    .map(
      ([k, v]) => `
      <div class="sheet-row">
        <span class="label"><i data-lucide="${specIcon(k)}"></i>${esc(k)}</span>
        <span class="value">${esc(v)}</span>
      </div>`
    )
    .join("");

  const colorChips = (p.colors || [])
    .map(
      (c) => `
      <button class="color-chip" data-color="${esc(c)}">
        <span class="swatch" style="background:${esc(c)}"></span>${esc(c)}
      </button>`
    )
    .join("");

  const photos = p.photo_urls?.length ? p.photo_urls : [null];
  const carouselSlides = photos
    .map(
      (url) =>
        `<div class="carousel-slide">${
          url ? `<img src="${esc(url)}" alt="${esc(p.name)}" />` : `<i data-lucide="${CATEGORY_ICONS[p.category] || "package"}"></i>`
        }</div>`
    )
    .join("");
  const carouselDots =
    photos.length > 1
      ? `<div class="carousel-dots">${photos
          .map((_, i) => `<span class="dot${i === 0 ? " active" : ""}" data-index="${i}"></span>`)
          .join("")}</div>`
      : "";

  sheetContent.innerHTML = `
    <div class="carousel" id="photoCarousel">
      <div class="carousel-track">${carouselSlides}</div>
      ${carouselDots}
    </div>

    <h2 class="sheet-name">${esc(p.name)}</h2>
    <div class="sheet-meta">
      ${p.brand ? `<span class="pill pill-brand"><i data-lucide="badge-check"></i>${esc(p.brand)}</span>` : ""}
      ${stockPill(p.stock_qty)}
    </div>

    <div class="sheet-price">
      ${hasDiscount ? `<span class="was">${money(p.price)}</span>` : ""}
      <span>${money(price)} ETB</span>
      ${hasDiscount ? `<span class="off">SAVE ${offPct}%</span>` : ""}
    </div>

    ${colorChips ? `<h3 class="section-title"><i data-lucide="palette"></i>Colors</h3><div class="color-chips">${colorChips}</div>` : ""}

    ${specsRows ? `<h3 class="section-title"><i data-lucide="list-checks"></i>Specifications</h3><div class="spec-list">${specsRows}</div>` : ""}

    <div class="sheet-footer">
      <button class="btn btn-primary" id="requestDeliveryBtn" ${p.stock_qty === 0 ? "disabled" : ""}>
        <i data-lucide="truck"></i>${p.stock_qty === 0 ? "Out of stock" : "Request Delivery"}
      </button>
      <button class="btn btn-icon-only" id="compareBtn" title="Add to Compare" aria-label="Add to Compare">
        <i data-lucide="columns-2"></i>
      </button>
    </div>
  `;

  if (photos.length > 1) {
    setupCarousel(document.getElementById("photoCarousel"));
  }

  let selectedColor = null;
  sheetContent.querySelectorAll(".color-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      sheetContent.querySelectorAll(".color-chip").forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
      selectedColor = chip.dataset.color;
      haptic();
    });
  });

  document.getElementById("requestDeliveryBtn").addEventListener("click", () =>
    submitDelivery(p.id, selectedColor)
  );
  document.getElementById("compareBtn").addEventListener("click", () =>
    addToCompare(p.id, p.name, p.photo_urls?.[0] || null)
  );

  sheetOverlay.classList.remove("hidden");
  sheetOverlay.querySelector(".sheet").scrollTop = 0;
  refreshIcons();
}

function setupCarousel(carouselEl) {
  const track = carouselEl.querySelector(".carousel-track");
  const dots = carouselEl.querySelectorAll(".dot");
  let current = 0;
  let startX = 0;

  function goTo(index) {
    current = Math.max(0, Math.min(index, dots.length - 1));
    track.style.transform = `translateX(-${current * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle("active", i === current));
    haptic();
  }

  track.addEventListener("touchstart", (e) => {
    startX = e.touches[0].clientX;
  });
  track.addEventListener("touchend", (e) => {
    const diff = e.changedTouches[0].clientX - startX;
    if (diff > 40) goTo(current - 1);
    else if (diff < -40) goTo(current + 1);
  });

  dots.forEach((dot) => {
    dot.addEventListener("click", () => goTo(Number(dot.dataset.index)));
  });
}

function closeSheet() {
  sheetOverlay.classList.add("hidden");
}

sheetOverlay.addEventListener("click", (e) => {
  if (e.target === sheetOverlay) closeSheet();
});
document.getElementById("sheetClose").addEventListener("click", closeSheet);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeSheet();
});

/* ---------- delivery ---------- */

async function submitDelivery(productId, color) {
  const user = tgUser();
  const res = await fetch("/api/inquiries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      telegram_id: user?.id || 0,
      telegram_username: user?.username || null,
      product_id: productId,
      preferred_color: color,
    }),
  });

  if (!res.ok) {
    hapticResult(false);
    toast("Something went wrong. Please try again.", "error");
    return;
  }
  const data = await res.json();
  closeSheet();
  hapticResult(true);
  toast(`Request sent! Reference #${data.reference_code} — the shop will contact you.`);
}

/* ---------- compare ---------- */

function addToCompare(id, name, photo) {
  if (!state.compareIds.find((c) => c.id === id)) {
    state.compareIds.push({ id, name, photo });
    if (state.compareIds.length > 2) state.compareIds.shift();
  }
  updateCompareBar();

  if (state.compareIds.length === 2) {
    closeSheet();
    showCompare();
  }
}

function updateCompareBar() {
  if (!state.compareIds.length) {
    compareBar.classList.add("hidden");
    return;
  }
  compareBar.classList.remove("hidden");
  compareText.textContent =
    state.compareIds.length === 1
      ? `${state.compareIds[0].name} — pick one more`
      : `${state.compareIds[0].name} vs ${state.compareIds[1].name}`;

  compareAvatars.innerHTML = state.compareIds
    .map(
      (c) =>
        `<div class="avatar">${c.photo ? `<img src="${esc(c.photo)}" alt="" />` : `<i data-lucide="package"></i>`}</div>`
    )
    .join("");

  compareGo.classList.toggle("hidden", state.compareIds.length < 2);
  refreshIcons();
}

document.getElementById("compareClear").addEventListener("click", () => {
  state.compareIds = [];
  updateCompareBar();
});
compareGo.addEventListener("click", showCompare);

async function showCompare() {
  const [a, b] = await Promise.all(
    state.compareIds.map((c) =>
      fetch(`/api/products/${c.id}`, { cache: "no-store" }).then((r) => r.json())
    )
  );

  const priceA = Number(a.discount_price ?? a.price);
  const priceB = Number(b.discount_price ?? b.price);
  const aCheaper = priceA < priceB;
  const bCheaper = priceB < priceA;

  const thumb = (p) =>
    p.photo_urls?.[0]
      ? `<img src="${esc(p.photo_urls[0])}" alt="" />`
      : `<i data-lucide="${CATEGORY_ICONS[p.category] || "package"}"></i>`;

  const rows = [
    ["Colors", (a.colors || []).join(", ") || "—", (b.colors || []).join(", ") || "—"],
    ["Stock", a.stock_qty, b.stock_qty],
    ...Object.keys({ ...a.specs, ...b.specs }).map((k) => [k, a.specs?.[k] ?? "—", b.specs?.[k] ?? "—"]),
  ];

  sheetContent.innerHTML = `
    <h2 class="sheet-name">Compare</h2>
    <div class="compare-heads">
      <div class="compare-head">
        <div class="thumb">${thumb(a)}</div>
        <div class="cname">${esc(a.name)}</div>
        <div class="cprice">${money(priceA)} ETB</div>
      </div>
      <div class="compare-head">
        <div class="thumb">${thumb(b)}</div>
        <div class="cname">${esc(b.name)}</div>
        <div class="cprice">${money(priceB)} ETB</div>
      </div>
    </div>
    <table class="compare-table">
      <tr>
        <th>Price</th>
        <td class="${aCheaper ? "better" : ""}">${money(priceA)} ETB</td>
        <td class="${bCheaper ? "better" : ""}">${money(priceB)} ETB</td>
      </tr>
      ${rows
        .map(([label, av, bv]) => `<tr><th>${esc(label)}</th><td>${esc(av)}</td><td>${esc(bv)}</td></tr>`)
        .join("")}
    </table>
    <div class="sheet-footer">
      <button class="btn btn-secondary" id="closeCompareBtn"><i data-lucide="x"></i>Close</button>
    </div>
  `;
  document.getElementById("closeCompareBtn").addEventListener("click", () => {
    closeSheet();
    state.compareIds = [];
    updateCompareBar();
  });
  sheetOverlay.classList.remove("hidden");
  sheetOverlay.querySelector(".sheet").scrollTop = 0;
  refreshIcons();
}

/* ---------- filters & search ---------- */

document.getElementById("categoryTabs").addEventListener("click", (e) => {
  const btn = e.target.closest(".tab");
  if (!btn) return;
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  btn.classList.add("active");
  state.category = btn.dataset.category;
  state.brand = "";
  haptic();
  fetchBrands();
  fetchProducts();
});

document.getElementById("priceFilters").addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (!btn) return;
  document.querySelectorAll("#priceFilters .chip").forEach((c) => c.classList.remove("active"));
  btn.classList.add("active");
  state.priceRange = btn.dataset.range;
  haptic();
  fetchProducts();
});

brandFilters.addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (!btn) return;
  document.querySelectorAll("#brandFilters .chip").forEach((c) => c.classList.remove("active"));
  btn.classList.add("active");
  state.brand = btn.dataset.brand;
  haptic();
  fetchProducts();
});

let searchDebounce;
searchInput.addEventListener("input", (e) => {
  searchClear.classList.toggle("hidden", !e.target.value);
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => {
    state.search = e.target.value.trim();
    fetchProducts();
  }, 350);
});

searchClear.addEventListener("click", () => {
  searchInput.value = "";
  searchClear.classList.add("hidden");
  state.search = "";
  fetchProducts();
  searchInput.focus();
});

/* ---------- boot ---------- */

refreshIcons();
fetchBrands();
fetchProducts();
