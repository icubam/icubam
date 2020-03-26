function toggleForm() {
  var icu_form = document.getElementById("icu_form");
  var buttons = document.getElementById("navigation_buttons");
  icu_form.style.display = "block";
  buttons.style.display = "none";
}

function navigateTo(route) {
   window.location = route;
}
