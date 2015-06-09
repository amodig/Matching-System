MatchingApp.directive('tooltip', function(){
  return {
    scope: {
      content: '='
    },
    restrict: 'A',
    link: function(scope, element, attrs){
      $(element).tooltip({ container: 'body', title: scope.content });
    }
  };
});
