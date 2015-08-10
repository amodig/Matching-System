MatchingApp.directive('modal', function(){
  return {
    scope: {
      show: '='
    },
    link: function(scope, elem, attrs){
      scope.$watch('show', function(show){
        var method = show ? 'show' : 'hide'
        $(elem).modal(method);
      });
    }
  }
});
