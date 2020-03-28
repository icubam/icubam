
$(document).ready(function() {
  $('#example').DataTable({
    ajax: {
      url: '/users_json',
      data: function(d){
            console.log(d)
            return d
        },
    },
    /*columnDefs: [ {
        "targets": 0,
        "data": "icu_id",
        "render": function ( data, type, row, meta ) {
              return '<a href="update?id='+row.icu_id+'"><span class="glyphicon glyphicon-edit aria-hidden="true"">modify </span></a>'; }
    } ],*/

    columns: [
    //{data: 'icu_id'},
    {data: 'id'},
    {data: 'name'},

    ]
  });
});
