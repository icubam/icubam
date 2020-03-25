
$(document).ready(function() {
  $('#example').DataTable({
    ajax: {
      url: '/beds',
      data: function(d){
            console.log(d)
            return d
        },
    },
    columnDefs: [ {
        "targets": 0,
        "data": "icu_id",
        "render": function ( data, type, row, meta ) {
              return '<a href="update?icu_id='+row.icu_id+'"><span class="glyphicon glyphicon-edit aria-hidden="true"">modify </span></a>'; }
    } ],

    columns: [
    {data: 'icu_id'},
    {data: 'icu_name'},
    {data: 'n_covid_occ'},
    {data: 'n_covid_free'},
    {data: 'n_ncovid_free'},
    {data: 'n_covid_deaths'},
    {data: 'n_covid_healed'},
    /*
    {data: 'n_covid_refused'},
    {data: 'n_covid_transfered'},
    {data: 'message'},
    {data: 'update_ts'},
    */
    ]
  });
});
