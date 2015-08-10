MatchingApp.directive('portrait', function(){
  return {
    scope: {
      mail: '=',
      name: '=',
      size: '@',
      click: '='
    },
    link: function(scope, elem, attrs){
      var url = 'http://www.gravatar.com/avatar/' + md5(scope.mail) + '?size=' + scope.size;

      $(elem)
        .css('background-image', 'url(' + url + ')')
        .tooltip({
          title: scope.name,
          container: 'body'
        })
        .on('click', function(){
          scope.$apply(function(){
            scope.click();
          });
        });
    }
  }
});
