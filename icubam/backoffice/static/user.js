$(function () {
  $('.select2bs4').select2()

  function isAdmin () { return $('#is_admin')[0].checked }
  function isManager () { return $("#managed_icus").val().length > 0 }
  function hasPassword () { return isAdmin() || isManager() }

  function mayShowPassword () {
    let elem = $("#auth_block")
    if (hasPassword()) {
      elem.show()
    } else {
      elem.hide()
    }
  }

  mayShowPassword( hasPassword() )
  $("#is_admin").bootstrapSwitch({onSwitchChange: mayShowPassword})
  $("#managed_icus").change(mayShowPassword)
  $("input[data-bootstrap-switch]").each(function() {
    $(this).bootstrapSwitch('state', $(this).prop('checked'));
  });
})
