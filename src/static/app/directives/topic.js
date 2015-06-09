MatchingApp.directive('topic', function(){
  return {
    scope: {
      topic: '=ngModel'
    },
    link: function(scope, elem, attrs){
        $(elem).slider();
    }
  }
});
