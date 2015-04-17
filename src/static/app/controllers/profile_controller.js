MatchingApp.controller('ProfileController', function($scope, $rootScope, Api, Fileupload){
  $rootScope.activeLink = 'profile';

  Api.getProfile().success(function(profile){
    $scope.bio = {
      editing: false,
      content: profile.bio,
      files: angular.fromJson(profile.files),
      user: profile.user,
      email: profile.email
    };


    Fileupload.init($scope.bio.files);
  });

  $scope.editBio = function(){
    $scope.bio.editing = true;
  };

  $scope.updateBio = function(){
    Api.updateBio($scope.bio.content).success(function(){
      $scope.bio.editing = false;
    });
  }
});
