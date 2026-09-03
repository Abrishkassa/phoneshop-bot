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
const loadingState = document.getElementById("loadingState");
const sheetOverlay = document.getElementById("sheetOverlay");
const sheetContent = document.getElementById("sheetContent");
const compareBar = document.getElementById("compareBar");
const compareText = document.getElementById("compareText");
const brandFilters = document.getElementById("brandFilters");
const searchInput = document.getElementById("searchInput");

function tgUser() {
  return tg?.initDataUnsafe?.user || null;
}

function money(n) {
  return Number(n).toLocaleString();
}

async function fetchBrands() {
  const res = await fetch(`/api/brands?category=${state.category}`);
  const brands = await res.json();

  if (!brands.length) {
    brandFilters.innerHTML = "";
    return;
  }
  brandFilters.innerHTML =
    `<button class="chip active" data-brand="">All brands</button>` +
    brands.map((b) => `<button class="chip" data-brand="${b}">${b}</button>`).join("");
}

async function fetchProducts() {
  loadingState.classList.remove("hidden");
  emptyState.classList.add("hidden");
  grid.innerHTML = "";

  const params = new URLSearchParams({ category: state.category, price_range: state.priceRange });
  if (state.brand) params.set("brand", state.brand);
  if (state.search) params.set("search", state.search);

  const res = await fetch(`/api/products?${params}`);
  const products = await res.json();

  loadingState.classList.add("hidden");
  if (!products.length) {
    emptyState.classList.remove("hidden");
    return;
  }
  renderGrid(products);
}

function renderGrid(products) {
  grid.innerHTML = products
    .map((p) => {
      const hasDiscount = p.discount_price != null;
      const displayPrice = hasDiscount ? p.discount_price : p.price;
      const stockLabel =
        p.stock_qty === 0
          ? '<span class="card-stock out">Out of stock</span>'
          : p.stock_qty <= 2
          ? `<span class="card-stock low">⚡ Only ${p.stock_qty} left</span>`
          : `<span class="card-stock">In stock</span>`;

      return `
        <div class="card" data-id="${p.id}">
          ${p.is_featured ? '<div class="card-badge">FEATURED</div>' : ""}
          <div class="card-img">${
            p.photo_urls?.[0]
              ? `<img src="${p.photo_urls[0]}" alt="${p.name}" />`
              : "📱"
          }</div>
          <div class="card-name">${p.name}</div>
          <div class="card-price">
            ${hasDiscount ? `<span class="was">${money(p.price)} ETB</span>` : ""}
            ${money(displayPrice)} ETB
          </div>
          ${stockLabel}
        </div>`;
    })
    .join("");

  grid.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("click", () => openDetail(Number(card.dataset.id)));
  });
}

async function openDetail(productId) {
  const res = await fetch(`/api/products/${productId}`);
  if (!res.ok) return;
  const p = await res.json();

  const hasDiscount = p.discount_price != null;
  const displayPrice = hasDiscount ? p.discount_price : p.price;
  const specsRows = Object.entries(p.specs || {})
    .map(([k, v]) => `<div class="sheet-row"><span>${k}</span><span>${v}</span></div>`)
    .join("");
  const colorChips = (p.colors || [])
    .map((c) => `<button class="color-chip" data-color="${c}">${c}</button>`)
    .join("");

  sheetContent.innerHTML = `
    <div class="sheet-img">${
      p.photo_urls?.[0] ? `<img src="${p.photo_urls[0]}" alt="${p.name}" />` : "📱"
    }</div>
    <div class="sheet-name">${p.name}</div>
    <div class="sheet-price">
      ${hasDiscount ? `<span class="was">${money(p.price)} ETB</span>` : ""}
      ${money(displayPrice)} ETB
    </div>
    ${colorChips ? `<div class="color-chips">${colorChips}</div>` : ""}
    ${specsRows}
    <div class="sheet-row"><span>Stock</span><span>${p.stock_qty > 0 ? p.stock_qty + " available" : "Out of stock"}</span></div>

    <button class="btn btn-primary" id="requestDeliveryBtn" ${p.stock_qty === 0 ? "disabled" : ""}>
      ✅ Request Delivery
    </button>
    <button class="btn btn-outline" id="compareBtn">🔍 Add to Compare</button>
  `;

  let selectedColor = null;
  sheetContent.querySelectorAll(".color-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      sheetContent.querySelectorAll(".color-chip").forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
      selectedColor = chip.dataset.color;
    });
  });

  document.getElementById("requestDeliveryBtn").addEventListener("click", () =>
    submitDelivery(p.id, selectedColor)
  );
  document.getElementById("compareBtn").addEventListener("click", () => addToCompare(p.id, p.name));

  sheetOverlay.classList.remove("hidden");
}

sheetOverlay.addEventListener("click", (e) => {
  if (e.target === sheetOverlay) sheetOverlay.classList.add("hidden");
});

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
    tg?.showAlert?.("Something went wrong. Please try again.");
    return;
  }
  const data = await res.json();
  sheetOverlay.classList.add("hidden");
  tg?.showAlert?.(`✅ Request sent! Reference #${data.reference_code}. The shop will contact you shortly.`);
}

function addToCompare(id, name) {
  if (!state.compareIds.find((c) => c.id === id)) {
    state.compareIds.push({ id, name });
    if (state.compareIds.length > 2) state.compareIds.shift();
  }
  updateCompareBar();

  if (state.compareIds.length === 2) {
    sheetOverlay.classList.add("hidden");
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
      ? `Comparing: ${state.compareIds[0].name} — pick one more`
      : `Comparing: ${state.compareIds.map((c) => c.name).join(" vs ")}`;
}

document.getElementById("compareClear").addEventListener("click", () => {
  state.compareIds = [];
  updateCompareBar();
});

async function showCompare() {
  const [a, b] = await Promise.all(
    state.compareIds.map((c) => fetch(`/api/products/${c.id}`).then((r) => r.json()))
  );

  const rows = [
    ["Price", `${money(a.discount_price ?? a.price)} ETB`, `${money(b.discount_price ?? b.price)} ETB`],
    ["Colors", (a.colors || []).join(", ") || "—", (b.colors || []).join(", ") || "—"],
    ["Stock", a.stock_qty, b.stock_qty],
    ...Object.keys({ ...a.specs, ...b.specs }).map((k) => [k, a.specs?.[k] ?? "—", b.specs?.[k] ?? "—"]),
  ];

  sheetContent.innerHTML = `
    <div class="sheet-name">Comparing</div>
    <table class="compare-table">
      <tr><th></th><th>${a.name}</th><th>${b.name}</th></tr>
      ${rows.map(([label, av, bv]) => `<tr><th>${label}</th><td>${av}</td><td>${bv}</td></tr>`).join("")}
    </table>
    <button class="btn btn-secondary" id="closeCompareBtn">Close</button>
  `;
  document.getElementById("closeCompareBtn").addEventListener("click", () => {
    sheetOverlay.classList.add("hidden");
    state.compareIds = [];
    updateCompareBar();
  });
  sheetOverlay.classList.remove("hidden");
}

document.getElementById("categoryTabs").addEventListener("click", (e) => {
  const btn = e.target.closest(".tab");
  if (!btn) return;
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  btn.classList.add("active");
  state.category = btn.dataset.category;
  state.brand = "";
  fetchBrands();
  fetchProducts();
});

document.getElementById("priceFilters").addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (!btn) return;
  document.querySelectorAll("#priceFilters .chip").forEach((c) => c.classList.remove("active"));
  btn.classList.add("active");
  state.priceRange = btn.dataset.range;
  fetchProducts();
});

brandFilters.addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (!btn) return;
  document.querySelectorAll("#brandFilters .chip").forEach((c) => c.classList.remove("active"));
  btn.classList.add("active");
  state.brand = btn.dataset.brand;
  fetchProducts();
});

let searchDebounce;
searchInput.addEventListener("input", (e) => {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => {
    state.search = e.target.value.trim();
    fetchProducts();
  }, 350);
});

fetchBrands();
fetchProducts();