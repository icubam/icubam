function toggleForm() {
  var icu_form = document.getElementById("icu_form")
  var buttons = document.getElementById("navigation_buttons")
  if (icu_form.style.display === "none" || icu_form.style.display === "") {
    icu_form.style.display = "block"
    buttons.style.display = "none"
  } else {
    icu_form.style.display = "none"
    buttons.style.display = "block"
  }
}

function navigateTo(route) {
   window.location = route
}

function markInvalidIfNotGreaterOrEqualTo(input_id, lower_bound) {
  var input = document.getElementById(input_id);
  var warn = document.getElementById("warn-" + input_id);
  var warn_new_val = document.getElementById("warn-" + input_id + "-new-value");
  var warn_last_val = document.getElementById("warn-" + input_id + "-last-value");
  var int_input_value = Number(input.value);
  var int_lower_bound = Number(lower_bound);
  if (int_input_value < int_lower_bound) {
    input.style.color = "red";
    input.style.backgroundColor = "rgba(255, 0, 0, 0.3)";
    warn.style.display = "block";
    warn_new_val.innerHTML = String(int_input_value);
    warn_last_val.innerHTML = String(int_lower_bound);
  }
  else {
    input.style.color = "green";
    input.style.backgroundColor = "rgba(0, 255, 0, 0.3)";
    warn.style.display = "none";
  }
}

function markInvalidIfDeltaGreaterThan(input_id, last_value, max_delta) {
  var input = document.getElementById(input_id);
  var warn = document.getElementById("warn-" + input_id);
  var warn_new_val = document.getElementById("warn-" + input_id + "-new-value");
  var warn_last_val = document.getElementById("warn-" + input_id + "-last-value");
  var warn_delta = document.getElementById("warn-" + input_id + "-delta");
  var int_input_value = Number(input.value);
  var int_last_value = Number(last_value);
  var int_max_delta = Number(max_delta);
  var delta = Math.abs(int_last_value - int_input_value);
  if (delta > int_max_delta) {
    input.style.color = "red";
    input.style.backgroundColor = "rgba(255, 0, 0, 0.3)";
    warn.style.display = "block";
    warn_new_val.innerHTML = String(int_input_value);
    warn_last_val.innerHTML = String(int_last_value);
    warn_delta.innerHTML = String(delta);
  }
  else {
    input.style.color = "green";
    input.style.backgroundColor = "rgba(0, 255, 0, 0.3)";
    warn.style.display = "none";
  }
}

function markInvalidIfDeltaGreaterThan2(input_id, last_value, max_delta) {
  var input = document.getElementById(input_id);
  var warn = document.getElementById("warn2-" + input_id);
  var warn_new_val = document.getElementById("warn2-" + input_id + "-new-value");
  var warn_last_val = document.getElementById("warn2-" + input_id + "-last-value");
  var warn_delta = document.getElementById("warn2-" + input_id + "-delta");
  var int_input_value = Number(input.value);
  var int_last_value = Number(last_value);
  var int_max_delta = Number(max_delta);
  var delta = Math.abs(int_last_value - int_input_value);
  if (delta > int_max_delta) {
    input.style.color = "red";
    input.style.backgroundColor = "rgba(255, 0, 0, 0.3)";
    warn.style.display = "block";
    warn_new_val.innerHTML = String(int_input_value);
    warn_last_val.innerHTML = String(int_last_value);
    warn_delta.innerHTML = String(delta);
  }
  else {
    input.style.color = "green";
    input.style.backgroundColor = "rgba(0, 255, 0, 0.3)";
    warn.style.display = "none";
  }
}
