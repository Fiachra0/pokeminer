var app = angular.module('chartApp', []);
app.controller('ChartController', function($scope) {
  // chart data source
  $scope.dataSource = {
    "chart": {
      "caption": "Column Chart Built in Angular!",
      "captionFontSize": "30",
      // more chart properties - explained later
    },
    "data": [{
       "label": "CornflowerBlue",
          "value": "42"
        }, {
          "label": "Tomato",
          "value": "81"
        }, {
          "label": "LightGreen",
          "value": "73"
        }, {
          "label": "Gold",
          "value": "62"
        }, {
          "label": "DeepPink",
          "value": "89" 
    }]
  };
});
