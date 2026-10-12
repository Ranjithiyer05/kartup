(function () {
  "use strict";

  var form = document.getElementById("submission-form");
  if (!form) return;

  var button = document.getElementById("submit-btn");
  var status = document.getElementById("form-status");
  var fields = ["name", "surname"];
  var labels = { name: "name", surname: "surname" };

  function input(field) { return document.getElementById(field); }

  function setFieldError(field, message) {
    var el = input(field);
    var err = document.getElementById(field + "-error");
    err.textContent = message || "";
    if (message) el.setAttribute("aria-invalid", "true");
    else el.removeAttribute("aria-invalid");
  }

  function showStatus(kind, message) {
    status.className = "notice notice-" + kind;
    status.textContent = message;
    status.hidden = false;
  }

  function clearStatus() {
    status.hidden = true;
    status.textContent = "";
  }

  function validate(field) {
    var value = input(field).value.trim().replace(/\s+/g, " ");
    if (!value) return "Please enter your " + labels[field] + ".";
    if (value.length > 100) return "Must be 100 characters or fewer.";
    return "";
  }

  fields.forEach(function (field) {
    input(field).addEventListener("input", function () {
      if (input(field).getAttribute("aria-invalid") === "true") setFieldError(field, validate(field));
      if (!status.hidden && status.classList.contains("notice-success")) clearStatus();
    });
    input(field).addEventListener("blur", function () {
      if (input(field).value) setFieldError(field, validate(field));
    });
  });

  function setLoading(on) {
    button.disabled = on;
    button.classList.toggle("is-loading", on);
    button.setAttribute("aria-busy", on ? "true" : "false");
    button.querySelector(".btn-label").textContent = on ? "Submitting…" : "Submit";
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clearStatus();

    var firstInvalid = null;
    fields.forEach(function (field) {
      var msg = validate(field);
      setFieldError(field, msg);
      if (msg && !firstInvalid) firstInvalid = input(field);
    });
    if (firstInvalid) { firstInvalid.focus(); return; }

    var payload = {
      name: input("name").value.trim(),
      surname: input("surname").value.trim()
    };

    setLoading(true);
    var controller = "AbortController" in window ? new AbortController() : null;
    var timer = controller ? setTimeout(function () { controller.abort(); }, 15000) : null;

    fetch(form.getAttribute("action"), {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload),
      credentials: "same-origin",
      signal: controller ? controller.signal : undefined
    })
      .then(function (res) {
        return res.json().catch(function () { return {}; }).then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        if (result.ok && result.data.ok) {
          form.reset();
          fields.forEach(function (f) { setFieldError(f, ""); });
          showStatus("success", result.data.message || "Thank you! Your details were submitted successfully.");
          status.focus();
          return;
        }
        var errors = (result.data && result.data.errors) || {};
        var focusTarget = null;
        fields.forEach(function (f) {
          if (errors[f]) { setFieldError(f, errors[f]); if (!focusTarget) focusTarget = input(f); }
        });
        showStatus("error", (result.data && result.data.message) || "Something went wrong. Please try again.");
        if (focusTarget) focusTarget.focus();
      })
      .catch(function () {
        showStatus("error", "We couldn't reach the server. Check your connection and try again.");
      })
      .finally(function () {
        if (timer) clearTimeout(timer);
        setLoading(false);
      });
  });
})();
