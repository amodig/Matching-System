MatchingApp.directive('polarChart', function($timeout){
  return {
    scope: {
      data: '=ngModel',
      click: '='
    },
    link: function(scope, elem, attrs){
      var colors = [
        {
          color:'#F7464A',
          highlight: '#FF5A5E'
        },
        {
          color: '#46BFBD',
          highlight: '#5AD3D1'
        },
        {
          color: '#FDB45C',
          highlight: '#FFC870'
        },
        {
          color: '#949FB1',
          highlight: '#A8B3C5'
        },
        {
          color: '#4D5360',
          highlight: '#616774'
        }
      ];

      scope.$watch('data', function(){
        if(scope.data){
          scope.data.forEach(function(d, index){
            d.color = colors[index].color;
            d.highlight = colors[index].highlight;
          });

          $timeout(function(){
            var canvas = document.createElement('canvas');
            canvas.width = 350;
            canvas.height = 350;

            $(elem).empty().append(canvas);

            var polar = new Chart($(canvas)[0].getContext('2d')).PolarArea(scope.data);

            $(canvas).on('click', function(evt){
              var segment = polar.getSegmentsAtEvent(evt);
              var clickData = _.find(scope.data, { highlight: segment[0].fillColor }).data;

              scope.$apply(function(){
                scope.click(clickData);
              });
            })
          });
        }
      });

    }
  }
});
