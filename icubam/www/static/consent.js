$(function () {
  // Maybe show modal.
  let modal = $('#modal-lg')
  if (modal !== null) {
    modal.modal()
  }

  $(".agree").click(function (e) {
    e.preventDefault();
    $.ajax({
      type: "POST",
      url: "/consent",
      data: {
        agree: $(this).val(),
      },
      success: function(result) {
        modal.modal('hide')
        const data = JSON.parse(result)
        if (data.redirect !== null) {
          window.location = data.redirect
        }
      },
      error: function(result) {
        modal.modal('hide')
        alert('Something went wrong');
        window.location = "/error"
      }
    })
  })
})
