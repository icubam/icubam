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
