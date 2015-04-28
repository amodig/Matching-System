MatchingApp.controller('ProfileController', function($scope, $rootScope, Api, Fileupload){
  $scope.activeFile = {};
  $rootScope.activeLink = 'profile';

  Api.getProfile()
    .success(function(profile){
      $scope.bio = {
        editing: false,
        content: profile.bio,
        files: angular.fromJson(profile.files),
        user: profile.user,
        email: profile.email
      };

      Fileupload.init($scope.bio.files, {
        fileClicked: function(file){
          $('#article-abstract-modal').modal('show');

          $scope.$apply(function(){
            $scope.activeFile.loading = true;
            $scope.activeFile.error = false;
            $scope.activeFile.title = file.title;
          });

          Api.getAbstractWithKey(file.key)
            .success(function(article){
              $scope.activeFile.loading = false;
              $scope.activeFile.abstract = article.abstract;
            })
            .error(function(){
              $scope.activeFile.loading = false;
              $scope.activeFile.error = true;
            });
        }
      });
    });

  $scope.editBio = function(){
    $scope.bio.editing = true;
  };

  $scope.updateBio = function(){
    Api.updateBio($scope.bio.content)
      .success(function(){
        $scope.bio.editing = false;
      });
  }
});
