// Time Series
// Waterhackweek 2014-2022

// Goal: The purpose is to classify water from SAR imagery and create
// interactive time series of water pixel count

// Topics addressed:
//  - loading and filtering image collections
//  - prepairing and classify SAR data
//  - creating a time series of water body classification in a region
//  - making interactive time series charts

// Load region defined by polygon and add it to the map
var roi = ee.Geometry.Polygon(
        [[[126.771302, 38.418591],
          [126.771302, 38.353767],
          [126.866022, 38.353767],
          [126.866022, 38.418591]]]);
Map.addLayer(roi, {}, 'ROI')
Map.centerObject(roi, 8)

//Load Sentinel-1 SAR collection and filter according to data collection type
var S1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(roi)
  .filterDate('2014-01-01','2022-02-20')
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))

//Add first image to map to get an idea of what a SAR image looks like  
Map.addLayer(S1.first(),{bands: 'VV',min: -18, max: 0}, 'SAR image')
  
// Filter speckle noise
var filterSpeckles = function(img) {
  var vv = img.select('VV') //select the VV polarization band
  var vv_smoothed = vv.focal_median(100,'circle','meters').rename('VV_Filtered') //Apply a focal median filter
  return img.addBands(vv_smoothed) // Add filtered VV band to original image
}

// Map speckle noise filter across collection. Result is same collection, with smoothed VV band added to each image
S1 = S1.map(filterSpeckles)

//Add speckle filtered image to map to sompare with raw SAR image
Map.addLayer(S1.first(),{bands: 'VV_Filtered',min: -18, max: 0}, 'Filtered SAR image')

//Classify water pixels using a set threshhold 
//Here we are using -16. This is only an approximation and will result in some errors. Try adjusting the 
var classifyWater = function(img) {
  var vv = img.select('VV_Filtered')
  var water = vv.lt(-16).rename('Water')  //Identify all pixels below threshold and set them equal to 1. All other pixels set to 0
  water = water.updateMask(water) //Remove all pixels equal to 0
  return img.addBands(water)  //Return image with added classified water band
}

//Map classification across sentinel-1 collection and print to console to inspect
S1 = S1.map(classifyWater)
print(S1)

//Make time series of water pixels within region
var ClassChart = ui.Chart.image.series({
  imageCollection: S1.select('Water'),
  region: roi,
  reducer: ee.Reducer.sum(),
  scale: 100,
})
  .setOptions({
      title: 'Inundated Pixels',
      hAxis: {'title': 'Date'},
      vAxis: {'title': 'Number of Inundated Pixels'},
      lineWidth: 2
    })

//Set the postion of the chart and add it to the map    
ClassChart.style().set({
    position: 'bottom-right',
    width: '500px',
    height: '300px'
  });
  
Map.add(ClassChart)

// Create a label on the map.
var label = ui.Label('Click a point on the chart to show the image for that date.');
Map.add(label);

//Create callbakc function that adds image to the map coresponding with clicked data point on chart
ClassChart.onClick(function(xValue, yValue, seriesName) {
    if (!xValue) return;  // Selection was cleared.
  
    // Show the image for the clicked date.
    var equalDate = ee.Filter.equals('system:time_start', xValue);
    //Find image coresponding with clicked data and clip water classification to roi 
    var classification = ee.Image(S1.filter(equalDate).first()).clip(roi).select('Water'); 
    var SARimage = ee.Image(S1.filter(equalDate).first());
    //Make map layer based on SAR image, reset the map layers, and add this new layer
    var S1Layer = ui.Map.Layer(SARimage, {
      bands: ['VV'],
      max: 0,
      min: -20
    });
    Map.layers().reset([S1Layer]);
    var visParams = {
      min: 0,
      max: 1,
      palette: ['#FFFFFF','#0000FF']
    }
    //Add water classification on top of SAR image
    Map.addLayer(classification,visParams,'Water')
    
    // Show a label with the date on the map.
    label.setValue((new Date(xValue)).toUTCString());
  });

Map.setCenter(126.8257, 38.3950, 13);  // Imjin River, Korea


