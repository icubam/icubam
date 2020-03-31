function togglePopup (cluster_id, color) {
  var cluster = document.getElementById('cluster-' + cluster_id +'-cluster' )
  var full = document.getElementById('cluster-' + cluster_id +'-full' )
  var box = document.getElementById('infowindow-' + cluster_id)

  var subtitleFull = document.getElementById('subtitle-full')
  var subtitleCluster = document.getElementById('subtitle-cluster')

  if (cluster.style.display === "block" || cluster.style.display === "" ) {
    cluster.style.display = "none"
    full.style.display = "block"
    box.style.borderStyle = 'solid'
    box.style.borderColor = color
    subtitleFull.style.display = 'inline'
    subtitleCluster.style.display = 'none'
    showed.add(cluster_id)

  } else {
    cluster.style.display = "block"
    full.style.display = "none"
    box.style.borderStyle = 'none'
    subtitleFull.style.display = 'none'
    subtitleCluster.style.display = 'inline'
    showed.delete(cluster_id)
  }
}

function toggleAll () {
  all_showed = !all_showed
  for (i = 0; i < data.length; i++) {
    if ((!showed.has(data[i].label) && all_showed) ||
        (!all_showed && (showed.has(data[i].label)))) {
      togglePopup(data[i].label, data[i].color)
    }
  }
}

function CenterControl(controlDiv, map) {
  // Set CSS for the control border.
  var controlUI = document.createElement('div');
  controlUI.style.backgroundColor = '#fff';
  controlUI.style.border = '2px solid #888';
  controlUI.style.borderRadius = '3px';
  controlUI.style.boxShadow = '0 2px 6px rgba(0,0,0,.3)';
  controlUI.style.cursor = 'pointer';
  controlUI.style.marginBottom = '22px';
  controlUI.style.textAlign = 'center';
  controlUI.title = 'Clicker pour afficher';
  controlDiv.appendChild(controlUI);

  // Set CSS for the control interior.
  var controlText = document.createElement('div');
  controlText.style.color = 'rgb(25,25,25)';
  controlText.style.fontFamily = 'Roboto,Arial,sans-serif';
  controlText.style.fontSize = '16px';
  controlText.style.lineHeight = '38px';
  controlText.style.paddingLeft = '5px';
  controlText.style.paddingRight = '5px';
  controlText.innerHTML = 'Tout montrer';
  controlUI.appendChild(controlText);
  controlUI.addEventListener('click', function() {
    toggleAll();
  });
}


function addMarker (obj, map) {
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
    icon: {url: icon_url},
  });

  let show = false
  function toggle () {
    show = !show
    if (show) {
      infowindow.open(map, marker);
    } else {
      infowindow.close(map, marker);
    }
  }

  toggle()
  marker.addListener('click', toggle)
}

function addPopup (obj, map, Popup) {
  var div = document.getElementById('map')
  div.insertAdjacentHTML('beforeend', obj.popup);
  var content = div.lastElementChild
  popup = new Popup(new google.maps.LatLng(obj.lat, obj.lng), content)
  popup.setMap(map);
}

function getCenter(data) {
  if (data.length === 0) {
    // Paris lat-long
    return {lat: 48.8566, lng: 2.3522}
  }

  let center = {lat: 0, lng: 0}
  for (i =0; i < data.length; i++) {
    center.lat = center.lat + data[i].lat
    center.lng = center.lng + data[i].lng
  }
  center.lat =  center.lat / data.length
  center.lng =  center.lng / data.length

  return center
}

function plotMap(data, center) {
  center = center === null ? getCenter(data) : center
  var map = new google.maps.Map(document.getElementById('map'), {
    zoom: 9,
    center: center,
    mapTypeControl: false,
    styles: [
          {
            elementType: 'geometry',
            stylers: [{color: '#f5f5f5'}]
          },
          {
            elementType: 'labels.icon',
            stylers: [{visibility: 'off'}]
          },
          {
            elementType: 'labels.text.fill',
            stylers: [{color: '#616161'}]
          },
          {
            elementType: 'labels.text.stroke',
            stylers: [{color: '#f5f5f5'}]
          },
          {
            featureType: 'administrative.land_parcel',
            elementType: 'labels.text.fill',
            stylers: [{color: '#bdbdbd'}]
          },
          {
            featureType: 'poi',
            elementType: 'geometry',
            stylers: [{color: '#eeeeee'}]
          },
          {
            featureType: 'poi',
            elementType: 'labels.text.fill',
            stylers: [{color: '#757575'}]
          },
          {
            featureType: 'poi.park',
            elementType: 'geometry',
            stylers: [{color: '#e5e5e5'}]
          },
          {
            featureType: 'poi.park',
            elementType: 'labels.text.fill',
            stylers: [{color: '#9e9e9e'}]
          },
          {
            featureType: 'road',
            elementType: 'geometry',
            stylers: [{color: '#ffffff'}]
          },
          {
            featureType: 'road.arterial',
            elementType: 'labels.text.fill',
            stylers: [{color: '#757575'}]
          },
          {
            featureType: 'road.highway',
            elementType: 'geometry',
            stylers: [{color: '#dadada'}]
          },
          {
            featureType: 'road.highway',
            elementType: 'labels.text.fill',
            stylers: [{color: '#616161'}]
          },
          {
            featureType: 'road.local',
            elementType: 'labels.text.fill',
            stylers: [{color: '#9e9e9e'}]
          },
          {
            featureType: 'transit.line',
            elementType: 'geometry',
            stylers: [{color: '#e5e5e5'}]
          },
          {
            featureType: 'transit.station',
            elementType: 'geometry',
            stylers: [{color: '#eeeeee'}]
          },
          {
            featureType: 'water',
            elementType: 'geometry',
            stylers: [{color: '#c9c9c9'}]
          },
          {
            featureType: 'water',
            elementType: 'labels.text.fill',
            stylers: [{color: '#9e9e9e'}]
          }
        ],
  });

  var all_popups = []
  Popup = createPopupClass();
  for (i = 0; i < data.length; i++) {
    // addMarker(data[i], map)
    all_popups.push(addPopup(data[i], map, Popup))
  }

  // Create the DIV to hold the control and call the CenterControl()
  // constructor passing in this DIV.
  var centerControlDiv = document.createElement('div');
  var centerControl = new CenterControl(centerControlDiv, map);
  centerControlDiv.index = 1;
  map.controls[google.maps.ControlPosition.TOP_CENTER].push(centerControlDiv);
}
