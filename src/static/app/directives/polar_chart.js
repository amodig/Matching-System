MatchingApp.directive('polarChart', function($timeout){
  return {
    scope: {
      data: '=ngModel',
      click: '=',
      legendContainer: '@legendContainer'
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

            Chart.defaults.global.customTooltips = function(tooltip) {

              // Tooltip Element
                var tooltipEl = $('#chartjs-tooltip');

                // Hide if no tooltip
                if (!tooltip) {
                    tooltipEl.css({
                        opacity: 0
                    });
                    return;
                }

                // Set caret Position
                tooltipEl.removeClass('above below');
                tooltipEl.addClass(tooltip.yAlign);

                // Set Text
                tooltipEl.html(tooltip.text);

                // Find Y Location on page
                var top;
                if (tooltip.yAlign == 'above') {
                    top = tooltip.y - tooltip.caretHeight - tooltip.caretPadding;
                } else {
                    top = tooltip.y + tooltip.caretHeight + tooltip.caretPadding;
                }

                // Display, position, and set styles for font
                tooltipEl.css({
                    opacity: 1,
                    left: tooltip.chart.canvas.offsetLeft + tooltip.x + 'px',
                    top: tooltip.chart.canvas.offsetTop + top + 'px',
                    fontFamily: tooltip.fontFamily,
                    fontSize: tooltip.fontSize,
                    fontStyle: tooltip.fontStyle,
                });
            };

            var polar = new Chart($(canvas)[0].getContext('2d')).PolarArea(scope.data, {
              tooltipFontSize: 12,
              tooltipTemplate: "<%if (label){%><%=label%><%}else{%>[No title]<%}%>",
              percentageInnerCutout : 70,
              legendTemplate : "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<segments.length; i++){%><li><span style=\"background-color:<%=segments[i].fillColor%>\" class=\"legend-label\"></span><%if(segments[i].label){%><%=segments[i].label%><%}%></li><%}%></ul>"
            });

            $('#' + scope.legendContainer).html(polar.generateLegend());

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
