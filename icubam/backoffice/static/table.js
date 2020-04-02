function setDatatable (table_id) {
  let table = $(table_id).DataTable({
    "responsive": true,
    "autoWidth": false,
  })

  // TODO(olivier): add a button to go to table.
  $(table_id).on( 'click', 'td', function () {
      console.log( table.cell( this ).data() );
  } );
}
