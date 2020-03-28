
$(document).ready(function() {
  $('#users').DataTable({
    ajax: {
      url: '/users_json',
      data: function(d){
            console.log(d)
            return d
        },
    },
    columns: [
    {data: 'id'},
    {data: 'name'},
    ]
  });
});
