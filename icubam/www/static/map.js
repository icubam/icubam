function add_marker (obj, map) {
  const position = {lat: obj.lat, lng: obj.lng};

  var infowindow = new google.maps.InfoWindow({
    content: obj.popup,
    maxWidth: 500,
  });

  let icon_url = "http://maps.google.com/mapfiles/ms/icons/"
  icon_url += obj.color + "-dot.png"

  var marker = new google.maps.Marker({
    position: position,
    map: map,
    title: obj.label,
    icon: {url: icon_url}
  });
  marker.addListener('click', function() {
    infowindow.open(map, marker);
  });
  infowindow.open(map,marker);
}

function plotMap(data) {
  let center = {lat: data[0].lat, lng: data[0].lng};
  var map = new google.maps.Map(document.getElementById('map'), {
    zoom: 9,
    center: center,
  });

  for (i = 0; i < data.length; i++) {
    add_marker(data[i], map)
  }
}
