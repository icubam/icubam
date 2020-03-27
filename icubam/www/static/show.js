
/* Useful links
http://live.datatables.net/siqoreko/26/edit
https://github.com/gryevns/jquery-colorize
*/
$(document).ready(function() {
  var themes = {
    "default": {
        color_min: "#C80000",
        color_mid: "#FFFFFF",
        color_max: "#10A54A"
    },
    "green-white-red": {
      color_min: "#10A54A",
      color_mid: "#FFFFFF",
      color_max: "#C80000"
    },
    "red-white-green": {
      color_min: "#C80000",
      color_mid: "#FFFFFF",
      color_max: "#10A54A"
    },
    "white-yellow-red": {
      color_min: "#FFFFFF",
      color_mid: "#e9f542",
      color_max: "#C80000"
    },
    "white-lime-green": {
      color_min: "#FFFFFF",
      color_mid: "#7bf542",
      color_max: "#10A54A"
    },

  };

  $('#example').DataTable({
    "pageLength": -1,
    ajax: {
     url: '/beds',
      data: function(d){
            return d;
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
    {data: 'icu_name'},
    {data: 'n_covid_tot'},
    {data: 'n_covid_occ'},
    {data: 'n_covid_free'},
    {data: 'n_ncovid_free'},
    {data: 'n_covid_deaths'},
    {data: 'n_covid_healed'},
    {data: 'since_update'},
    /*
    {data: 'n_covid_refused'},
    {data: 'n_covid_transfered'},
    {data: 'message'},
    {data: 'update_ts'},
    */
    ],

    columnDefs: [
      {
        // targets: [5],
        createdCell: function (td, cellData, rowData, rowIndex, colIndex) {
          console.log(td);
          $(td).colorize();
        }
      },
    ],

    drawCallback: function () {
      $("#example tbody td").not(':nth-child(1),:nth-child(2),:nth-child(3),:nth-child(4),:nth-child(5),:nth-child(7),:nth-child(8)').colorize({
        themes: themes,
        theme:"white-yellow-red"
      });

      $("#example tbody td").not(':nth-child(1),:nth-child(2),:nth-child(3),:nth-child(4),:nth-child(5),:nth-child(6),:nth-child(8)').colorize({
        themes: themes,
        theme:"white-lime-green"
      });
    }
  });


});
