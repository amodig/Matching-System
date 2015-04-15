MatchingApp.directive('upload', function(){
  return {
    scope: {
      added: '=',
      uploaded: '=',
      files: '='
    },
    link: function(scope, elem, attrs){
      $(elem).fileupload()
        .bind('fileuploadadd', function (e, data) {
          scope.added(data);
        })
        .bind('fileuploaddone', function (e, data) {
          scope.uploaded(data);
        });
    }
  }
});
