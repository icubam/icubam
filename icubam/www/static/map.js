function togglePopup(cluster_id, color) {
  var cluster = document.getElementById('cluster-' + cluster_id + '-cluster')
  var full = document.getElementById('cluster-' + cluster_id + '-full')
  var box = document.getElementById('infowindow-' + cluster_id)

  var titleBox = document.getElementById('title-box')
  var subtitleFullPos = titleBox.getElementsByClassName('subtitle-full-pos')[0]
  var subtitleFullNeg = titleBox.getElementsByClassName('subtitle-full-neg')[0]
  var subtitleFullAll = titleBox.getElementsByClassName('subtitle-full-all')[0]
  var subtitleCluster = titleBox.getElementsByClassName('subtitle-cluster')[0]

  if (cluster.style.display === "block" || cluster.style.display === "") {
    cluster.style.display = "none"
    full.style.display = "block"
    box.style.borderStyle = 'solid'
    box.style.borderColor = color
    if (subtitleFullPos !== null) {subtitleFullPos.style.display = titleBox.getElementsByClassName('subtitle-covid-pos') [0].style.display}
    if (subtitleFullNeg !== null) {subtitleFullNeg.style.display = titleBox.getElementsByClassName('subtitle-covid-neg') [0].style.display}
    if (subtitleFullAll !== null) {subtitleFullAll.style.display = titleBox.getElementsByClassName('subtitle-covid-all') [0].style.display}
    if (subtitleCluster !== null) {subtitleCluster.style.display = 'none'}
    showed.add(cluster_id)

  } else {
    cluster.style.display = "block"
    full.style.display = "none"
    box.style.borderStyle = 'none'
    if (subtitleFullPos !== null) {subtitleFullPos.style.display = 'none'}
    if (subtitleFullNeg !== null) {subtitleFullNeg.style.display = 'none'}
    if (subtitleFullAll !== null) {subtitleFullAll.style.display = 'none'}
    if (subtitleCluster !== null) {subtitleCluster.style.display = 'inline'}
    showed.delete(cluster_id)
  }
}

function toggleAll() {
  all_showed = !all_showed
  let dc = data[covid]
  for (i = 0; i < dc.length; i++) {
    if ((!showed.has(dc[i].label) && all_showed) ||
      (!all_showed && (showed.has(dc[i].label)))) {
      togglePopup(dc[i].label, dc[i].color)
    }
  }
}

function CenterControl(
  controlDiv, map, displayAllText, displayAllAltText, toggleFn) {
  // Set CSS for the control border.
  var controlUI = document.createElement('div');
  controlUI.style.backgroundColor = '#fff';
  controlUI.style.border = '2px solid #888';
  controlUI.style.borderRadius = '3px';
  controlUI.style.boxShadow = '0 2px 6px rgba(0,0,0,.3)';
  controlUI.style.cursor = 'pointer';
  controlUI.style.marginBottom = '22px';
  controlUI.style.textAlign = 'center';
  controlUI.title = displayAllAltText;
  controlDiv.appendChild(controlUI);

  // Set CSS for the control interior.
  var controlText = document.createElement('div');
  controlText.style.color = 'rgb(25,25,25)';
  controlText.style.fontFamily = 'Roboto,Arial,sans-serif';
  controlText.style.fontSize = '16px';
  controlText.style.lineHeight = '38px';
  controlText.style.paddingLeft = '5px';
  controlText.style.paddingRight = '5px';
  controlText.innerHTML = displayAllText;
  controlUI.appendChild(controlText);
  controlUI.addEventListener('click', toggleFn);
}


function addMarker(obj, map) {
  const position = { lat: obj.lat, lng: obj.long };

  var infowindow = new google.maps.InfoWindow({
    content: obj.popup,
  });

  let icon_url = "http://maps.google.com/mapfiles/ms/icons/"
  icon_url += obj.color + "-dot.png"

  var marker = new google.maps.Marker({
    position: position,
    map: map,
    title: obj.label,
    icon: { url: icon_url },
  });

  let show = false
  function toggle() {
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

function addPopup(obj, map, Popup) {
  var div = document.getElementById('map')
  div.insertAdjacentHTML('beforeend', obj.popup);
  var content = div.lastElementChild
  popup = new Popup(new google.maps.LatLng(obj.lat, obj.long), content)
  popup.setMap(map);
}

function toggleCovid() {
  if (covid == true) {
    covid = false;
  }
  else if (covid == false){
    covid = null;
  }
  else {
    covid = true;
  }

  //covid = !covid
  plotMap(data[covid], center, covid)
}


function plotMap(data, center, covid_status=true) {
  var map = new google.maps.Map(document.getElementById('map'), {
    zoom: 9,
    center: center,
    mapTypeControl: false,
    styles: [
      {
        elementType: 'geometry',
        stylers: [{ color: '#f5f5f5' }]
      },
      {
        elementType: 'labels.icon',
        stylers: [{ visibility: 'off' }]
      },
      {
        elementType: 'labels.text.fill',
        stylers: [{ color: '#616161' }]
      },
      {
        elementType: 'labels.text.stroke',
        stylers: [{ color: '#f5f5f5' }]
      },
      {
        featureType: 'administrative.land_parcel',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#bdbdbd' }]
      },
      {
        featureType: 'poi',
        elementType: 'geometry',
        stylers: [{ color: '#eeeeee' }]
      },
      {
        featureType: 'poi',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#757575' }]
      },
      {
        featureType: 'poi.park',
        elementType: 'geometry',
        stylers: [{ color: '#e5e5e5' }]
      },
      {
        featureType: 'poi.park',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#9e9e9e' }]
      },
      {
        featureType: 'road',
        elementType: 'geometry',
        stylers: [{ color: '#ffffff' }]
      },
      {
        featureType: 'road.arterial',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#757575' }]
      },
      {
        featureType: 'road.highway',
        elementType: 'geometry',
        stylers: [{ color: '#dadada' }]
      },
      {
        featureType: 'road.highway',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#616161' }]
      },
      {
        featureType: 'road.local',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#9e9e9e' }]
      },
      {
        featureType: 'transit.line',
        elementType: 'geometry',
        stylers: [{ color: '#e5e5e5' }]
      },
      {
        featureType: 'transit.station',
        elementType: 'geometry',
        stylers: [{ color: '#eeeeee' }]
      },
      {
        featureType: 'water',
        elementType: 'geometry',
        stylers: [{ color: '#c9c9c9' }]
      },
      {
        featureType: 'water',
        elementType: 'labels.text.fill',
        stylers: [{ color: '#9e9e9e' }]
      }
    ],
  });

  var all_popups = []
  Popup = createPopupClass();
  for (i = 0; i < data.length; i++) {
    all_popups.push(addPopup(data[i], map, Popup))
  }

  // Create the DIV to hold the control and call the CenterControl()
  // constructor passing in this DIV.
  var centerControlDiv = document.createElement('div');
  var centerControl = new CenterControl(
    centerControlDiv, map, displayAllText, displayAllAltText, toggleAll);
  centerControlDiv.index = 1;
  map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(centerControlDiv);
  var titleDiv = document.getElementById('title-box-orig')
  var titleClone = titleDiv.cloneNode(true); // true means clone all childNodes and all event handlers
  titleClone.id = "title-box";
  if (covid_status == true){
   titleClone.getElementsByClassName('subtitle-covid-pos')[0].style.display = 'block';
   titleClone.getElementsByClassName('subtitle-covid-neg')[0].style.display = 'none';
   titleClone.getElementsByClassName('subtitle-covid-all')[0].style.display = 'none';
   titleClone.getElementsByClassName('subtitle-full-pos')[0].style.display = 'block';
   titleClone.getElementsByClassName('subtitle-full-neg')[0].style.display = 'none';
   titleClone.getElementsByClassName('subtitle-full-all')[0].style.display = 'none';
   titleClone.getElementsByClassName('subtitle-cluster')[0].style.display = 'none';
  }
  else if (covid_status == false){
    titleClone.getElementsByClassName('subtitle-covid-neg')[0].style.display = 'block';
    titleClone.getElementsByClassName('subtitle-covid-pos')[0].style.display = 'none';
    titleClone.getElementsByClassName('subtitle-covid-all')[0].style.display = 'none';
    titleClone.getElementsByClassName('subtitle-full-pos')[0].style.display = 'none';
    titleClone.getElementsByClassName('subtitle-full-neg')[0].style.display = 'block';
    titleClone.getElementsByClassName('subtitle-full-all')[0].style.display = 'none';
    titleClone.getElementsByClassName('subtitle-cluster')[0].style.display = 'none';
  }
  else {
    titleClone.getElementsByClassName('subtitle-covid-all')[0].style.display = 'block';
    titleClone.getElementsByClassName('subtitle-covid-neg')[0].style.display = 'none';
    titleClone.getElementsByClassName('subtitle-covid-pos')[0].style.display = 'none';
    titleClone.getElementsByClassName('subtitle-full-pos')[0].style.display = 'none';
    titleClone.getElementsByClassName('subtitle-full-neg')[0].style.display = 'none';
    titleClone.getElementsByClassName('subtitle-full-all')[0].style.display = 'block';
    titleClone.getElementsByClassName('subtitle-cluster')[0].style.display = 'none';
  }
//  var dispEl = covid_status ? 'pos' : 'neg'
//  var hideEl = !covid_status ? 'pos' : 'neg'
//  titleClone.getElementsByClassName('subtitle-covid-'.concat(dispEl))[0].style.display = 'block'
//  titleClone.getElementsByClassName('subtitle-covid-'.concat(hideEl))[0].style.display = 'none'
  map.controls[google.maps.ControlPosition.TOP_LEFT].push(titleClone);
  // Create the DIV to hold the control and call the CenterControl()
  // constructor passing in this DIV.
  var covidControlDiv = document.createElement('div');
  //const covidText = covid ? showingCovidText : showingNCovidText;
  var covidText;
  if (covid_status == true) {
    covidText = showingCovidText;
  }
  else if (covid_status == false)
  {
     covidText = showingAllText;
  }
  else{
    covidText = showingNCovidText;
  }
  var covidControl = new CenterControl(
      covidControlDiv, map, covidText, covidAltText, toggleCovid);
  covidControlDiv.index = 1;
  map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(covidControlDiv);
}
