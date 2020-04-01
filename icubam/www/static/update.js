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
  var submit_button = document.getElementById("update-form-submit-button");
  var submit_error_message = document.getElementById("submit-error-message");
  var int_input_value = Number(input.value);
  var int_lower_bound = Number(lower_bound);
  if (int_input_value < int_lower_bound) {
    input.style.color = "red";
    input.style.backgroundColor = "rgba(255, 0, 0, 0.3)";
    submit_button.disabled = true;
    submit_error_message.style.display = "inline";
  }
  else {
    input.style.color = "green";
    input.style.backgroundColor = "rgba(0, 255, 0, 0.3)";
    submit_button.disabled = false;
    submit_error_message.style.display = "none";
  }
}
