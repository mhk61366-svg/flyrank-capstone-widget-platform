(function () {
  const scriptTag = document.currentScript;
  const params = new URL(scriptTag.src).searchParams;
  const widgetId = params.get("id");
  const apiBase = "http://localhost:8000"; // TODO: derive from script src origin for real multi-deployment use

  const inputStyle =
    "display:block; width:100%; margin-bottom:10px; padding:8px; border:1px solid #ccc; border-radius:4px; box-sizing:border-box; font-family: Inter, sans-serif;";
  const buttonStyle =
    "background:#1E3A5F; color:#FAFAFA; border:none; padding:10px 16px; border-radius:4px; cursor:pointer; font-family: Inter, sans-serif;";

  if (!widgetId) {
    console.error("[FlyRankWidget] Missing widget id in script src");
    return;
  }

  fetch(`${apiBase}/widgets/${widgetId}/config`)
    .then((res) => {
      if (!res.ok) throw new Error("Widget config not found");
      return res.json();
    })
    .then(renderWidget)
    .catch((err) => console.error("[FlyRankWidget]", err));

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
  }

  function renderWidget(config) {
    const container = document.createElement("div");
    container.id = `flyrank-widget-${widgetId}`;
    container.style.cssText =
      "font-family: Inter, sans-serif; max-width: 360px; border: 1px solid #1E3A5F; border-radius: 8px; padding: 20px; background: #FAFAFA; color: #111111;";

    container.innerHTML = `
      <h3 style="margin:0 0 8px; color:#1E3A5F;">${escapeHtml(config.title)}</h3>
      ${config.description ? `<p style="margin:0 0 16px; font-size:14px;">${escapeHtml(config.description)}</p>` : ""}
      <form id="flyrank-form-${widgetId}">
        <input name="name" placeholder="Name" required style="${inputStyle}" />
        <input name="email" type="email" placeholder="Email" required style="${inputStyle}" />
        <input name="age" type="number" placeholder="Age" required style="${inputStyle}" />
        <input name="gender" placeholder="Gender" required style="${inputStyle}" />
        <textarea name="message" placeholder="Message (optional)" style="${inputStyle}"></textarea>
        <input name="hp_field" type="text" autocomplete="off" tabindex="-1" style="position:absolute; left:-9999px; opacity:0;" />
        <button type="submit" style="${buttonStyle}">${escapeHtml(config.button_text)}</button>
      </form>
      <div id="flyrank-msg-${widgetId}" style="margin-top:8px; font-size:13px;"></div>
    `;

    scriptTag.parentNode.insertBefore(container, scriptTag);

    const form = container.querySelector(`#flyrank-form-${widgetId}`);
    const msg = container.querySelector(`#flyrank-msg-${widgetId}`);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const formData = new FormData(form);
      const payload = {
        widget_id: widgetId,
        name: formData.get("name"),
        email: formData.get("email"),
        age: parseInt(formData.get("age"), 10),
        gender: formData.get("gender"),
        message: formData.get("message") || null,
        hp_field: formData.get("hp_field") || "",
      };

      fetch(`${apiBase}/submissions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then((res) => {
          if (!res.ok) throw new Error("Submission failed");
          return res.json();
        })
        .then(() => {
          msg.textContent = "Thanks! We got your submission.";
          msg.style.color = "#1E3A5F";
          form.reset();
        })
        .catch(() => {
          msg.textContent = "Something went wrong. Please try again.";
          msg.style.color = "#b00020";
        });
    });
  }
})();