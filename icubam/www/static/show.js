
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
            return d
        },
    },

    columns: [
    {data: 'icu_name'},
    {data: 'n_covid_tot'},
    {data: 'n_covid_occ'},
    {data: 'n_covid_free'},
    {data: 'n_ncovid_free'},
    {data: 'n_covid_deaths'},
    {data: 'n_covid_healed'},
    {data: 'since_update'},
    ],


    drawCallback: function () {

      $("#example tbody td").filter(':nth-child(6)').colorize({
        themes: themes,
        theme:"white-yellow-red"
      });

      $("#example tbody td").filter(':nth-child(7)').colorize({
        themes: themes,
        theme:"white-lime-green"
      });
    }
  });

});

