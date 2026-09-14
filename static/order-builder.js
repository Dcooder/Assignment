(() => {
  const picker = document.querySelector("#product-picker");
  if (!picker) return;
  const lines = document.querySelector("#line-items"),
    hidden = document.querySelector("#items-input");
  const state = new Map();
  const render = () => {
    hidden.value = JSON.stringify(
      [...state.values()].map(({ id, quantity }) => ({
        product_id: id,
        quantity,
      })),
    );
    lines.innerHTML = "";
    [...state.values()].forEach((item) => {
      const row = document.createElement("div");
      row.className = "line-item";
      row.innerHTML = `<div><strong>${item.name}</strong><small>${item.sku} · ${item.weight} kg each</small></div><div class="quantity"><button type="button" aria-label="Decrease ${item.name}">−</button><span>${item.quantity}</span><button type="button" aria-label="Increase ${item.name}">+</button></div><button type="button" class="link-button">Remove</button>`;
      const [minus, plus] = row.querySelectorAll(".quantity button");
      minus.onclick = () => {
        if (item.quantity === 1) state.delete(item.id);
        else item.quantity--;
        render();
      };
      plus.onclick = () => {
        item.quantity++;
        render();
      };
      row.querySelector(".link-button").onclick = () => {
        state.delete(item.id);
        render();
      };
      lines.append(row);
    });
    if (!state.size)
      lines.innerHTML =
        '<div class="empty compact"><h3>Your order is empty.</h3><p>Add a product to begin.</p></div>';
    const items = [...state.values()];
    document.querySelector("#total-items").textContent = items.reduce(
      (total, i) => total + i.quantity,
      0,
    );
    document.querySelector("#total-weight").textContent = items
      .reduce((total, i) => total + Number(i.weight) * i.quantity, 0)
      .toFixed(3);
    document.querySelector("#submit-order").disabled = !state.size;
  };
  document.querySelector("#add-product").onclick = () => {
    const option = picker.options[picker.selectedIndex];
    if (!option.value) return;
    const old = state.get(option.value);
    if (old) old.quantity++;
    else
      state.set(option.value, {
        id: option.value,
        name: option.dataset.name,
        sku: option.dataset.sku,
        weight: option.dataset.weight,
        quantity: 1,
      });
    render();
  };
  const initial = JSON.parse(
    document.querySelector("#cart-items-data").textContent,
  );
  initial.forEach(({ product_id, quantity }) => {
    const option = [...picker.options].find(
      (item) => item.value === String(product_id),
    );
    if (option)
      state.set(option.value, {
        id: option.value,
        name: option.dataset.name,
        sku: option.dataset.sku,
        weight: option.dataset.weight,
        quantity,
      });
  });
  render();
})();
