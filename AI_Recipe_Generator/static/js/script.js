/* =========================================================
   AI Recipe Generator — Front-end interactivity
   ========================================================= */

// ---- Sidebar toggle (mobile) ----
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove("open");
      }
    });
  }

  // Auto-dismiss flash messages
  document.querySelectorAll(".flash-msg").forEach((el, i) => {
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity 0.4s ease"; }, 4000 + i * 300);
    setTimeout(() => el.remove(), 4500 + i * 300);
  });

  initMealFilters();
  initGenerateButton();
});

function getCSRFToken() {
  const input = document.querySelector('input[name="csrf_token"]');
  return input ? input.value : "";
}

function showLoading(text) {
  const overlay = document.getElementById("aiLoadingOverlay");
  const label = document.getElementById("aiLoadingText");
  if (label && text) label.textContent = text;
  if (overlay) overlay.classList.add("show");
}
function hideLoading() {
  const overlay = document.getElementById("aiLoadingOverlay");
  if (overlay) overlay.classList.remove("show");
}

// ---- Dashboard: meal type filters ----
function initMealFilters() {
  const filters = document.querySelectorAll(".meal-filter-chip");
  if (!filters.length) return;
  filters.forEach((chip) => {
    chip.addEventListener("click", () => {
      const meal = chip.dataset.meal;
      window.location.href = `/dashboard?meal_type=${encodeURIComponent(meal)}`;
    });
  });
}

// ---- Dashboard: Generate Recipes button ----
function initGenerateButton() {
  const btn = document.getElementById("generateBtn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const activeChip = document.querySelector(".meal-filter-chip.active");
    const mealType = activeChip ? activeChip.dataset.meal : "Dinner";

    btn.disabled = true;
    showLoading(`Generating ${mealType} recipes from your pantry...`);

    try {
      const res = await fetch("/api/generate-recipes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meal_type: mealType }),
      });
      const data = await res.json();

      if (data.success) {
        // Simplest reliable UX: reload dashboard scoped to this meal type
        window.location.href = `/dashboard?meal_type=${encodeURIComponent(mealType)}`;
      } else {
        alert("Could not generate recipes. Please try again.");
      }
    } catch (err) {
      alert("Something went wrong while generating recipes.");
    } finally {
      hideLoading();
      btn.disabled = false;
    }
  });
}

// ---- Favourites toggle (used on dashboard, favourites, recipe details) ----
async function toggleFavorite(recipeId, btnEl) {
  try {
    const res = await fetch(`/favorites/toggle/${recipeId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await res.json();
    if (data.success) {
      const icon = btnEl.querySelector("i");
      if (data.favorited) {
        btnEl.classList.add("active");
        icon.classList.remove("bi-heart");
        icon.classList.add("bi-heart-fill");
      } else {
        btnEl.classList.remove("active");
        icon.classList.remove("bi-heart-fill");
        icon.classList.add("bi-heart");
        // If we're on the favourites page, remove the card entirely
        if (window.location.pathname.startsWith("/favorites")) {
          const card = btnEl.closest(".recipe-card");
          if (card) card.remove();
        }
      }
    }
  } catch (err) {
    console.error("Favourite toggle failed", err);
  }
}

// ---- Pantry: quick add ----
async function quickAdd(ingredient, category) {
  try {
    const res = await fetch("/pantry/quick-add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ingredient, category }),
    });
    const data = await res.json();
    if (data.success) {
      window.location.reload();
    }
  } catch (err) {
    console.error("Quick add failed", err);
  }
}

// ---- Pantry: delete item ----
async function deletePantryItem(itemId) {
  if (!confirm("Remove this ingredient from your pantry?")) return;
  try {
    const res = await fetch(`/pantry/delete/${itemId}`, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data = await res.json();
    if (data.success) {
      const el = document.getElementById(`pantry-item-${itemId}`);
      if (el) el.remove();
    }
  } catch (err) {
    console.error("Delete failed", err);
  }
}

// ---- Meal planner: "Save" modal from dashboard cards ----
let pendingPlanRecipeId = null;

function openPlanModal(recipeId, title) {
  pendingPlanRecipeId = recipeId;
  const nameEl = document.getElementById("planRecipeName");
  const dateEl = document.getElementById("planDate");
  if (nameEl) nameEl.textContent = title;
  if (dateEl) dateEl.value = new Date().toISOString().split("T")[0];

  const modalEl = document.getElementById("planModal");
  if (modalEl) new bootstrap.Modal(modalEl).show();
}

document.addEventListener("DOMContentLoaded", () => {
  const confirmBtn = document.getElementById("confirmPlanBtn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", async () => {
      const date = document.getElementById("planDate").value;
      const mealType = document.getElementById("planMealType").value;
      if (!pendingPlanRecipeId || !date) return;

      try {
        const res = await fetch("/meal-plan/add", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ recipe_id: pendingPlanRecipeId, date, meal_type: mealType }),
        });
        const data = await res.json();
        if (data.success) {
          bootstrap.Modal.getInstance(document.getElementById("planModal")).hide();
          alert("Added to your meal planner!");
        }
      } catch (err) {
        console.error("Add to plan failed", err);
      }
    });
  }
});

// ---- Meal planner page: add plan modal ----
function openAddPlanModal(dateStr, recipeId, title) {
  const dateEl = document.getElementById("addPlanDate");
  const selectEl = document.getElementById("planRecipeSelect");

  if (dateEl) dateEl.value = dateStr || new Date().toISOString().split("T")[0];
  if (selectEl && recipeId) selectEl.value = recipeId;

  const modalEl = document.getElementById("addPlanModal");
  if (modalEl) new bootstrap.Modal(modalEl).show();
}

document.addEventListener("DOMContentLoaded", () => {
  const confirmAddBtn = document.getElementById("confirmAddPlanBtn");
  if (confirmAddBtn) {
    confirmAddBtn.addEventListener("click", async () => {
      const recipeId = document.getElementById("planRecipeSelect").value;
      const date = document.getElementById("addPlanDate").value;
      const mealType = document.getElementById("addPlanMealType").value;
      if (!recipeId || !date) return;

      try {
        const res = await fetch("/meal-plan/add", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ recipe_id: recipeId, date, meal_type: mealType }),
        });
        const data = await res.json();
        if (data.success) {
          window.location.reload();
        }
      } catch (err) {
        console.error("Add to plan failed", err);
      }
    });
  }
});

// ---- Meal planner: remove entry ----
async function removeMealPlan(entryId) {
  if (!confirm("Remove this meal from your plan?")) return;
  try {
    const res = await fetch(`/meal-plan/remove/${entryId}`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      const el = document.getElementById(`plan-${entryId}`);
      if (el) el.remove();
    }
  } catch (err) {
    console.error("Remove plan failed", err);
  }
}
